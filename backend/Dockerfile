FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Default Piper voice (add more .onnx + .onnx.json files to /models)
RUN mkdir -p /models /data/audio && cd /models && \
    B=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium && \
    curl -fLO $B/en_US-lessac-medium.onnx && curl -fLO $B/en_US-lessac-medium.onnx.json
COPY app app
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
