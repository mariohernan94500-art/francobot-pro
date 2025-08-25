# main.py - FrancoBot Pro en GitHub Codespaces
import os
import subprocess
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re

app = Flask(__name__)

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Directorios
AUDIO_DIR = "audio"
VIDEO_DIR = "videos"
LYRICS_DIR = "lyrics"
BACKGROUND_IMAGE = "background.jpg"

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(LYRICS_DIR, exist_ok=True)

def download_audio(song, artist):
    query = f"{artist} {song} official audio"
    output = f"{AUDIO_DIR}/{song.replace('/', '-')} - {artist.replace('/', '-')}.%(ext)s"
    cmd = [
        "yt-dlp",
        "-f", "bestaudio",
        "-x", "--audio-format", "mp3",
        "-o", output,
        f"ytsearch1:{query}"
    ]
    subprocess.run(cmd, check=True)
    return output.replace(".%(ext)s", ".mp3")

def extract_instrumental(audio_path):
    output = audio_path.replace(".mp3", "_instrumental.mp3")
    cmd = [
        "ffmpeg", "-i", audio_path,
        "-af", "highpass=f=150, lowpass=f=2000, volume=1.5",
        "-y", output
    ]
    subprocess.run(cmd, check=True)
    return output

def create_background():
    if not os.path.exists(BACKGROUND_IMAGE):
        cmd = [
            "ffmpeg", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=1",
            "-vf", "drawtext=text='FrancoBot Pro':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
            "-frames:v", "1", BACKGROUND_IMAGE
        ]
        subprocess.run(cmd, check=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎤 ¡Hola! Envíame: Haz 'canción' de artista")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("haz '"):
        try:
            parts = text.split("'")
            song = parts[1]
            artist = text.split("de")[1].strip()

            await update.message.reply_text(f"🎵 Descargando: {song} de {artist}...")
            audio_path = download_audio(song, artist)

            await update.message.reply_text("🎧 Extrayendo instrumental...")
            instrumental_path = extract_instrumental(audio_path)

            await update.message.reply_text("🎬 Creando video...")
            create_background()
            video_path = f"{VIDEO_DIR}/{song} - {artist}.mp4"
            cmd = [
                "ffmpeg", "-loop", "1", "-i", BACKGROUND_IMAGE,
                "-i", instrumental_path,
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p", "-shortest",
                "-y", video_path
            ]
            subprocess.run(cmd, check=True)

            await update.message.reply_text(f"✅ ¡Listo! Video creado: {video_path}")
            await update.message.reply_text("📁 Sube este video a Google Drive y Zapier lo subirá a YouTube.")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

@app.route('/')
def home():
    return "FrancoBot Pro está activo 🇫🇷🎶"

if __name__ == '__main__':
    # Iniciar bot
    from threading import Thread
    def run_bot():
        app_builder = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app_builder.add_handler(CommandHandler("start", start))
        app_builder.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app_builder.run_polling()
    
    Thread(target=run_bot, daemon=True).start()
    
    # Iniciar servidor
    app.run(host="0.0.0.0", port=5000)