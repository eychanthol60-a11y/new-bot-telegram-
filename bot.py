# Save as: bot.py
import os
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# === YOUR BOT TOKEN (GET FROM @BotFather) ===
TOKEN = "8243930858:AAFp9-15UphKEZMj1pNXKrpcqCo2fM0ZBFwj"  # ← CHANGE THIS!

# Folder to save videos
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

# Best settings for TikTok + all platforms (no watermark)
ydl_opts = {
    'format': 'best[height<=720]/best',        # Max 720p to stay under 50MB
    'merge_output_format': 'mp4',
    'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'retries': 10,
    'fragment_retries': 10,
    # TikTok no watermark
    'cookiefile': 'cookies.txt',  # optional: put your cookies.txt here for private videos
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "TikTok Downloader Bot\n\n"
        "Just paste any link:\n"
        "• TikTok\n"
        "• YouTube\n"
        "• Instagram Reels\n"
        "• Facebook\n"
        "• Twitter / X\n\n"
        "I will send you the video without watermark!\n"
        "Powered by yt-dlp"
    )

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("Please send a valid link")
        return

    status_msg = await update.message.reply_text("Downloading video...")

    try:
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info['id']
            title = info.get('title', 'video')[:100]

        # Find downloaded file
        video_file = None
        for file in Path(DOWNLOAD_DIR).glob(f"{video_id}.*"):
            if file.suffix in ['.mp4', '.mkv', '.webm']:
                video_file = file
                break

        if not video_file:
            await status_msg.edit_text("Error: Video not found after download")
            return

        file_size = video_file.stat().st_size
        if file_size > 50 * 1024 * 1024:  # > 50 MB
            await status_msg.edit_text("Video > 50MB, sending as document...")
            await update.message.reply_document(
                document=open(video_file, 'rb'),
                caption=f"{title}\n@YourChannel",
                filename=f"{title}.mp4"
            )
        else:
            await update.message.reply_video(
                video=open(video_file, 'rb'),
                caption=f"{title}\n@YourChannel",
                supports_streaming=True
            )

        # Clean up
        video_file.unlink()
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"Failed: {str(e)[:100]}")
        logging.error(e)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_and_send))

    print("Bot is running... Press Ctrl+C to stop")
    app.run_polling()

if __name__ == '__main__':
    main()