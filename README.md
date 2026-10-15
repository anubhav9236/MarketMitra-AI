# 🤖 LocalBiz AI – Social Media Post Generator

> **Hacktoberfest Open-Source AI Challenge 2024**
> Generate professional promotional content for Instagram, Facebook, and WhatsApp using a **locally running AI** — no internet, no API key, no cloud, no cost.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-green?logo=flask)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-purple)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)
![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2024-orange)

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 📸 Promotional Caption | Platform-specific caption with emojis |
| 📝 Short Description | 2–3 sentence product description |
| 🏷️ Hashtags | 10–15 clickable, copyable hashtags |
| 📣 Call to Action | Punchy one-liner CTA |
| 💬 WhatsApp Message | Short, personalised message (<300 chars) |
| 🌐 Languages | English · Hindi · Hinglish |
| 📱 Platforms | Instagram · Facebook · WhatsApp |
| 🎭 Tones | Professional · Friendly · Promotional |
| 🧪 Demo Mode | Works without Ollama (sample output) |
| ⬇️ Download | Save content as a `.txt` file |
| 📋 Copy buttons | Per-section one-click copy |
| 🔒 100% Private | No data leaves your computer |

---

## 🗂️ Project Structure

```
LocalBiz-AI/
├── app.py               # Flask backend + Ollama integration
├── requirements.txt     # Python dependencies
├── render.yaml          # Render free demo deployment
├── .gitignore
├── README.md
├── templates/
│   └── index.html       # Main HTML page
└── static/
    ├── style.css        # Dark glassmorphism design
    └── script.js        # All front-end interactivity
```

---

## 🚀 Quick Start (Windows)

### Step 1 — Install Python

1. Go to <https://python.org/downloads/>
2. Download **Python 3.11** (or 3.9+)
3. ✅ During install, **tick "Add Python to PATH"**
4. Verify in Command Prompt:

```cmd
python --version
```

---

### Step 2 — Download the Project

**Option A – Git:**
```cmd
git clone https://github.com/your-username/LocalBiz-AI.git
cd LocalBiz-AI
```

**Option B – Manual:**
Download the ZIP from GitHub → Extract → Open the folder in Command Prompt:
```cmd
cd C:\Users\YourName\Downloads\LocalBiz-AI
```

---

### Step 3 — Create a Virtual Environment (Recommended)

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of your prompt.

---

### Step 4 — Install Python Dependencies

```cmd
pip install -r requirements.txt
```

This installs:
- **Flask** – web framework
- **requests** – HTTP calls to Ollama

---

### Step 5 — Install Ollama

1. Go to <https://ollama.com/download>
2. Download **Ollama for Windows**
3. Run the installer (it installs as a background service)
4. Verify:

```cmd
ollama --version
```

---

### Step 6 — Download an AI Model

Pull a lightweight Llama-family model:

```cmd
ollama pull llama3.2:3b
```

> **About storage:** `llama3.2:3b` is ~2 GB. You need at least 8 GB RAM.
> For lower-end PCs, try `ollama pull tinyllama` (640 MB, 4 GB RAM).

Check that your model is available:
```cmd
ollama list
```

---

### Step 7 — Start Ollama

Ollama usually starts automatically on Windows. If it doesn't:
```cmd
ollama serve
```

Leave this terminal open.

---

### Step 8 — Configure the Model (Optional)

The app defaults to `llama3.2:3b`. To use a different model, set an environment variable **before** starting Flask:

```cmd
set OLLAMA_MODEL=llama3.2:3b
```

Or for `tinyllama`:
```cmd
set OLLAMA_MODEL=tinyllama
```

---

### Step 9 — Start the Flask App

Open a **new** terminal (with `venv` activated):

```cmd
python app.py
```

You should see:
```
=======================================================
  🚀  LocalBiz AI – Social Media Post Generator
=======================================================
  Ollama Host  : http://localhost:11434
  Model        : llama3.2:3b
  App URL      : http://127.0.0.1:5000
  Demo Mode    : Available (no Ollama needed)
=======================================================
```

---

### Step 10 — Open the App

Open your browser and go to:

```
http://127.0.0.1:5000
```

---

## 🧪 Testing Every Feature

### Test 1 – Form Validation
1. Click **Generate with AI** without filling anything
2. ✅ Each required field should show a red error message

### Test 2 – Demo Mode (no Ollama needed)
1. Fill in all required fields with any text
2. Click **🧪 Demo Mode**
3. ✅ Results appear instantly with a yellow "Demo Output" badge
4. No AI or internet required

### Test 3 – Real AI Generation
1. Ensure Ollama is running (`ollama serve`)
2. Ensure your model is pulled (`ollama list`)
3. Fill the form → Click **✨ Generate with AI**
4. ✅ The green dot in the header means Ollama is connected
5. ✅ After 10–30 seconds, results appear

### Test 4 – Copy Buttons
1. Generate content (Demo Mode or real AI)
2. Click any **📋 Copy** button on a result card
3. ✅ Button turns green and shows "✅ Copied!"
4. Paste in Notepad to verify

