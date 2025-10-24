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
    ("I Favor the Villainess", "A bold twist on isekai romance where love crosses all expectations."),
    ("Knight's Oath", "Duty and devotion give way to an honest, earned love."),
    ("The Lantern Bride", "Two lost souls find light together under moonlit vows."),
    ("Kaguya-sama: Love Is War", "Love is a battlefield where confessions mean defeat."),
    ("Horimiya", "Two high schoolers reveal hidden sides and fall in love."),
    ("Kimi ni Todoke", "A shy girl finds her voice and her heart."),
    ("Ao no Flag", "A coming-of-age triangle where love and identity collide."),
    ("Nana", "Two women, two dreams, one bittersweet destiny."),
    ("Your Throne", "A political power struggle between two women with fate intertwined."),
    ("Who Made Me a Princess", "A reincarnated girl must win the heart of her cold father, the emperor."),
    ("The Abandoned Empress", "A fallen noble girl vows to rise above fate and reclaim her worth."),
    ("Light and Shadow", "A maid’s secret marriage to a cold noble hides a deeper bond."),
    ("Beware the Villainess!", "A reincarnated heroine decides to flip the villainess script."),
    ("Suddenly Became a Princess One Day", "A new life, royal blood, and a dangerous father’s love."),
    ("The Reason Why Raeliana Ended Up at the Duke’s Mansion", "A woman reborn inside a novel changes her doomed story."),
    ("Death Is the Only Ending for the Villainess", "A player wakes up as the doomed villainess in her favorite game."),
    ("The Villainess Reverses the Hourglass", "A betrayed noble rewinds time for revenge and redemption."),
    ("The Duchess’ 50 Tea Recipes", "A modern woman introduces tea culture to a fantasy world."),
    ("I’m the Male Lead’s Girl Friend", "The wrong side of the love story never felt this right."),
    ("Doctor Elise: The Royal Lady with the Lamp", "A surgeon reincarnates as a disgraced noble and heals a kingdom."),
    ("Cheese in the Trap", "A realistic romance full of mind games and subtle emotions."),
    ("My Dear Cold-Blooded King", "A mysterious king and a girl’s fateful encounter under the stars."),
    ("Under the Oak Tree", "A shy lady and her knight rediscover love through war and distance."),
    ("My Next Life as a Villainess: All Routes Lead to Doom!", "A clueless noble girl tries to avoid every bad ending."),
    ("Crimson Karma", "A soldier reborn in a new world questions what she’s fighting for."),
    ("Sincerely: I Became a Duke’s Maid", "Love blooms between a loyal maid and a gentle noble."),
    ("I Belong to House Castielo", "A young girl in a powerful family finds warmth in cold hearts."),
    ("The Monster Duchess and Contract Princess", "A cursed duchess and a lost child heal each other."),
    ("A Stepmother’s Märchen", "A misunderstood stepmother’s love defies time and tragedy."),
    ("The Villainess Lives Twice", "Reborn with memories of betrayal, she plots a perfect revenge."),
    ("A Returner’s Magic Should Be Special", "A magician returns from ruin to rewrite the world’s fate."),
    ("Solo Leveling", "From weakest hunter to unstoppable hero — one man’s rebirth in power."),
    ("Remarried Empress", "A queen betrayed by her emperor finds freedom and a new love."),
    ("Lady Baby", "Reborn to change her family’s fate from childhood."),
    ("The Beginning After the End", "A reincarnated king starts anew in a magical world."),
    ("Tomb Raider King", "A man returns from death to reclaim stolen power."),
    ("Trash of the Count’s Family", "A lazy noble wakes up in a novel — and accidentally becomes a hero."),
    ("Lucia", "A princess who knows her tragic future makes a deal with a cold duke."),
    ("The Villainess Wants a Divorce", "A noble lady turns her failed marriage into liberation."),
    ("Wotakoi: Love Is Hard for Otaku", "Office romance between anime geeks — awkward, adorable, real."),
    ("Run Away With Me, Girl", "A tender yuri love story about rediscovering first love."),
    ("Yona of the Dawn", "A princess turned warrior travels to reclaim her kingdom and heart."),
    ("Tsubaki-chou Lonely Planet", "A girl working as a maid for an author finds unexpected comfort."),
    ("Fruits Basket", "A kind girl breaks a mysterious family curse through empathy."),
    ("Snow White with the Red Hair", "A herbalist’s pure heart wins a prince’s trust and love."),
    ("Orange", "A letter from the future guides a girl to save her friend from despair."),
    ("Say I Love You", "A lonely girl learns trust through an awkward, honest romance."),
    ("Toradora!", "A short boy and a fierce girl team up to win their crushes — and find love."),
    ("Nisekoi", "A fake relationship turns into something real."),
    ("Ao Haru Ride", "First love rekindled under new hearts and broken pasts."),
    ("Kamisama Kiss", "A homeless girl becomes a shrine goddess and meets a fox spirit."),
    ("ReLIFE", "A man relives high school for one more chance to fix his future."),
    ("Akatsuki no Yona", "Courage and love grow through fire and blood."),
    ("Skip and Loafer", "Country girl meets city boy in a charming coming-of-age romance."),
    ("Bloom Into You", "A delicate yuri romance about identity and first love."),
    ("My Dress-Up Darling", "Cosplay, connection, and a love stitched in fabric."),
    ("Honey and Clover", "A slow, poetic story of love, art, and growing up."),
    ("The Wolfman’s Romance", "An unlikely bond between predator and prey blooms softly."),
    ("Obey Me", "A girl caught between angels and demons learns what love really means."),
    ("The Villainess is a Marionette", "A puppet of fate cuts her own strings and rewrites destiny."),
    ("Beastars", "A carnivore and herbivore face instincts and affection in a divided world."),
    ("Spy x Family", "A spy, an assassin, and a telepath form a fake family — and real love."),
    ("Noragami", "A forgotten god and his mortal friend cross the line between worlds."),
    ("Re:Zero − Starting Life in Another World", "A man trapped in time finds love through endless trials."),
    ("That Time I Got Reincarnated as a Slime", "A reborn slime builds a new world of hope."),
    ("Jobless Reincarnation", "A failure reborn vows to live a life worth meaning."),
    ("The Villainess Turns the Hourglass", "A second chance turns tragedy into triumph."),
    ("Charlotte Has Five Disciples", "A powerful mage reborn into the chaos she once ended."),
    ("The Princess Imprints the Traitor", "A princess and her guard rewrite a tale of vengeance."),
    ("Father, I Don’t Want This Marriage!", "A rebellious daughter wins her father’s heart back."),
    ("I Tamed a Tyrant and Ran Away", "A captive turns her tyrant into her lover."),
    ("Seduce the Villain’s Father", "A heroine’s clever heart rewrites her cursed fate."),
    ("The Villainess is a Marionette", "A woman takes the strings of fate into her own hands."),
    ("Survive as the Hero’s Wife", "A modern woman navigates a deadly fantasy marriage."),
    ("The Tyrant’s Tranquilizer", "A gentle soul soothes a cursed emperor’s rage."),
    ("My In-Laws Are Obsessed with Me", "A woman wins the affection of the family that once hated her."),
    ("The Villainess’s Maker", "A mysterious man sculpts the perfect villainess — and falls for her."),
    ("A Villainess for the Tyrant", "The heart of a ruthless ruler softens in unlikely ways."),
    ("Beware of the Brothers!", "A girl reborn faces her overly protective brothers."),
    ("Villains Are Destined to Die", "A gamer wakes as the villainess in a dating sim full of danger."),
    ("Kill the Villainess", "A soul stuck in a doomed role searches for a way out."),
    ("The Way to Protect the Female Lead’s Older Brother", "A girl protects her family from their scripted deaths."),
    ("A Transmigrator’s Privilege", "Fate bends for those who dare to write their own story."),
    ("When the Villainess Loves", "The story’s villainess decides to chase love instead of revenge."),
    ("If You Touch My Little Brother, You’re All Dead", "Overprotective sister mode, but make it fantasy."),
    ("Flirting with the Villain’s Dad", "A reincarnated heroine wins over her father-in-law — literally."),
    ("Please Love the Useless Me", "A woman rebuilds her life through laughter and love."),
    ("Sweet Home", "Horror and heartbreak — humanity clings to hope in monsters."),
    ("Eleceed", "A kind boy and his superpowered cat change the world."),
    ("Omniscient Reader", "A reader becomes the hero of the story he once followed."),
    ("The Villainess’s Survival Diary", "A girl rewrites her own ending one chapter at a time."),
    ("The Dragon’s Bride", "A human and a dragon discover love beyond worlds."),
    ("The Runaway Lead Lives Next Door", "Escaping a novel’s fate never looked this romantic."),
    ("The Evil Lady’s Hero", "A villainess and her knight rewrite their destiny."),
    ("The Flower That Was Bloomed by a Cloud", "Beauty, power, and forbidden affection in the palace."),
    ("The Crown Princess Audition", "Romance and rivalry bloom behind royal masks."),
    ("This Girl is a Little Wild", "A female warrior must hide her past in a noble’s world."),
    ("Daughter of the Emperor", "A reborn girl melts her father’s icy heart."),
    ("The Way I Remember You", "A bittersweet romance that transcends lifetimes."),
    ("Crimson Heart", "Love and war clash in a world of blood and bloom."),
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
        "Thanks for watching \nSUBSCRIBE for more manga gems ",
        "Thanks for watching. SUBSCRIBE for more manga gems.",
        OUTPUT_DIR,
        "outro"
    ))

    create_tiktok_video(slides, FINAL_VIDEO_PATH)
    send_email_with_video(FINAL_VIDEO_PATH, title, selected)

if __name__ == "__main__":
    main()
