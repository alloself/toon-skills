"""toon_blender: shot list, checks and shot export for toon-skills.

Blender 4.2 or newer (tested on 5.1). The open file is never saved or changed:
exports render in a separate background Blender.

Through a Blender MCP that runs Python, send this whole file once, followed by

    print(TOON("install"))

After that, every call is short:

    import importlib, toon_blender_core as T; importlib.reload(T); print(T.TOON("check"))

Headless, from a shell (the result is printed between <<<TOON and TOON>>>):

    blender -b scene.blend --python toon_blender.py -- toon '{"cmd": "shots"}'
    blender -b scene.blend --python toon_blender.py -- toon @args.json

Commands: version, install, check, shots, continuity, sequences, export, status.
See references/blender-conventions.md for arguments and outputs.

The module lives in SRC so that it can install itself and start its own worker.
"""

SRC = r'''
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

VERSION = "0.1.0"
DEFAULTS = {
    "char_prefix": "CHR_",
    "camera_prefix": "CAM_",
    "prop_prefix": "PRP_",
    "marker_regex": r"^(?P<scene>[A-Za-z]+\d+)_(?P<num>\d+[A-Za-z]?)_(?P<desc>.+)$",
    "max_shot_seconds": 30,
    "min_shot_seconds": 0.5,
    "jump_m": 0.3,
    "aspect": None,
    "seq_prefix": "SEQ_",
    "char_order": None,
    "char_names": None,
    "prop_names": None,
}
GEOM = {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "POINTCLOUD", "VOLUME"}
MODES = ("full", "hidden", "capsule", "frozen")
# Saturated, nameable colours: the prompt says "the red capsule is @Yaga". Linear RGB.
PALETTE = [("red", (0.80, 0.06, 0.05)), ("blue", (0.05, 0.22, 0.90)), ("yellow", (0.95, 0.70, 0.02)),
           ("green", (0.06, 0.60, 0.10)), ("purple", (0.45, 0.10, 0.75)), ("cyan", (0.03, 0.62, 0.72)),
           ("orange", (0.95, 0.35, 0.02)), ("white", (0.90, 0.90, 0.90))]


# --- basics ------------------------------------------------------------------

def _cfg(kw):
    c = dict(DEFAULTS)
    for k in list(kw):
        if k in DEFAULTS:
            v = kw.pop(k)
            if v is not None:
                c[k] = v
    return c


def _fps(sc):
    return sc.render.fps / sc.render.fps_base


def _r3(v):
    return [round(x, 3) for x in v]


def _safe(name):
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip() or "shot"


def _depth(o):
    n = 0
    while o.parent:
        o, n = o.parent, n + 1
    return n


def _renders(o):
    if o.hide_render:
        return False
    cols = o.users_collection
    return not cols or any(not col.hide_render for col in cols)


def _fcurves(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return []
    try:
        from bpy_extras import anim_utils
        bag = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        return list(bag.fcurves) if bag else []
    except Exception:
        return list(getattr(ad.action, "fcurves", []))


# --- shots, characters, camera -----------------------------------------------

def _shots(c, scene=None):
    sc = bpy.context.scene
    rx = re.compile(c["marker_regex"])
    marks = sorted((m for m in sc.timeline_markers if m.camera), key=lambda m: m.frame)
    fps = _fps(sc)
    out = []
    for i, m in enumerate(marks):
        f0 = m.frame
        f1 = marks[i + 1].frame - 1 if i + 1 < len(marks) else sc.frame_end
        f1 = max(f0, f1)
        g = rx.match(m.name)
        s = {"id": m.name, "scene": g.group("scene") if g else None,
             "num": g.group("num") if g else None, "desc": g.group("desc") if g else None,
             "frame_start": f0, "frame_end": f1, "frames": f1 - f0 + 1,
             "seconds": round((f1 - f0 + 1) / fps, 2), "camera": m.camera.name}
        if scene is None or s["scene"] == scene:
            out.append(s)
    return out


def _charlike(c, o):
    return o.name.startswith(c["char_prefix"]) or o.name in (c.get("char_names") or ())


def _isprop(c, o):
    return o.name.startswith(c["prop_prefix"]) or o.name in (c.get("prop_names") or ())


def _chars(c):
    """Character roots: char-like objects (prefix or char_names) with no char-like ancestor."""
    out = []
    for o in bpy.context.scene.objects:
        if not _charlike(c, o):
            continue
        p = o.parent
        while p and not _charlike(c, p):
            p = p.parent
        if p is None:
            out.append(o)
    return out


def _family(o):
    return [o] + list(o.children_recursive)


def _animated(o):
    ad = o.animation_data
    return bool((ad and (ad.action or len(ad.nla_tracks))) or len(o.constraints))


def _loose_props(c, chars, animated_only=True):
    fam = {x.name for ch in chars for x in _family(ch)}
    return [o for o in bpy.context.scene.objects
            if o.name not in fam and _isprop(c, o) and (_animated(o) or not animated_only)]


def _legend(c, chars):
    """Stable capsule colour per character: passport order first, then by name."""
    order = list(c.get("char_order") or [])
    names = [n for n in order if any(ch.name == n for ch in chars)]
    names += sorted(ch.name for ch in chars if ch.name not in names)
    return {n: {"color": PALETTE[i % len(PALETTE)][0], "rgb": PALETTE[i % len(PALETTE)][1]}
            for i, n in enumerate(names)}


def _screen_box(sc, cam, pts):
    xs, ys = [], []
    for p in pts:
        v = world_to_camera_view(sc, cam, p)
        if v.z > 0:
            xs.append(v.x)
            ys.append(v.y)
    if not xs:
        return None
    left, right = max(0.0, min(xs)), min(1.0, max(xs))
    bottom, top = max(0.0, min(ys)), min(1.0, max(ys))
    if left >= right or bottom >= top:
        return None
    return [round(left, 3), round(1 - top, 3), round(right, 3), round(1 - bottom, 3)]


def _cast_at(c, chars, cam, frame):
    sc = bpy.context.scene
    sc.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    loose = []
    for o in _loose_props(c, chars, animated_only=False):
        if o.type in GEOM:
            e = o.evaluated_get(dg)
            cs = [e.matrix_world @ Vector(v) for v in e.bound_box]
            loose.append((o.name, sum(cs, Vector()) / len(cs)))
    res = {}
    for ch in chars:
        body, props = [], []
        for o in _family(ch):
            if o.type in GEOM and _renders(o):
                (props if _isprop(c, o) else body).append(o)
        pts = []
        for o in body:
            e = o.evaluated_get(dg)
            pts += [e.matrix_world @ Vector(v) for v in e.bound_box]
        box = _screen_box(sc, cam, pts) if pts else None
        loc = ch.matrix_world.translation
        near = []
        if pts:
            m = 0.3
            lo = Vector((min(p.x for p in pts) - m, min(p.y for p in pts) - m, min(p.z for p in pts) - m))
            hi = Vector((max(p.x for p in pts) + m, max(p.y for p in pts) + m, max(p.z for p in pts) + m))
            near = [n for n, p in loose if lo.x <= p.x <= hi.x and lo.y <= p.y <= hi.y and lo.z <= p.z <= hi.z]
        res[ch.name] = {"in_frame": box is not None, "box": box,
                        "height_frac": round(box[3] - box[1], 3) if box else 0,
                        "world": _r3(loc),
                        "distance_m": round((loc - cam.matrix_world.translation).length, 2),
                        "holds": [o.name for o in props], "near": near}
    return res


def _cam_state(cam, frame):
    bpy.context.scene.frame_set(frame)
    mw = cam.matrix_world.copy()
    q = mw.to_quaternion()
    fwd = q @ Vector((0, 0, -1))
    d = cam.data
    lens = d.lens if d.type == "PERSP" else None
    return {"frame": frame, "loc": mw.translation.copy(), "fwd": fwd, "right": q @ Vector((1, 0, 0)),
            "yaw": math.degrees(math.atan2(fwd.y, fwd.x)),
            "pitch": math.degrees(math.asin(max(-1.0, min(1.0, fwd.z)))),
            "lens": lens, "sensor": d.sensor_width, "type": d.type}


def _speed(v, slow, fast):
    return "slowly" if v < slow else ("quickly" if v > fast else "steadily")


def _camera(cam, f0, f1, fps, cast):
    a, b = _cam_state(cam, f0), _cam_state(cam, f1)
    secs = max((f1 - f0 + 1) / fps, 1e-6)
    pts = []
    n = 8
    for i in range(n + 1):
        bpy.context.scene.frame_set(int(round(f0 + (f1 - f0) * i / n)))
        pts.append(cam.matrix_world.translation.copy())
    path = sum((pts[i + 1] - pts[i]).length for i in range(n))
    move = b["loc"] - a["loc"]
    fwd_m, side_m, up_m = move.dot(a["fwd"]), move.dot(a["right"]), move.z
    dyaw = (b["yaw"] - a["yaw"] + 180) % 360 - 180
    dpitch = b["pitch"] - a["pitch"]
    moves = []
    if abs(fwd_m) > 0.05:
        moves.append(("pushes in" if fwd_m > 0 else "pulls back") + f" {abs(fwd_m):.1f} m")
    if abs(side_m) > 0.05:
        moves.append(f"trucks {'right' if side_m > 0 else 'left'} {abs(side_m):.1f} m")
    if abs(up_m) > 0.05:
        moves.append(f"cranes {'up' if up_m > 0 else 'down'} {abs(up_m):.1f} m")
    if abs(dyaw) > 1:
        moves.append(f"pans {'left' if dyaw > 0 else 'right'} {abs(dyaw):.0f}°")
    if abs(dpitch) > 1:
        moves.append(f"tilts {'up' if dpitch > 0 else 'down'} {abs(dpitch):.0f}°")
    if a["lens"] and b["lens"] and abs(b["lens"] - a["lens"]) > 0.5:
        moves.append(f"zooms {'in' if b['lens'] > a['lens'] else 'out'} {a['lens']:.0f}→{b['lens']:.0f} mm")
    lin = max(path, move.length) / secs
    ang = max(abs(dyaw), abs(dpitch)) / secs
    curved = move.length > 0.05 and path > 1.3 * move.length
    pitch = a["pitch"]
    angle = ("top-down" if pitch < -60 else "high-angle" if pitch < -15
             else "low-angle" if pitch > 10 else "eye-level")
    eq = a["lens"] * 36.0 / a["sensor"] if a["lens"] else None
    lens_word = ("orthographic" if eq is None else "ultra-wide" if eq < 20 else "wide" if eq < 35
                 else "normal" if eq < 60 else "short telephoto" if eq < 100 else "telephoto")
    tallest = max((v["height_frac"] for v in cast.values()), default=0)
    size = ("close-up" if tallest > 0.85 else "medium shot" if tallest > 0.5
            else "full shot" if tallest > 0.25 else "wide shot" if tallest > 0 else "establishing shot")
    head = f"{angle.capitalize()} {size}, {lens_word} lens" + (f" ({eq:.0f} mm equiv.)" if eq else "")
    drift = bool(moves) and max(path, move.length) < 0.25 and max(abs(dyaw), abs(dpitch)) < 3 \
        and not (a["lens"] and b["lens"] and abs(b["lens"] - a["lens"]) > 2)
    if drift:
        desc = f"{head}. Almost locked-off camera, slight drift (" + ", ".join(moves) + f") over {secs:.1f} s."
    elif moves:
        verb = _speed(lin, 0.3, 1.2) if lin > 0.05 else _speed(ang, 8, 25)
        desc = f"{head}. Camera {verb} " + ", ".join(moves) + (" on a curved path" if curved else "") + f" over {secs:.1f} s."
    else:
        desc = f"{head}. Locked-off camera, no movement, {secs:.1f} s."
    return {"name": cam.name, "description": desc, "static": not moves, "drift": drift, "moves": moves,
            "start": {"location": _r3(a["loc"]), "yaw": round(a["yaw"], 1), "pitch": round(a["pitch"], 1), "lens_mm": a["lens"]},
            "end": {"location": _r3(b["loc"]), "yaw": round(b["yaw"], 1), "pitch": round(b["pitch"], 1), "lens_mm": b["lens"]},
            "path_m": round(path, 2), "sensor_mm": a["sensor"], "lens_equiv_mm": round(eq, 1) if eq else None,
            "height_m": round(a["loc"].z, 2), "angle": angle, "shot_size": size}


# --- commands ----------------------------------------------------------------

def _travellers(c, chars, shots, min_m=0.3, max_frames=400):
    """Top-level objects outside characters and props that move more than min_m inside a shot."""
    sc = bpy.context.scene
    fam = {x.name for ch in chars for x in _family(ch)}
    cands = [o for o in sc.objects
             if o.parent is None and o.name not in fam and o.type != "CAMERA" and not _isprop(c, o)
             and not o.name.startswith("TOON_") and (_animated(o) or any(_animated(k) for k in o.children))]
    if not cands or not shots:
        return []
    pairs = [(s["frame_start"], s["frame_end"], s["id"]) for s in shots]
    if len(pairs) * 2 > max_frames:
        step = len(pairs) * 2 / max_frames
        pairs = [pairs[int(i * step)] for i in range(int(len(pairs) / step))]
    keep = sc.frame_current
    best = {}
    for f0, f1, sid in pairs:
        sc.frame_set(f0)
        a = {o.name: o.matrix_world.translation.copy() for o in cands}
        sc.frame_set(f1)
        for o in cands:
            d = (o.matrix_world.translation - a[o.name]).length
            if d > best.get(o.name, (0, None))[0]:
                best[o.name] = (d, sid)
    sc.frame_set(keep)
    out = []
    for o in cands:
        d, sid = best.get(o.name, (0, None))
        if d > min_m:
            parts = len([k for k in o.children_recursive if k.type in GEOM])
            out.append({"object": o.name, "moves_m": round(d, 2), "in_shot": sid, "parts": parts,
                        "looks_like": "character" if parts >= 4 or o.type == "ARMATURE" else "prop"})
    return sorted(out, key=lambda x: -x["moves_m"])


def _check(c):
    sc = bpy.context.scene
    r = sc.render
    errors, warnings, info = [], [], []
    shots = _shots(c)
    if not bpy.data.filepath:
        warnings.append("The file is not saved; exports will save a temporary copy first.")
    if not shots:
        errors.append("No timeline markers with a bound camera. A shot is a marker with a camera "
                      "(select the camera, put the playhead on the marker, Marker > Bind Camera to Markers).")
    ids = [s["id"] for s in shots]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if dups:
        errors.append({"msg": "Duplicate shot names", "items": dups})
    bad = [s["id"] for s in shots if s["scene"] is None]
    if bad:
        warnings.append({"msg": "Marker names do not match marker_regex", "count": len(bad), "items": bad[:30]})
    longs = [[s["id"], s["seconds"]] for s in shots if s["seconds"] > c["max_shot_seconds"]]
    if longs:
        warnings.append({"msg": f"Shots longer than {c['max_shot_seconds']} s (split them or pick a longer model)",
                         "count": len(longs), "items": longs[:30]})
    shorts = [[s["id"], s["seconds"]] for s in shots if s["seconds"] < c["min_shot_seconds"]]
    if shorts:
        warnings.append({"msg": f"Shots shorter than {c['min_shot_seconds']} s", "count": len(shorts), "items": shorts[:30]})
    sp = c["seq_prefix"].upper()
    breaks = [m.name for m in sc.timeline_markers if not m.camera and m.name.upper().startswith(sp)]
    if breaks:
        info.append({"msg": f"{c['seq_prefix']} markers force a new sequence", "count": len(breaks), "items": breaks[:20]})
    notes = [m.name for m in sc.timeline_markers if not m.camera and not m.name.upper().startswith(sp)]
    if notes:
        info.append({"msg": "Markers without a camera are treated as notes", "count": len(notes), "items": notes[:20]})
    cams = sorted({s["camera"] for s in shots})
    off = [x for x in cams if not x.startswith(c["camera_prefix"])]
    if off:
        info.append({"msg": f"Cameras without the {c['camera_prefix']} prefix", "items": off[:20]})
    chars = _chars(c)
    if not chars:
        errors.append(f"No characters: no top-level objects named {c['char_prefix']}*")
    movers = _travellers(c, chars, shots)
    if movers:
        warnings.append({"msg": "Objects that travel during shots but are neither characters nor props. "
                                "A moving rig is probably a character: rename it with the character prefix or "
                                "list it in blender.char_names. A carried or pushed object is a prop: use the "
                                "prop prefix or blender.prop_names. Otherwise its own motion is copied into "
                                "the reference", "count": len(movers), "items": movers[:30]})
    if c.get("aspect"):
        w, h = (float(x) for x in str(c["aspect"]).split(":"))
        if abs(r.resolution_x / r.resolution_y - w / h) > 0.01:
            warnings.append(f"Render aspect {r.resolution_x}x{r.resolution_y} differs from {c['aspect']}")
    return {"file": bpy.data.filepath, "blender": bpy.app.version_string, "engine": r.engine,
            "fps": _fps(sc), "resolution": [r.resolution_x, r.resolution_y], "frame_range": [sc.frame_start, sc.frame_end],
            "shots": len(shots), "scenes": sorted({s["scene"] for s in shots if s["scene"]}),
            "characters": [ch.name for ch in chars], "cameras": len(cams),
            "errors": errors, "warnings": warnings, "info": info, "ok": not errors}


def _shots_cmd(c, scene=None, ids=None, cast=False, camera=False):
    shots = _shots(c, scene)
    if ids:
        want = set(ids)
        shots = [s for s in shots if s["id"] in want]
    if cast or camera:
        sc = bpy.context.scene
        keep = sc.frame_current
        fps = _fps(sc)
        chars = _chars(c)
        for s in shots:
            cam = bpy.data.objects[s["camera"]]
            first = _cast_at(c, chars, cam, s["frame_start"])
            if cast:
                s["cast"] = {"first": first, "last": _cast_at(c, chars, cam, s["frame_end"])}
            if camera:
                cm = _camera(cam, s["frame_start"], s["frame_end"], fps, first)
                s["camera_move"] = {k: cm[k] for k in ("description", "static", "drift", "moves", "shot_size", "angle")}
        sc.frame_set(keep)
    return {"count": len(shots), "fps": _fps(bpy.context.scene), "shots": shots}


def _roots_at(chars, cam, frame):
    sc = bpy.context.scene
    sc.frame_set(frame)
    out = {}
    for ch in chars:
        p = ch.matrix_world.translation.copy()
        v = world_to_camera_view(sc, cam, p)
        out[ch.name] = (p, v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1)
    return out


def _continuity(c, scene=None, inside=False, step=1, cut_m=0.5):
    sc = bpy.context.scene
    keep = sc.frame_current
    shots, chars = _shots(c, scene), _chars(c)
    jumps, teleports = [], []
    prev, prev_end = None, {}
    for s in shots:
        cam = bpy.data.objects[s["camera"]]
        start = _roots_at(chars, cam, s["frame_start"])
        end = _roots_at(chars, cam, s["frame_end"])
        if prev and prev["scene"] == s["scene"]:
            for name, (p, vis) in start.items():
                q, qvis = prev_end[name]
                d = (p - q).length
                if d > c["jump_m"]:
                    jumps.append({"character": name, "from_shot": prev["id"], "to_shot": s["id"],
                                  "jump_m": round(d, 2), "visible_before": qvis, "visible_after": vis})
        if inside:
            last = None
            for f in range(s["frame_start"], s["frame_end"] + 1, max(1, int(step))):
                sc.frame_set(f)
                pos = {ch.name: ch.matrix_world.translation.copy() for ch in chars}
                if last:
                    for name, p in pos.items():
                        d = (p - last[name]).length
                        if d > cut_m * max(1, int(step)) and len(teleports) < 100:
                            teleports.append({"character": name, "shot": s["id"], "frame": f, "step_m": round(d, 2)})
                last = pos
        prev, prev_end = s, end
    sc.frame_set(keep)
    visible = [j for j in jumps if j["visible_before"] or j["visible_after"]]
    return {"scene": scene, "shots": len(shots), "jump_m": c["jump_m"], "jumps": jumps,
            "visible_jumps": len(visible), "teleports_inside_shots": teleports, "ok": not visible and not teleports}


def _seq_name(scene, i):
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return f"{scene}_{s}"


def _sequences(c, scene=None, target=(8, 15), max_seconds=30, min_seconds=4):
    """Propose sequences: consecutive shots of one scene that go to the video model as one generation."""
    sc = bpy.context.scene
    keep = sc.frame_current
    shots, chars = _shots(c, scene), _chars(c)
    sp = c["seq_prefix"].upper()
    breaks = sorted(m.frame for m in sc.timeline_markers if not m.camera and m.name.upper().startswith(sp))
    for s in shots:
        cam = bpy.data.objects[s["camera"]]
        seen = set()
        for f in (s["frame_start"], (s["frame_start"] + s["frame_end"]) // 2, s["frame_end"]):
            seen |= {n for n, v in _cast_at(c, chars, cam, f).items() if v["in_frame"]}
        s["in_frame"] = sorted(seen)
        sc.frame_set(s["frame_start"])
        s["_p0"] = {ch.name: ch.matrix_world.translation.copy() for ch in chars}
        sc.frame_set(s["frame_end"])
        s["_p1"] = {ch.name: ch.matrix_world.translation.copy() for ch in chars}
    sc.frame_set(keep)
    jump_cut = max(1.0, 3 * float(c["jump_m"]))
    lo, hi = float(target[0]), float(target[1])
    out, skipped = [], [s["id"] for s in shots if s["scene"] is None]
    scenes = []
    for s in shots:
        if s["scene"] is not None and s["scene"] not in scenes:
            scenes.append(s["scene"])
    for scn in scenes:
        lst = [s for s in shots if s["scene"] == scn]
        groups, cur, cast, prev = [], [], set(), None
        for s in lst:
            dur = sum(x["seconds"] for x in cur)
            new = set(s["in_frame"]) - cast
            forced = prev is not None and any(prev["frame_start"] < f <= s["frame_start"] for f in breaks)
            jumps = []
            if prev is not None:
                jumps = sorted(((s["_p0"][n] - prev["_p1"][n]).length, n) for n in s["_p0"])
                jumps = [f"{n} {d:.1f} m" for d, n in jumps if d > jump_cut]
            cut = None
            if cur:
                if forced:
                    cut = ("marker", f"{c['seq_prefix']} marker")
                elif dur + s["seconds"] > max_seconds:
                    cut = ("length", f"next shot would pass {max_seconds:g} s")
                elif jumps and dur >= min_seconds:
                    cut = ("natural", "jump across the cut: " + ", ".join(jumps))
                elif dur >= lo and new:
                    cut = ("natural", "enters: " + ", ".join(sorted(new)))
                elif dur >= hi or (dur >= lo and dur + s["seconds"] > hi):
                    cut = ("length", f"about {hi:g} s")
            if cut:
                groups.append([cur, cut])
                cur, cast = [], set()
            cur.append(s)
            cast |= set(s["in_frame"])
            prev = s
        if cur:
            groups.append([cur, ("end", "end of scene")])
        if len(groups) > 1:
            tail = sum(x["seconds"] for x in groups[-1][0])
            if tail < min_seconds and sum(x["seconds"] for x in groups[-2][0]) + tail <= max_seconds:
                groups[-2][0] += groups[-1][0]
                groups[-2][1] = groups[-1][1]
                groups.pop()
        for i, (g, (kind, why)) in enumerate(groups):
            secs = round(sum(x["seconds"] for x in g), 2)
            warn = []
            if secs < min_seconds:
                warn.append(f"shorter than {min_seconds:g} s: generate {min_seconds:g} s and trim")
            longs = [x["id"] for x in g if x["seconds"] > max_seconds]
            if longs:
                warn.append(f"shot longer than {max_seconds:g} s, split it in Blender: {longs}")
            out.append({"id": _seq_name(scn, i), "scene": scn, "shots": [x["id"] for x in g],
                        "frame_start": g[0]["frame_start"], "frame_end": g[-1]["frame_end"],
                        "seconds": secs, "cast": sorted({n for x in g for n in x["in_frame"]}),
                        "ends": why, "boundary": kind,
                        "sticky_next_suggested": kind == "length", "warnings": warn})
    return {"count": len(out), "target": [lo, hi], "max_seconds": max_seconds, "min_seconds": min_seconds,
            "sequences": out, "shots_without_scene": skipped[:50],
            "note": "A 'length' boundary may cut through an action: ask the owner whether the next "
                    "sequence is sticky (waits for this one and gets its last frame as a state reference)."}


def _put(out, st):
    st["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    st["updated_ts"] = time.time()
    tmp = os.path.join(out, "_status.json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(out, "_status.json"))


def _status(job):
    p = os.path.join(job, "_status.json")
    if not os.path.exists(p):
        return {"state": "unknown", "job": job}
    with open(p, encoding="utf-8") as fh:
        st = json.load(fh)
    st["age_s"] = round(time.time() - st.get("updated_ts", 0))
    if st.get("state") == "running" and st["age_s"] > 900:
        st["hint"] = "No progress for 15 min; read _worker.log in the job folder."
    return st


def _wrapper():
    q = "'" * 3
    return ("SRC = r" + q + SRC + q + "\n"
            "_TOON_NS = {'__name__': 'toon_blender_rt', 'SRC': SRC}\n"
            "exec(compile(SRC, 'toon_blender', 'exec'), _TOON_NS)\n"
            "TOON = _TOON_NS['TOON']\nVERSION = _TOON_NS['VERSION']\n")


def _install():
    d = bpy.utils.user_resource("SCRIPTS", path="modules", create=True)
    p = os.path.join(d, "toon_blender_core.py")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(_wrapper())
    if d not in sys.path:
        sys.path.append(d)
    if "toon_blender_core" in sys.modules:
        import importlib
        importlib.reload(sys.modules["toon_blender_core"])
    return {"installed": p, "version": VERSION,
            "next": "import importlib, toon_blender_core as T; importlib.reload(T); print(T.TOON('check'))"}


def _seq_list(c, shots=None, sequences=None):
    all_shots = _shots(c)
    known = {s["id"]: s for s in all_shots}
    order = [s["id"] for s in all_shots]
    want = [i for q in (sequences or []) for i in q.get("shots", [])] + list(shots or [])
    missing = [i for i in want if i not in known]
    if missing:
        raise ValueError(f"Shots not found: {missing}")
    seqs = []
    for q in sequences or []:
        ss = sorted((known[i] for i in q["shots"]), key=lambda s: s["frame_start"])
        if not ss:
            raise ValueError(f"Sequence {q.get('id')} has no shots")
        idx = [order.index(s["id"]) for s in ss]
        if idx != list(range(idx[0], idx[0] + len(idx))):
            raise ValueError(f"Sequence {q.get('id')}: shots must be consecutive on the timeline")
        seqs.append({"id": q.get("id") or ss[0]["id"], "shots": ss})
    for sid in shots or []:
        seqs.append({"id": sid, "shots": [known[sid]]})
    return seqs


def _export(c, shots=None, sequences=None, modes=("capsule",), out=None, ref_scale=100, still_scale=100,
            engine=None, props="show", stills=False):
    """Render the Blender reference of each sequence (all its shots, cuts included) plus sequence.json."""
    sc = bpy.context.scene
    r = sc.render
    modes = list(modes)
    badm = [m for m in modes if m not in MODES]
    if badm:
        raise ValueError(f"Unknown modes {badm}; use {list(MODES)}")
    if props not in ("show", "hide"):
        raise ValueError("props must be 'show' or 'hide'")
    seqs = _seq_list(c, shots, sequences)
    if not seqs:
        raise ValueError("Pass shots=[shot ids] or sequences=[{'id': ..., 'shots': [...]}]")
    out = os.path.abspath(bpy.path.abspath(out or "//toon_exports"))
    os.makedirs(out, exist_ok=True)
    chars, fps, keep = _chars(c), _fps(sc), sc.frame_current
    legend = _legend(c, chars)
    jobs = []
    for q in seqs:
        ss = q["shots"]
        f0, f1 = ss[0]["frame_start"], ss[-1]["frame_end"]
        d = os.path.join(out, _safe(q["id"]))
        os.makedirs(d, exist_ok=True)
        items, cast = [], set()
        for s in ss:
            cam = bpy.data.objects[s["camera"]]
            a = _cast_at(c, chars, cam, s["frame_start"])
            b = _cast_at(c, chars, cam, s["frame_end"])
            cast |= {n for half in (a, b) for n, v in half.items() if v["in_frame"]}
            items.append(dict(s, t0=round((s["frame_start"] - f0) / fps, 3),
                              t1=round((s["frame_end"] + 1 - f0) / fps, 3),
                              camera_move=_camera(cam, s["frame_start"], s["frame_end"], fps, a),
                              cast={"first": a, "last": b}))
        seconds = (f1 - f0 + 1) / fps
        files = {"ref_" + m: f"ref_{m}.mp4" for m in modes}
        still_list = []
        if stills:
            files["stills"] = {s["id"]: f"stills/{_safe(s['id'])}.png" for s in ss}
            still_list = [[files["stills"][s["id"]], s["frame_start"]] for s in ss]
        meta = {"toon_blender": VERSION, "sequence": q["id"], "scene": ss[0]["scene"], "fps": fps,
                "frame_start": f0, "frame_end": f1, "frames": f1 - f0 + 1, "seconds": round(seconds, 3),
                "suggested_duration": max(4, math.ceil(seconds - 1e-3)),
                "resolution": [r.resolution_x, r.resolution_y], "ref_scale": ref_scale,
                "blend": bpy.data.filepath, "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "in_frame": sorted(cast), "legend": legend, "props": props,
                "shots": items, "modes": modes, "files": files}
        with open(os.path.join(d, "sequence.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=1)
        jobs.append({"dir": d, "id": q["id"], "f0": f0, "f1": f1, "camera": ss[0]["camera"],
                     "modes": modes, "stills": still_list})
    sc.frame_set(keep)
    jp = os.path.join(out, "_job.json")
    with open(jp, "w", encoding="utf-8") as fh:
        json.dump({"version": VERSION, "out": out, "jobs": jobs, "cfg": c, "ref_scale": ref_scale,
                   "still_scale": still_scale, "engine": engine, "props": props}, fh,
                  ensure_ascii=False, indent=1)
    _put(out, {"state": "queued", "done": [], "errors": []})
    if bpy.app.background:
        _work(jp)
        return _status(out)
    src = bpy.data.filepath
    if not src or bpy.data.is_dirty:
        src = os.path.join(out, "_source.blend")
        bpy.ops.wm.save_as_mainfile(filepath=src, copy=True)
    worker = os.path.join(out, "_toon_worker.py")
    with open(worker, "w", encoding="utf-8") as fh:
        fh.write(_wrapper())
    log = open(os.path.join(out, "_worker.log"), "w", encoding="utf-8")
    kw = {"stdout": log, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL}
    if os.name == "nt":
        kw["creationflags"] = 0x08000000 | 0x00000200
    else:
        kw["start_new_session"] = True
    p = subprocess.Popen([bpy.app.binary_path, "-b", src, "--python", worker, "--", "toon-worker", jp], **kw)
    log.close()
    return {"job": out, "state": "running", "pid": p.pid, "source": src,
            "sequences": [q["id"] for q in seqs], "modes": modes,
            "next": f"TOON('status', job=r'{out}')"}


# --- worker: renders stills and reference videos -----------------------------

def _fmt(r, kind):
    s = r.image_settings
    if hasattr(s, "media_type"):
        try:
            s.media_type = "VIDEO" if kind == "video" else "IMAGE"
        except (TypeError, AttributeError):
            pass
    if kind == "video":
        s.file_format = "FFMPEG"
        for attr, val in (("format", "MPEG4"), ("codec", "H264"),
                          ("constant_rate_factor", "MEDIUM"), ("audio_codec", "NONE")):
            try:
                setattr(r.ffmpeg, attr, val)
            except (TypeError, AttributeError):
                pass
    else:
        s.file_format = "PNG"
        try:
            s.color_mode = "RGB"
        except TypeError:
            pass


def _still(sc, frame, path, scale):
    sc.frame_set(frame)
    _fmt(sc.render, "image")
    sc.render.resolution_percentage = int(scale)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _video(sc, f0, f1, path, scale):
    r = sc.render
    _fmt(r, "video")
    r.resolution_percentage = int(scale)
    parts = path + ".parts"
    shutil.rmtree(parts, ignore_errors=True)
    os.makedirs(parts)
    r.filepath = os.path.join(parts, "ref_")
    sc.frame_start, sc.frame_end = f0, f1
    bpy.ops.render.render(animation=True)
    made = sorted(glob.glob(os.path.join(parts, "*")), key=os.path.getmtime)
    if not made:
        raise RuntimeError(f"Blender wrote no video for {path}")
    os.replace(made[-1], path)
    shutil.rmtree(parts, ignore_errors=True)


def _force(o, prop, value, undo):
    muted = [fc for fc in _fcurves(o) if fc.data_path == prop and not fc.mute]
    for fc in muted:
        fc.mute = True
    old = getattr(o, prop)
    setattr(o, prop, value)

    def restore(o=o, old=old, muted=muted):
        setattr(o, prop, old)
        for fc in muted:
            fc.mute = False
    undo.append(restore)


def _capsule(c, ch, col, frame):
    bpy.context.scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in _family(ch):
        if o.type in GEOM and _renders(o) and not _isprop(c, o):
            e = o.evaluated_get(dg)
            pts += [e.matrix_world @ Vector(v) for v in e.bound_box]
    if not pts:
        return None
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    h = max(hi.z - lo.z, 0.05)
    rad = min(max(max(hi.x - lo.x, hi.y - lo.y) / 2, 0.12 * h), 0.3 * h)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=rad)
    half = max(h / 2 - rad, 0)
    for v in bm.verts:
        v.co.z += half if v.co.z > 0 else -half
    me = bpy.data.meshes.new(f"TOON_capsule_{ch.name}")
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.new(f"TOON_capsule_{ch.name}")
    try:
        mat.use_nodes = True
    except (AttributeError, TypeError):
        pass
    mat.diffuse_color = (*col, 1.0)
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if mat.node_tree else None
    if bsdf:
        # A little emission keeps the hue readable in shadow, so the colour legend holds.
        for ident, val in (("Base Color", (*col, 1.0)), ("Emission Color", (*col, 1.0)),
                           ("Emission", (*col, 1.0)), ("Emission Strength", 0.35), ("Roughness", 0.8)):
            sock = next((s for s in bsdf.inputs if s.identifier == ident), None)
            if sock is not None:
                try:
                    sock.default_value = val
                except (TypeError, ValueError):
                    pass
    me.materials.append(mat)
    ob = bpy.data.objects.new(f"TOON_capsule_{ch.name}", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + h / 2)
    bpy.context.view_layer.update()
    ob.parent = ch
    ob.matrix_parent_inverse = ch.matrix_world.inverted()
    return ob


def _freeze(objs, f0, undo):
    sc = bpy.context.scene
    sc.frame_set(f0)
    snap = []
    for o in objs:
        ad = o.animation_data
        if not ad or not (ad.action or len(ad.nla_tracks)):
            continue
        poses = None
        if o.type == "ARMATURE" and o.pose:
            poses = {pb.name: pb.matrix_basis.copy() for pb in o.pose.bones}
        snap.append((o, o.matrix_world.copy(), poses, o.hide_render))
    for o, _mw, _p, _h in snap:
        ad = o.animation_data
        act, slot = ad.action, getattr(ad, "action_slot", None)
        tracks = [(t, t.mute) for t in ad.nla_tracks]
        ad.action = None
        for t, _m in tracks:
            t.mute = True

        def restore(ad=ad, act=act, slot=slot, tracks=tracks):
            ad.action = act
            if act is not None and slot is not None and hasattr(ad, "action_slot"):
                try:
                    ad.action_slot = slot
                except Exception:
                    pass
            for t, m in tracks:
                t.mute = m
        undo.append(restore)
    for o, mw, poses, hid in sorted(snap, key=lambda s: _depth(s[0])):
        o.matrix_world = mw
        if poses:
            for name, m in poses.items():
                o.pose.bones[name].matrix_basis = m
        o.hide_render = hid
    undo.append(lambda: sc.frame_set(f0))


def _visibility(c, chars, f0, f1):
    """Per character, per frame: does any body part render? Read before anything is forced hidden."""
    sc = bpy.context.scene
    vis = {ch.name: [] for ch in chars}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for ch in chars:
            vis[ch.name].append(any(o.type in GEOM and _renders(o) and not _isprop(c, o) for o in _family(ch)))
    sc.frame_set(f0)
    return vis


def _capsules(c, chars, f0, f1):
    legend = _legend(c, chars)
    vis = _visibility(c, chars, f0, f1)
    caps = []
    for ch in chars:
        v = vis[ch.name]
        if not any(v):
            continue
        first = f0 + v.index(True)
        cap = _capsule(c, ch, legend[ch.name]["rgb"], first)
        if cap is None:
            continue
        if not all(v):
            prev = None
            for i, on in enumerate(v):
                if on != prev:
                    cap.hide_render = not on
                    cap.keyframe_insert("hide_render", frame=f0 + i)
                    prev = on
        caps.append(cap)
    bpy.context.scene.frame_set(f0)
    return caps


def _apply_mode(mode, c, chars, f0, f1, undo, props="show"):
    """full: as is. hidden: characters gone. capsule: a coloured capsule per character on its root,
    visible exactly when the character is. frozen: characters (and their props) held in their
    first-frame pose. Props stay visible unless props='hide'."""
    sc = bpy.context.scene
    sc.frame_set(f0)
    fam = [o for ch in chars for o in _family(ch)]
    body = [o for o in fam if not _isprop(c, o)]
    held = [o for o in fam if _isprop(c, o)]
    loose = _loose_props(c, chars)
    if mode == "full":
        return
    if mode in ("hidden", "capsule"):
        if mode == "capsule":
            caps = _capsules(c, chars, f0, f1)
            undo.append(lambda caps=caps: [bpy.data.objects.remove(x, do_unlink=True) for x in caps if x])
        for o in body + ((held + loose) if props == "hide" else []):
            _force(o, "hide_render", True, undo)
    elif mode == "frozen":
        _freeze(fam + loose, f0, undo)


def _work(jp):
    with open(jp, encoding="utf-8") as fh:
        job = json.load(fh)
    out, c = job["out"], job["cfg"]
    st = {"state": "running", "pid": os.getpid(), "started": time.strftime("%Y-%m-%d %H:%M:%S"),
          "done": [], "errors": [], "current": None, "frame": None}
    _put(out, st)
    sc = bpy.context.scene

    def tick(scene, *_a):
        st["frame"] = scene.frame_current
        if scene.frame_current % 12 == 0:
            _put(out, st)
    bpy.app.handlers.render_post.append(tick)
    if job.get("engine"):
        try:
            sc.render.engine = job["engine"]
        except TypeError as e:
            st["errors"].append(f"engine: {e}")
    chars = _chars(c)
    t0 = time.time()
    try:
        for j in job["jobs"]:
            d, f0, f1 = j["dir"], j["f0"], j["f1"]
            sc.camera = bpy.data.objects[j["camera"]]
            for rel, f in j["stills"]:
                path = os.path.join(d, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                st["current"] = f"{j['id']}/{rel}"
                _put(out, st)
                _still(sc, f, path, job["still_scale"])
                st["done"].append(path)
            for m in j["modes"]:
                st["current"] = f"{j['id']}/ref_{m}.mp4"
                _put(out, st)
                undo = []
                try:
                    _apply_mode(m, c, chars, f0, f1, undo, job.get("props", "show"))
                    _video(sc, f0, f1, os.path.join(d, f"ref_{m}.mp4"), job["ref_scale"])
                    st["done"].append(os.path.join(d, f"ref_{m}.mp4"))
                finally:
                    for fn in reversed(undo):
                        fn()
                    sc.frame_set(f0)
        st["state"] = "done"
    except Exception:
        import traceback
        st["state"] = "error"
        st["errors"].append(traceback.format_exc())
    finally:
        if tick in bpy.app.handlers.render_post:
            bpy.app.handlers.render_post.remove(tick)
    st["current"] = None
    st["seconds"] = round(time.time() - t0)
    _put(out, st)


# --- entry points --------------------------------------------------------------

def _dispatch(cmd, kw):
    c = _cfg(kw)
    if cmd == "version":
        return {"version": VERSION, "blender": bpy.app.version_string, "file": bpy.data.filepath,
                "background": bpy.app.background}
    if cmd == "install":
        return _install()
    if cmd == "check":
        return _check(c)
    if cmd == "shots":
        return _shots_cmd(c, **kw)
    if cmd == "continuity":
        return _continuity(c, **kw)
    if cmd == "sequences":
        return _sequences(c, **kw)
    if cmd == "export":
        return _export(c, **kw)
    if cmd == "status":
        return _status(kw["job"])
    raise ValueError(f"Unknown command {cmd!r}: use version, install, check, shots, continuity, "
                     f"sequences, export, status")


def TOON(cmd, **kw):
    try:
        res = _dispatch(cmd, dict(kw))
    except Exception as e:
        import traceback
        res = {"error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc(limit=4)}
    return json.dumps(res, ensure_ascii=False, indent=1, default=str)


def _cli():
    if not bpy.app.background or "--" not in sys.argv:
        return
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) >= 2 and args[0] == "toon-worker":
        _work(args[1])
        return
    if not args or args[0] != "toon":
        return
    raw = args[1] if len(args) > 1 else '{"cmd": "check"}'
    try:
        if raw.startswith("@"):
            with open(raw[1:], encoding="utf-8-sig") as fh:
                raw = fh.read()
        payload = json.loads(raw)
        calls = payload if isinstance(payload, list) else [payload]
        res = []
        for call in calls:
            call = dict(call)
            res.append(json.loads(TOON(call.pop("cmd", ""), **call)))
        res = res if isinstance(payload, list) else res[0]
    except (OSError, ValueError, TypeError, AttributeError) as e:
        res = {"error": f"Bad toon arguments: {type(e).__name__}: {e}",
               "usage": "-- toon '{\"cmd\": \"check\"}'  or  -- toon @calls.json (UTF-8 JSON object or list)"}
    text = json.dumps(res, ensure_ascii=False, indent=1, default=str)
    target = os.environ.get("TOON_RESULT")
    if target:
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(text)
    print("<<<TOON")
    print(json.dumps(res, ensure_ascii=True, indent=1, default=str))
    print("TOON>>>")


_cli()
'''

# Run the module in its own namespace, so it works however the caller (Blender, an MCP) runs this file.
_TOON_NS = {"__name__": "toon_blender_rt", "SRC": SRC}
exec(compile(SRC, "toon_blender", "exec"), _TOON_NS)
TOON = _TOON_NS["TOON"]
VERSION = _TOON_NS["VERSION"]