### Test 5 – Hashtag Click-to-Copy
1. In the Hashtags card, click any individual hashtag pill
2. ✅ Toast notification confirms the copy

### Test 6 – Regenerate
1. Click **🔄 Regenerate** (top right of results)
2. ✅ New content is generated using the same form inputs

### Test 7 – Download
1. Generate content
2. Click **⬇️ Download**
3. ✅ A `.txt` file is saved to your Downloads folder
4. Open it — it contains all five content sections

### Test 8 – Hindi / Hinglish
1. Set Language to **Hindi** or **Hinglish**
2. Generate (Demo Mode works fine here too)
3. ✅ Hindi Devanagari text or Hinglish text appears correctly

### Test 9 – Ollama Offline Error
1. Stop Ollama (close the terminal running `ollama serve`)
2. Refresh the page
3. ✅ The red dot + "Ollama Not Detected" card appear with setup steps
4. Click **Use Demo Mode Instead** — still works

### Test 10 – All Platforms and Tones
- Switch between Instagram / Facebook / WhatsApp
- Switch between Professional / Friendly / Promotional
- ✅ Each generates slightly different content

---

## 🌍 Public Demo Deployment (Render)

The included `render.yaml` deploys a public demo using Render's free web service. On this deployment, `DEMO_MODE_ONLY=true` forces sample output and disables Ollama calls. The deployed service cannot access Ollama running on your personal computer; real AI generation remains available when running the app locally with Ollama.

1. Push this project to a **dedicated GitHub repository**. Do not push the parent `C:\Users\<YourName>` folder; it may contain unrelated personal files. Ensure `.venv/` stays excluded.
2. In Render, choose **New + → Blueprint**, connect that repository, and select its `render.yaml`.
3. Wait for the service deploy to finish. Render will provide a public `https://...onrender.com` URL.
4. Open the URL and try **Generate Demo**.

The demo is sample output, not AI-generated content. Set `DEMO_MODE_ONLY=false` only when deploying to a server where an Ollama instance is intentionally configured and reachable.

---

## ⚙️ Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OLLAMA_HOST`       | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL`      | `llama3.2:3b` | Model name (must be pulled) |
| `OLLAMA_TIMEOUT`    | `120` | Seconds before timeout |
| `DEMO_MODE_ONLY`    | `false` | Always serve sample output and never call Ollama when `true` |
| `SECRET_KEY`        | *(auto)* | Flask session secret |

Set them before running:
```cmd
set OLLAMA_MODEL=llama3.2:3b
python app.py
```

---

## 🌐 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET`  | `/`   | Main web UI |
| `GET`  | `/health` | Ollama status check (JSON) |
| `POST` | `/generate` | Generate content (JSON in/out) |
| `POST` | `/download` | Download content as `.txt` |

### `/generate` Request Body
```json
{
  "business_name":   "Sharma Store",
  "product_name":    "Homemade Pickle",
  "description":     "Traditional achaar made with mustard oil",
  "price":           "₹99 for 500g",
  "target_audience": "Housewives and food lovers",
  "platform":        "Instagram",
  "language":        "Hinglish",
  "tone":            "Friendly",
  "cta":             "DM to order",
  "demo_mode":       false
}
```

---

## 📤 Upload to GitHub

```cmd
git init
git add .
git commit -m "feat: LocalBiz AI - Social Media Post Generator"
git branch -M main
git remote add origin https://github.com/your-username/LocalBiz-AI.git
git push -u origin main
```

---

## 🤝 Contributing (Hacktoberfest)

1. Fork this repository
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Commit: `git commit -m "feat: describe your change"`
5. Push and open a Pull Request

**Good first issues:**
- Add more languages (Tamil, Telugu, Marathi, Bengali)
- Add more platforms (Twitter/X, LinkedIn)
- Add image prompt suggestion feature
- Improve Hindi prompt quality

---

## 🧠 How It Works

```
User fills form
      │
      ▼
Flask validates input
      │
      ▼
Build structured prompt (business details + language/tone instructions)
      │
      ▼
POST to Ollama /api/generate (local, no internet)
      │
      ▼
Parse JSON response (caption, hashtags, CTA, WhatsApp message)
      │
      ▼
Render in beautiful UI
```

---

## 📋 Compatible Models

| Model | Size | RAM | Quality |
|-------|------|-----|---------|
| `llama3.2:3b` | ~2 GB | 8 GB | ⭐⭐⭐⭐⭐ Recommended |
| `llama3.1` | ~4 GB | 8 GB | ⭐⭐⭐⭐⭐ |
| `mistral`  | ~4 GB | 8 GB | ⭐⭐⭐⭐ |
| `phi3`     | ~2 GB | 6 GB | ⭐⭐⭐⭐ |
| `tinyllama`| ~640 MB | 4 GB | ⭐⭐⭐ Budget |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [Ollama](https://ollama.com) – for making local AI easy
- [Meta Llama](https://ai.meta.com/llama/) – open-weight model
- [Flask](https://flask.palletsprojects.com) – lightweight Python web framework
- [Hacktoberfest](https://hacktoberfest.com) – for inspiring open-source contribution

---

*Built with ❤️ for small business owners across India*
