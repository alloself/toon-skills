#!/usr/bin/env python3
"""media.py: ffmpeg helpers for toon-skills. Needs ffmpeg and ffprobe on PATH, Python 3.8+.

  probe  FILE                                  JSON: duration, fps, width, height, frames
  frames VIDEO OUTDIR [--at first,last,1.5] [--every SEC] [--prefix f]
  sheet  VIDEO OUT.png [--cols 6] [--rows 3] [--width 320]
  pair   A B OUT.png [--height 540]            side by side, for "layout vs generated"
  compare REF TAKE OUT.png --at 1.2,3.4 [--height 270]
                                               one row per time: reference frame | take frame
  pad    IN OUT --seconds S                    hold the last frame until S seconds
  fit    IN OUT --seconds S [--how auto|retime|trim]
                                               auto: retime if the length ratio is within 1.25, else trim
  concat OUT IN [IN ...] [--fps 24] [--size 1920x1080]
                                               re-encode to one fps and size, no audio
  fetch  URL OUT                               download a generation result

Every command prints one JSON line with what it wrote.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request


def _need(tool):
    if not shutil.which(tool):
        sys.exit(json.dumps({"error": f"{tool} not found on PATH"}))


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        sys.exit(json.dumps({"error": "ffmpeg failed", "cmd": cmd, "stderr": p.stderr[-1500:]}))
    return p.stdout


def probe(path):
    _need("ffprobe")
    out = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "json", path])
    d = json.loads(out)
    st = (d.get("streams") or [{}])[0]
    num, _, den = st.get("r_frame_rate", "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    dur = float(d.get("format", {}).get("duration") or 0)
    frames = int(st["nb_frames"]) if str(st.get("nb_frames", "")).isdigit() else int(round(dur * fps))
    return {"file": path, "duration": round(dur, 3), "fps": round(fps, 3),
            "width": st.get("width"), "height": st.get("height"), "frames": frames}


def _grab(video, t, out):
    _run(["ffmpeg", "-y", "-v", "error", "-i", video, "-ss", f"{max(t, 0):.3f}", "-frames:v", "1", out])
    return out


def frames(a):
    _need("ffmpeg")
    info = probe(a.video)
    os.makedirs(a.outdir, exist_ok=True)
    step = 1.0 / info["fps"] if info["fps"] else 0.04
    times = []
    if a.every:
        t = 0.0
        while t < info["duration"] - step / 2:
            times.append(round(t, 3))
            t += a.every
    for item in (a.at.split(",") if a.at else []):
        item = item.strip()
        if item == "first":
            times.append(0.0)
        elif item == "last":
            times.append(max(info["duration"] - step, 0.0))
        elif item:
            times.append(float(item))
    written = []
    for t in sorted(set(times)):
        name = os.path.join(a.outdir, f"{a.prefix}_{t:.3f}s.png")
        written.append(_grab(a.video, t, name))
    return {"frames": written, "duration": info["duration"]}


def sheet(a):
    _need("ffmpeg")
    info = probe(a.video)
    n = a.cols * a.rows
    total = max(info["frames"], 1)
    picks = sorted({min(total - 1, int(total * (i + 0.5) / n)) for i in range(n)})
    expr = "+".join(f"eq(n\\,{k})" for k in picks)
    vf = f"select='{expr}',scale={a.width}:-2,tile={a.cols}x{a.rows}:padding=4:color=black"
    _run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-vf", vf, "-frames:v", "1", "-fps_mode", "vfr", a.out])
    return {"sheet": a.out, "frames": [round(k / info["fps"], 2) for k in picks] if info["fps"] else picks}


def pair(a):
    _need("ffmpeg")
    fc = f"[0:v]scale=-2:{a.height}[l];[1:v]scale=-2:{a.height}[r];[l][r]hstack=inputs=2"
    _run(["ffmpeg", "-y", "-v", "error", "-i", a.a, "-i", a.b, "-filter_complex", fc, "-frames:v", "1", a.out])
    return {"pair": a.out}


def compare(a):
    """Rows of reference | take at the given times, for review."""
    _need("ffmpeg")
    import tempfile
    times = [float(t) for t in a.at.split(",") if t.strip()]
    if not times:
        sys.exit(json.dumps({"error": "--at needs at least one time"}))
    ref_d, take_d = probe(a.ref)["duration"], probe(a.take)["duration"]
    tmp = tempfile.mkdtemp(prefix="toon_cmp_")
    inputs = []
    for i, t in enumerate(times):
        for tag, src, dur in (("r", a.ref, ref_d), ("t", a.take, take_d)):
            p = os.path.join(tmp, f"{tag}{i}.png")
            _grab(src, min(t, max(dur - 0.05, 0)), p)
            inputs.append(p)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for p in inputs:
        cmd += ["-i", p]
    parts, rows = [], []
    for i in range(len(inputs)):
        parts.append(f"[{i}:v]scale=-2:{a.height},setsar=1[s{i}]")
    for r in range(len(times)):
        parts.append(f"[s{2 * r}][s{2 * r + 1}]hstack=inputs=2[row{r}]")
        rows.append(f"[row{r}]")
    if len(rows) > 1:
        parts.append("".join(rows) + f"vstack=inputs={len(rows)}[out]")
        last = "[out]"
    else:
        last = "[row0]"
    cmd += ["-filter_complex", ";".join(parts), "-map", last, "-frames:v", "1", a.out]
    _run(cmd)
    shutil.rmtree(tmp, ignore_errors=True)
    return {"compare": a.out, "times": times, "left": a.ref, "right": a.take}


def _encode(src, vf, out, extra=None):
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf, "-an", "-c:v", "libx264",
           "-crf", "18", "-pix_fmt", "yuv420p"] + (extra or []) + [out]
    _run(cmd)
    return out


def pad(a):
    _need("ffmpeg")
    info = probe(a.inp)
    extra = max(a.seconds - info["duration"], 0)
    _encode(a.inp, f"tpad=stop_mode=clone:stop_duration={extra:.3f}", a.out, ["-t", f"{a.seconds:.3f}"])
    return {"out": a.out, "from": info["duration"], "to": a.seconds}


def fit(a):
    _need("ffmpeg")
    info = probe(a.inp)
    ratio = info["duration"] / a.seconds if a.seconds else 1
    how = a.how
    if how == "auto":
        how = "retime" if 0.8 <= ratio <= 1.25 else "trim"
    if how == "retime":
        _encode(a.inp, f"setpts=PTS*{a.seconds / info['duration']:.6f}", a.out, ["-t", f"{a.seconds:.3f}"])
    else:
        _encode(a.inp, "null", a.out, ["-t", f"{a.seconds:.3f}"])
    return {"out": a.out, "how": how, "from": info["duration"], "to": a.seconds}


def concat(a):
    _need("ffmpeg")
    w, h = (int(x) for x in a.size.lower().split("x"))
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for f in a.inputs:
        cmd += ["-i", f]
    parts = []
    for i in range(len(a.inputs)):
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={a.fps},scale={w}:{h}:force_original_aspect_ratio=decrease,"
                     f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]")
    fc = ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(len(a.inputs))) + f"concat=n={len(a.inputs)}:v=1:a=0[out]"
    cmd += ["-filter_complex", fc, "-map", "[out]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", a.out]
    _run(cmd)
    return {"out": a.out, "clips": len(a.inputs), **{k: v for k, v in probe(a.out).items() if k != "file"}}


def fetch(a):
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    req = urllib.request.Request(a.url, headers={"User-Agent": "toon-skills/0.1"})
    with urllib.request.urlopen(req, timeout=300) as r, open(a.out, "wb") as fh:
        shutil.copyfileobj(r, fh)
    return {"out": a.out, "bytes": os.path.getsize(a.out)}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("probe"); s.add_argument("file")
    s = sub.add_parser("frames"); s.add_argument("video"); s.add_argument("outdir")
    s.add_argument("--at", default="first,last"); s.add_argument("--every", type=float); s.add_argument("--prefix", default="f")
    s = sub.add_parser("sheet"); s.add_argument("video"); s.add_argument("out")
    s.add_argument("--cols", type=int, default=6); s.add_argument("--rows", type=int, default=3); s.add_argument("--width", type=int, default=320)
    s = sub.add_parser("pair"); s.add_argument("a"); s.add_argument("b"); s.add_argument("out"); s.add_argument("--height", type=int, default=540)
    s = sub.add_parser("compare"); s.add_argument("ref"); s.add_argument("take"); s.add_argument("out")
    s.add_argument("--at", required=True); s.add_argument("--height", type=int, default=270)
    s = sub.add_parser("pad"); s.add_argument("inp"); s.add_argument("out"); s.add_argument("--seconds", type=float, required=True)
    s = sub.add_parser("fit"); s.add_argument("inp"); s.add_argument("out"); s.add_argument("--seconds", type=float, required=True)
    s.add_argument("--how", choices=["auto", "retime", "trim"], default="auto")
    s = sub.add_parser("concat"); s.add_argument("out"); s.add_argument("inputs", nargs="+")
    s.add_argument("--fps", type=float, default=24); s.add_argument("--size", default="1920x1080")
    s = sub.add_parser("fetch"); s.add_argument("url"); s.add_argument("out")
    a = p.parse_args()
    fn = {"probe": lambda a: probe(a.file), "frames": frames, "sheet": sheet, "pair": pair, "compare": compare,
          "pad": pad, "fit": fit, "concat": concat, "fetch": fetch}[a.cmd]
    print(json.dumps(fn(a), ensure_ascii=False))


if __name__ == "__main__":
    main()
