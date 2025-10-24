# main.py
import os
import random
import requests
import smtplib
from email.message import EmailMessage
from gtts import gTTS
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, AudioFileClip, ImageClip,
    CompositeVideoClip, concatenate_videoclips
)
import numpy as np

# --- Pillow 10+ compatibility fix ---
from PIL import Image as _PIL_Image
if not hasattr(_PIL_Image, "ANTIALIAS"):
    _PIL_Image.ANTIALIAS = _PIL_Image.LANCZOS

# ---------------- CONFIG (read from env for GitHub Actions) ----------------
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")                 # set as GitHub Secret
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")               # set as GitHub Secret
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")   # set as GitHub Secret
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", EMAIL_SENDER) # set as GitHub Secret or same as sender

# Local file names you will add to the repo root
CAT_GIF = "cat_talker.gif"       # optional; can be omitted
INTRO_IMAGE = "intro_image.jpg"  # you will upload
OUTRO_IMAGE = "outro_image.jpg"  # you will upload

# Output folder / file
OUTPUT_DIR = "output"
FINAL_VIDEO_PATH = os.path.join(OUTPUT_DIR, "tiktok_video.mp4")

# Styling
CAPTION_FONT_SIZE = int(os.getenv("CAPTION_FONT_SIZE", "100"))
TITLE_FONT_SIZE = int(os.getenv("TITLE_FONT_SIZE", "96"))
CAT_POSITION = ("center", 1300)
CAT_SIZE = int(os.getenv("CAT_SIZE", "380"))
NUM_RECOMMENDATIONS = int(os.getenv("NUM_RECOMMENDATIONS", "5"))

TIKTOK_TITLES = [
    "This manga ruined my sleep ;)",
    "Better than most anime tbh",
    "Why is no one talking about this??",
    "If you like villainess, READ THIS",
    "You’ll thank me later :)"
]

TAGS = "#manga #manhwa #anime #romanceanime #romancemanga #isekai #animeedit #otaku #mangarecommendation #trending"

# You can replace or extend this list
MANGA_LIST = [
    ("The Scent of Rain", "Thunderous feelings and the quiet after the storm create love."),
    ("The Paper Princess", "Fragile façade and the one who reads past it to the true heart."),
    ("I Favor the Villainess", "Queer romance where feelings grow in surprising places."),
    ("Knight's Oath", "Duty and devotion give way to an honest, earned love."),
    ("The Lantern Bride", "Light in the dark leads two lost souls into companionship."),
    ("Kaguya-sama: Love Is War", "A battle of wits where love means war."),
    ("Horimiya", "Two high schoolers reveal their hidden sides."),
    ("Kimi ni Todoke", "A shy girl learns to open her heart."),
    ("Ao no Flag", "A coming-of-age love triangle."),
    ("Nana", "Two women, two dreams, one heartbreak."),
]

# ---------------- HELPERS ----------------
def _load_font(size: int):
    # Try common fonts, fallback to default
    for fp in ("arialbd.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            pass
    return ImageFont.load_default()

def _wrap_text(text: str, font, max_width: int):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if font.getbbox(test)[2] - font.getbbox(test)[0] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines

def generate_tts(text: str, output_path: str, gremlin_pitch: float = 1.25):
    """
    gTTS -> (optional) pydub pitch effect requires ffmpeg.
    If ffmpeg isn't available, fall back to plain gTTS file.
    """
    try:
        tmp = output_path + ".tmp.mp3"
        gTTS(text=text, lang="en").save(tmp)

        # If pydub/ffmpeg is unavailable, just rename and return
        try:
            sound = AudioSegment.from_file(tmp, format="mp3")
            new_rate = int(sound.frame_rate * gremlin_pitch)
            pitched = sound._spawn(sound.raw_data, overrides={"frame_rate": new_rate})
            pitched = pitched.set_frame_rate(sound.frame_rate)
            pitched.export(output_path, format="mp3")
            os.remove(tmp)
        except Exception:
            os.replace(tmp, output_path)

        return True
    except Exception as e:
        print(f"[!] TTS error: {e}")
        return False

def search_manga_image(title: str):
    if not SERPAPI_KEY:
        return None
    try:
        r = requests.get("https://serpapi.com/search.json", params={
            "engine": "google",
            "q": f"{title} manga cover",
            "tbm": "isch",
            "api_key": SERPAPI_KEY,
            "num": 1
        }, timeout=30)
        r.raise_for_status()
        js = r.json()
        res = js.get("images_results", [])
        if res:
            return res[0].get("original")
    except Exception as e:
        print(f"[!] SerpAPI error: {e}")
    return None

def download_image(url: str, path: str):
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"[!] Download error: {e}")
        return False

