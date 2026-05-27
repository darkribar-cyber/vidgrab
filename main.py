from flask import Flask, request, jsonify, send_file, render_template_string
import subprocess
import os
import uuid
import threading
import time
import json

app = Flask(__name__)

DOWNLOAD_FOLDER = os.path.expanduser("/sdcard/VidGrab")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# İndirme durumlarını tut
jobs = {}

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>VidGrab</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Space+Mono&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0d0d1a;
    color: #cce0ff;
    font-family: 'Space Mono', monospace;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 16px;
  }

  h1 {
    font-family: 'Orbitron', sans-serif;
    font-size: 26px;
    color: #00f5a0;
    letter-spacing: 4px;
    margin-bottom: 4px;
  }

  .sub { color: #334455; font-size: 11px; letter-spacing: 3px; margin-bottom: 28px; }

  .card {
    background: #12121f;
    border: 1px solid #1e2d3d;
    border-radius: 20px;
    padding: 24px;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 20px 60px #00000080;
  }

  .input-wrap {
    background: #0d0d1a;
    border: 1px solid #1e2d3d;
    border-radius: 12px;
    display: flex;
    align-items: center;
    padding: 4px 4px 4px 14px;
    margin-bottom: 16px;
  }

  .input-wrap input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #cce0ff;
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    padding: 10px 0;
  }

  .input-wrap input::placeholder { color: #334455; }

  .clear-btn {
    background: none;
    border: none;
    color: #445566;
    font-size: 20px;
    padding: 6px 12px;
    cursor: pointer;
  }

  .label {
    color: #445566;
    font-size: 10px;
    letter-spacing: 2px;
    margin-bottom: 8px;
  }

  .quality-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 20px;
  }

  .q-btn {
    padding: 6px 14px;
    border-radius: 8px;
    border: 1px solid #1e2d3d;
    background: transparent;
    color: #445566;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .q-btn.active {
    border-color: #00f5a0;
    color: #00f5a0;
    background: #00f5a015;
  }

  .divider { height: 1px; background: #1e2d3d; margin-bottom: 20px; }

  .main-btn {
    width: 100%;
    padding: 14px;
    border-radius: 12px;
    border: none;
    background: linear-gradient(135deg, #00f5a0, #00d9f5);
    color: #0d0d1a;
    font-family: 'Orbitron', sans-serif;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 2px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .main-btn:disabled {
    background: #1e2d3d;
    color: #334455;
    cursor: not-allowed;
  }

  .main-btn:active { transform: scale(0.97); }

  .progress-wrap { margin: 16px 0; }

  .progress-label {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #445566;
    margin-bottom: 6px;
  }

  .progress-label span:last-child { color: #00f5a0; }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: #1a1a2e;
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #00f5a0, #00d9f5);
    border-radius: 4px;
    transition: width 0.4s ease;
    box-shadow: 0 0 10px #00f5a080;
    width: 0%;
  }

  .status-box {
    padding: 12px 16px;
    border-radius: 10px;
    font-size: 12px;
    margin-bottom: 16px;
    line-height: 1.6;
  }

  .status-box.info {
    background: #0d1520;
    border: 1px solid #1e2d3d;
    color: #8899aa;
  }

  .status-box.success {
    background: #00f5a015;
    border: 1px solid #00f5a040;
    color: #00f5a0;
    text-align: center;
  }

  .status-box.error {
    background: #ff003315;
    border: 1px solid #ff003340;
    color: #ff6688;
  }

  .spinner {
    display: inline-block;
    animation: spin 1s linear infinite;
    margin-right: 6px;
  }

  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
  .fadein { animation: fadeIn 0.3s ease; }
</style>
</head>
<body>

<h1>VID<span style="color:#00d9f5">GRAB</span></h1>
<div class="sub">VIDEO İNDİRİCİ</div>

<div class="card">
  <div class="input-wrap">
    <span style="font-size:18px;opacity:0.4;margin-right:10px">⬇</span>
    <input type="url" id="urlInput" placeholder="Video linkini yapıştır..." />
    <button class="clear-btn" onclick="clearUrl()">×</button>
  </div>

  <div class="label">KALİTE</div>
  <div class="quality-grid">
    <button class="q-btn" onclick="setQ(this,'1080')">1080p HD</button>
    <button class="q-btn active" onclick="setQ(this,'720')">720p HD</button>
    <button class="q-btn" onclick="setQ(this,'480')">480p</button>
    <button class="q-btn" onclick="setQ(this,'360')">360p</button>
    <button class="q-btn" onclick="setQ(this,'mp3')">🎵 MP3</button>
  </div>

  <div class="divider"></div>

  <div id="statusArea"></div>

  <button class="main-btn" id="mainBtn" onclick="startDownload()">⬇ İNDİR</button>
</div>

<script>
let selectedQuality = '720';
let polling = null;

function setQ(el, q) {
  document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  selectedQuality = q;
}

function clearUrl() {
  document.getElementById('urlInput').value = '';
  document.getElementById('statusArea').innerHTML = '';
}

function setStatus(html) {
  document.getElementById('statusArea').innerHTML = html;
}

function setBtn(text, disabled) {
  const btn = document.getElementById('mainBtn');
  btn.innerHTML = text;
  btn.disabled = disabled;
}

async function startDownload() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { alert('Lütfen bir link gir!'); return; }

  setBtn('<span class="spinner">◌</span> BAŞLATIYOR...', true);
  setStatus('<div class="status-box info fadein">⏳ İndirme başlatılıyor...</div>');

  try {
    const res = await fetch('/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality: selectedQuality })
    });
    const data = await res.json();

    if (data.job_id) {
      pollStatus(data.job_id);
    } else {
      setStatus('<div class="status-box error fadein">❌ ' + (data.error || 'Hata oluştu') + '</div>');
      setBtn('⬇ İNDİR', false);
    }
  } catch(e) {
    setStatus('<div class="status-box error fadein"> ❌ Sunucuya bağlanılamadı</div>');
    setBtn('⬇ İNDİR', false);
  }
}

function pollStatus(jobId) {
  if (polling) clearInterval(polling);

  polling = setInterval(async () => {
    try {
      const res = await fetch('/status/' + jobId);
      const data = await res.json();

      const pct = data.progress || 0;

      if (data.state === 'downloading') {
        setBtn('<span class="spinner">◌</span> İNDİRİLİYOR', true);
        setStatus(`
          <div class="progress-wrap fadein">
            <div class="progress-label">
              <span>İNDİRİLİYOR...</span>
              <span>${pct}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width:${pct}%"></div>
            </div>
          </div>
        `);
      } else if (data.state === 'done') {
        clearInterval(polling);
        setStatus('<div class="status-box success fadein">✅ İndirme tamamlandı!<br><small style="opacity:0.7">/sdcard/VidGrab/ klasörüne kaydedildi</small></div>');
        setBtn('⬇ YENİ İNDİR', false);
        document.getElementById('urlInput').value = '';
      } else if (data.state === 'error') {
        clearInterval(polling);
        setStatus('<div class="status-box error fadein">❌ ' + (data.error || 'İndirme başarısız') + '</div>');
        setBtn('⬇ İNDİR', false);
      }
    } catch(e) {}
  }, 1000);
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/start", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    quality = data.get("quality", "720")

    if not url:
        return jsonify({"error": "URL gerekli"}), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"state": "downloading", "progress": 0, "error": None}

    def run():
        try:
            if quality == "mp3":
                fmt = "bestaudio/best"
                extra = ["--extract-audio", "--audio-format", "mp3"]
            else:
                fmt = f"best[height<={quality}][ext=mp4]/best[height<={quality}]/best"
                extra = []

            output = os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")
            cmd = ["yt-dlp", "-f", fmt, "-o", output,
                   "--newline", "--no-playlist"] + extra + [url]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                line = line.strip()
                # İlerleme yüzdesini parse et
                if "[download]" in line and "%" in line:
                    try:
                        pct = float(line.split("%")[0].split()[-1])
                        jobs[job_id]["progress"] = round(pct)
                    except:
                        pass

            process.wait()

            if process.returncode == 0:
                jobs[job_id]["state"] = "done"
                jobs[job_id]["progress"] = 100
            else:
                jobs[job_id]["state"] = "error"
                jobs[job_id]["error"] = "yt-dlp hatası oluştu"

        except Exception as e:
            jobs[job_id]["state"] = "error"
            jobs[job_id]["error"] = str(e)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"state": "error", "error": "İş bulunamadı"}), 404
    return jsonify(job)

if __name__ == "__main__":
    print("\n" + "="*40)
    print("  VidGrab başlatıldı!")
    print("  Tarayıcıda aç: http://localhost:5000")
    print("="*40 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
