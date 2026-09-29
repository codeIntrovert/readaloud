import { useEffect, useRef, useState } from "react";

const api = async (url, opts) => {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || "Request failed");
  return r.json();
};
const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;

export default function App() {
  const [items, setItems] = useState([]);
  const [voices, setVoices] = useState({ piper: [], elevenlabs: [] });
  const [provider, setProvider] = useState("piper");
  const [voice, setVoice] = useState("");
  const [speed, setSpeed] = useState(1);
  const [text, setText] = useState("");
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const end = useRef(null), file = useRef(null);

  useEffect(() => { api("/api/voices").then(setVoices).catch((e) => setError(e.message)); }, []);
  useEffect(() => { setVoice(voices[provider]?.[0] || ""); }, [provider, voices]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [items]);
  useEffect(() => {
    const t = setTimeout(() => api(q ? `/api/search?q=${encodeURIComponent(q)}` : "/api/messages")
      .then(setItems).catch((e) => setError(e.message)), 250);
    return () => clearTimeout(t);
  }, [q]);

  const run = async (req) => {
    setBusy(true); setError("");
    try { const job = await req(); setItems((x) => [...x, job]); setText(""); }
    catch (e) { setError(e.message); }
    setBusy(false);
  };
  const send = () => text.trim() && run(() => api("/api/chat", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, provider, voice, speed }) }));
  const upload = (f) => {
    const fd = new FormData();
    fd.append("file", f); fd.append("provider", provider); fd.append("voice", voice); fd.append("speed", speed);
    run(() => api("/api/upload", { method: "POST", body: fd }));
  };

  const field = "rounded-md border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900";
  return (
    <div className="mx-auto flex h-dvh max-w-3xl flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="space-y-3 border-b border-slate-200 p-4 dark:border-slate-800">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-lg font-semibold">Readaloud</h1>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search past texts"
                 className={field + " w-48"} aria-label="Search" />
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <select className={field} value={provider} onChange={(e) => setProvider(e.target.value)} aria-label="Engine">
            <option value="piper">Standard (Piper)</option>
            {voices.elevenlabs.length > 0 && <option value="elevenlabs">Premium (ElevenLabs)</option>}
          </select>
          <select className={field} value={voice} onChange={(e) => setVoice(e.target.value)} aria-label="Voice">
            {(voices[provider] || []).map((v) => <option key={v}>{v}</option>)}
          </select>
          <label className="flex items-center gap-2">Speed
            <input type="range" min="0.7" max="1.5" step="0.1" value={speed} onChange={(e) => setSpeed(+e.target.value)} />
            <span className="w-8">{speed.toFixed(1)}×</span>
          </label>
        </div>
      </header>

      <main className="flex-1 space-y-4 overflow-y-auto p-4">
        {items.length === 0 && (
          <p className="mt-16 text-center text-slate-500">
            {q ? "No saved texts match that search." : "Type some text or attach a PDF, DOCX or TXT file to hear it read aloud."}
          </p>
        )}
        {items.map((m) => (
          <div key={m.id} className="space-y-2">
            <div className="ml-auto max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-teal-700 px-4 py-2 text-white">
              {m.source !== "chat" && <div className="mb-1 text-xs opacity-80">{m.source}</div>}
              {m.text}{m.chars > 400 && "…"}
            </div>
            <div className="max-w-[85%] rounded-2xl rounded-bl-sm bg-slate-200 p-3 dark:bg-slate-800">
              <audio controls preload="none" src={m.audio_url} className="w-full" />
              <div className="mt-1 flex justify-between gap-3 text-xs text-slate-500">
                <span>{m.provider}, {m.voice}</span><span>{fmt(m.duration)}</span>
                <a className="underline" href={m.audio_url} download={`readaloud-${m.id.slice(0, 6)}.mp3`}>Download MP3</a>
              </div>
            </div>
          </div>
        ))}
        {busy && <p className="text-sm text-slate-500">Generating audio…</p>}
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <div ref={end} />
      </main>

      <footer className="flex gap-2 border-t border-slate-200 p-3 dark:border-slate-800">
        <input ref={file} type="file" accept=".pdf,.docx,.txt,.md" hidden
               onChange={(e) => { e.target.files[0] && upload(e.target.files[0]); e.target.value = ""; }} />
        <button onClick={() => file.current.click()} disabled={busy} className={field + " px-3"}>Attach</button>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} placeholder="Type or paste text"
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
                  className={field + " flex-1 resize-none"} />
        <button onClick={send} disabled={busy || !text.trim()}
                className="rounded-md bg-teal-700 px-4 text-white disabled:opacity-50">Convert</button>
      </footer>
    </div>
  );
}
