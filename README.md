# TikTok Manga Video (Auto, Daily, Emailed)

This project generates a vertical TikTok-style video with:
- big captions,
- optional talking cat GIF,
- intro/outro with your images,
- gremlin-pitched TTS,
- automatic email delivery with the video attached.

## 1) Add your assets
Place these files in the repo root:
- `intro_image.jpg` (required)
- `outro_image.jpg` (required)
- `cat_talker.gif` (optional)

If any image is missing, a simple placeholder will be generated so it never crashes.

## 2) Set secrets in GitHub
Repo → Settings → Secrets and variables → Actions → New repository secret:
- `SERPAPI_KEY`
- `EMAIL_SENDER`
- `EMAIL_APP_PASSWORD`
- `EMAIL_RECEIVER`

## 3) Run locally (optional)
```bash
pip install -r requirements.txt
python main.py
