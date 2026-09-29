import glob, os, re, subprocess, tempfile, httpx
from . import config as c, audio

def voices() -> dict:
    piper = sorted(os.path.basename(p)[:-5] for p in glob.glob(f"{c.PIPER_MODELS}/*.onnx"))
    return {"piper": piper, "elevenlabs": [c.ELEVEN_VOICE] if c.ELEVEN_KEY else []}

def chunks(text: str, limit: int = 1500):
    """Split on sentence ends so long documents synthesize in manageable pieces."""
    buf = ""
    for s in re.split(r"(?<=[.!?\n])\s+", text.strip()):
        if buf and len(buf) + len(s) > limit:
            yield buf.strip(); buf = ""
        buf += s + " "
    if buf.strip(): yield buf.strip()

def _piper(text, voice, speed, out_mp3, tmp):
    wav = os.path.join(tmp, "p.wav")
    subprocess.run(["python", "-m", "piper", "-m", f"{c.PIPER_MODELS}/{voice}.onnx", "-f", wav,
                    "--length_scale", str(round(1 / speed, 2))],
                   input=text.encode(), check=True, capture_output=True)
    audio.to_mp3(wav, out_mp3)

def _eleven(text, voice, speed, out_mp3, tmp):
    if not c.ELEVEN_KEY: raise RuntimeError("ElevenLabs is not configured")
    r = httpx.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice or c.ELEVEN_VOICE}",
                   headers={"xi-api-key": c.ELEVEN_KEY},
                   params={"output_format": "mp3_22050_32"},
                   json={"text": text, "model_id": "eleven_multilingual_v2",
                         "voice_settings": {"speed": min(1.2, max(0.7, speed))}}, timeout=120)
    r.raise_for_status()
    with open(out_mp3, "wb") as f: f.write(r.content)

def synthesize(text: str, provider: str, voice: str, speed: float, dst: str) -> float:
    fn = {"piper": _piper, "elevenlabs": _eleven}[provider]
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for i, part in enumerate(chunks(text)):
            p = os.path.join(tmp, f"{i}.mp3")
            fn(part, voice, speed, p, tmp); parts.append(p)
        audio.concat(parts, dst)
    return audio.duration(dst)
