import os
import sys
import logging
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    print("On Railway: Add environment variable TELEGRAM_BOT_TOKEN")
    sys.exit(1)

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# ==================== BOT FUNCTIONS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    await update.message.reply_text(
        "🎵 KIRAK MP3 BOT\n\n"
        "Send YouTube link to download MP3!\n\n"
        "📞 @KIRAK_SML"
    )

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download audio from YouTube"""
    if update.message.text and update.message.text.startswith('/'):
        return
    
    url = update.message.text.strip() if update.message.text else ""
    
    if not url or ('youtube.com' not in url and 'youtu.be' not in url):
        await update.message.reply_text("⚠️ Please send a YouTube URL")
        return
    
    try:
        await update.message.reply_text("📥 Downloading...")
        
        # Create temp directory
        os.makedirs('/tmp/downloads', exist_ok=True)
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '/tmp/downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
        
        # Check if file exists
        if os.path.exists(file_path):
            await update.message.reply_text("✅ Sending MP3...")
            
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=update.message.chat_id,
                    audio=audio_file,
                    title=info.get('title', 'Audio')[:50],
                    performer=info.get('uploader', 'Unknown')[:30]
                )
            
            # Cleanup
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ Download failed!")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

# ==================== MAIN FUNCTION ====================
def main():
    """Main function to run the bot"""
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))
    
    # Start bot
    logger.info("🤖 Bot is starting...")
    print("✅ Bot is running on Railway!")
    
    application.run_polling(
        drop_pending_updates=True,
        timeout=30,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30
    )

# ==================== ENTRY POINT ====================
if __name__ == '__main__':
    main()
