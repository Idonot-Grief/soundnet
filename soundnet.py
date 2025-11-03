# -*- coding: cp1252 -*-
#!/usr/bin/env python3
"""
SoundNet Scope Server with Volume Slider
Minimalist dark webpage with green waveform scope, toggle, footer.
Streams audio from MAONO AU-AM200 via ffmpeg (dshow).
"""

import http.server, socketserver, subprocess

# Config
IP   = "0.0.0.0"
PORT = 5000
FFMPEG_PATH = r"./ffmpeg.exe"

# Audio command (Audio Input, 44.1kHz, 192k bitrate, MP3 format)
FFMPEG_AUDIO_CMD = [
    FFMPEG_PATH,
    "-f", "dshow",
    "-i", "audio=<System Microphone Name>",
    "-ar", "44100",
    "-ac", "1",
    "-b:a", "192k",
    "-f", "mp3",
    "-"
]

class ScopeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self.page_html().encode())

        elif self.path == "/audio":
            self.stream_audio()

        else:
            self.send_error(404, "Not Found")

    def page_html(self):
        return """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>SoundNet</title>
  <style>
    body {
      margin: 0; padding: 0;
      background: #111; color: #ccc;
      font-family: sans-serif; text-align: center;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      height: 100vh;
    }
    canvas {
      width: 90%; height: 200px;
      background: #000;
      border-radius: 6px;
      display: block;
    }
    button {
      margin-top: 12px;
      padding: 10px 20px;
      border: none; border-radius: 6px;
      background: #222; color: #0f0;
      cursor: pointer;
    }
    input[type=range] {
      -webkit-appearance: none;
      width: 90%;
      margin-top: 12px;
      height: 6px;
      background: #222;
      border-radius: 6px;
      outline: none;
    }
    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 16px; height: 16px;
      border-radius: 50%;
      background: #0f0;
      cursor: pointer;
    }
    footer {
      margin-top: 12px;
      font-size: 12px;
      color: #666;
    }
  </style>
</head>
<body>
  <canvas id="scope"></canvas>
  <button id="btn">Start Audio</button>
  <input type="range" id="vol" min="0" max="1" step="0.01" value="1">
  <footer>Powered by SoundNet</footer>
  <script>
    const audio = new Audio();
    audio.src = "/audio";
    audio.crossOrigin = "anonymous";
    let ctx, analyser, source, gainNode, dataArray;
    let started = false;

    const button = document.getElementById("btn");
    const slider = document.getElementById("vol");
    const canvas = document.getElementById("scope");
    const cctx = canvas.getContext("2d");

    function resize() {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    }
    resize(); window.onresize = resize;

    function draw() {
      requestAnimationFrame(draw);
      if (!analyser) return;
      analyser.getByteTimeDomainData(dataArray);
      cctx.fillStyle = "#000";
      cctx.fillRect(0,0,canvas.width,canvas.height);
      cctx.strokeStyle = "#0f0";
      cctx.beginPath();
      const slice = canvas.width / dataArray.length;
      for (let i=0;i<dataArray.length;i++) {
        const x = i * slice;
        let v = (dataArray[i] - 128) / 128.0; 
        v *= 1.5; // scope boost for visibility
        const y = (0.5 - v/2) * canvas.height;
        if (i===0) cctx.moveTo(x,y);
        else cctx.lineTo(x,y);
      }
      cctx.stroke();
    }

    button.onclick = () => {
      if (!started) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        ctx = new AudioCtx();
        source = ctx.createMediaElementSource(audio);
        analyser = ctx.createAnalyser();
        gainNode = ctx.createGain();
        analyser.fftSize = 2048;
        dataArray = new Uint8Array(analyser.frequencyBinCount);
        source.connect(analyser);
        analyser.connect(gainNode);
        gainNode.connect(ctx.destination);
        audio.play();
        draw();
        button.innerText = "Stop Audio";
        started = true;
      } else {
        audio.pause();
        button.innerText = "Start Audio";
        started = false;
      }
    };

    slider.oninput = () => {
      if (gainNode) {
        gainNode.gain.value = slider.value;
      }
    };
  </script>
</body>
</html>
"""

    def stream_audio(self):
        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.end_headers()
        try:
            ffmpeg = subprocess.Popen(FFMPEG_AUDIO_CMD, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            while True:
                data = ffmpeg.stdout.read(1024)
                if not data: break
                self.wfile.write(data)
        except Exception as e:
            print("[Audio] Error:", e)
        finally:
            try: ffmpeg.kill()
            except: pass

def start_server():
    with socketserver.ThreadingTCPServer((IP, PORT), ScopeHandler) as server:
        print(f"[SERVER] Running at http://{IP}:{PORT}/")
        server.serve_forever()

if __name__=="__main__":
    start_server()