def build_caption_clip(text: str, duration: float):
    font = _load_font(CAPTION_FONT_SIZE)
    W, H = 1080, 500
    lines = _wrap_text(text, font, W - 120)
    if len(lines) > 2:
        lines = lines[:2]
    lh = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    total_h = len(lines) * lh + (len(lines) - 1) * 10
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = (H - total_h) // 2
    for line in lines:
        w = font.getbbox(line)[2] - font.getbbox(line)[0]
        x = (W - w) // 2
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += lh + 10
    arr = np.array(img)
    return ImageClip(arr).set_duration(duration).set_position(("center", "center"))

# ---------- VIDEO CREATION ----------
def create_tiktok_video(slides, output_path):
    clips = []
    for s in slides:
        if not os.path.exists(s["img"]) or not os.path.exists(s["audio"]):
            continue

        audio = AudioFileClip(s["audio"])
        img = (ImageClip(s["img"])
               .set_duration(audio.duration)
               .resize(height=1920)
               .fadein(0.5)
               .fadeout(0.5))

        layers = [img]

        # Optional cat overlay
        if os.path.exists(CAT_GIF):
            try:
                cat = (VideoFileClip(CAT_GIF)
                       .resize(width=CAT_SIZE)
                       .loop(duration=audio.duration)
                       .set_position(CAT_POSITION)
                       .set_opacity(0.95))
                layers.append(cat)
            except Exception:
                pass

        caption_text = f"{s['title']}: {s['description']}".strip(": ").strip()
        if caption_text:
            caption = build_caption_clip(caption_text, audio.duration)
            layers.append(caption)

        comp = CompositeVideoClip(layers, size=(1080, 1920)).set_audio(audio)
        clips.append(comp)

    if clips:
        final = concatenate_videoclips(clips, method="compose")
        # lower bitrate in case email attachment gets big
        final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", bitrate="4M")
        print(f"[+] Video created: {output_path}")

# ---------- INTRO / OUTRO ----------
def _ensure_placeholder_if_missing(path: str):
    if not os.path.exists(path):
        Image.new("RGB", (1080, 1920), (20, 20, 25)).save(path)

def create_image_slide(image_path, text, tts_text, output_dir, name="intro"):
    _ensure_placeholder_if_missing(image_path)
    out_img = os.path.join(output_dir, f"{name}.jpg")
    out_audio = os.path.join(output_dir, f"{name}.mp3")

    base = Image.open(image_path).convert("RGBA")
    base = base.resize((1080, 1920), _PIL_Image.LANCZOS)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 120))
    draw = ImageDraw.Draw(overlay)
    font = _load_font(TITLE_FONT_SIZE)
    lines = _wrap_text(text, font, 900)
    lh = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    total_h = len(lines) * lh + 20
    y = (1920 - total_h) // 2
    for line in lines:
        w = font.getbbox(line)[2] - font.getbbox(line)[0]
        x = (1080 - w) // 2
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += lh + 10
    composed = Image.alpha_composite(base, overlay)
    composed.convert("RGB").save(out_img, quality=95)

    generate_tts(tts_text, out_audio)
    return {"img": out_img, "audio": out_audio, "title": "", "description": ""}

# ---------- EMAIL SENDER ----------
def send_email_with_video(video_path, title, mangas):
    if not (EMAIL_SENDER and EMAIL_APP_PASSWORD and EMAIL_RECEIVER):
        print("[!] Email creds missing; skipping email.")
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Manga Video Ready: {title}"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        body = f"{title}\n{TAGS}\n\n"
        for name, desc in mangas:
            body += f"{name}: {desc}\n"
        msg.set_content(body)

        if os.path.exists(video_path):
            with open(video_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="video", subtype="mp4",
                                   filename=os.path.basename(video_path))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print("[+] Email with video sent successfully.")
    except Exception as e:
        print(f"[!] Failed to send email: {e}")

# ---------- MAIN ----------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    slides = []

    title = random.choice(TIKTOK_TITLES)

    # Intro
    slides.append(create_image_slide(
        INTRO_IMAGE, title,
        f"Welcome manga lovers. {title}", OUTPUT_DIR, "intro"))

    # Manga slides
    selected = random.sample(MANGA_LIST, NUM_RECOMMENDATIONS)
    for i, (t, d) in enumerate(selected):
        print(f"[{i}] {t}")
        url = search_manga_image(t)
        if not url:
            continue
        img_path = os.path.join(OUTPUT_DIR, f"manga_{i}.jpg")
        audio_path = os.path.join(OUTPUT_DIR, f"tts_{i}.mp3")
        if not download_image(url, img_path):
            continue
        generate_tts(f"{t}. {d}", audio_path)
        slides.append({"img": img_path, "audio": audio_path, "title": t, "description": d})

    # Outro
    slides.append(create_image_slide(
        OUTRO_IMAGE,
        "💫 Thanks for watching 💫\nFollow for more manga gems ✨",
        "Thanks for watching. Follow for more manga gems.",
        OUTPUT_DIR,
        "outro"
    ))

    create_tiktok_video(slides, FINAL_VIDEO_PATH)
    send_email_with_video(FINAL_VIDEO_PATH, title, selected)

if __name__ == "__main__":
    main()
