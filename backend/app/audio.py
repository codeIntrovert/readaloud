import subprocess, shutil

def _run(cmd): subprocess.run(cmd, check=True, capture_output=True)

def to_mp3(src: str, dst: str):
    _run(["ffmpeg", "-y", "-i", src, "-ar", "22050", "-ac", "1", "-codec:a", "libmp3lame", "-q:a", "4", dst])

def concat(parts: list[str], dst: str):
    if len(parts) == 1:
        shutil.move(parts[0], dst); return
    lst = dst + ".txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", dst])

def duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", path], capture_output=True, text=True)
    return float(out.stdout.strip() or 0)
