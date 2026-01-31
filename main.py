import subprocess
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL
import asyncio
import threading
from flask import Flask, request
import time

# Web server for Replit 24/7
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 KIRAK MP3 Download Bot is running!"

@app.route('/health')
def health():
    return "✅ Bot is healthy", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Start Flask server in a separate thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# Ensure yt-dlp is always updated
subprocess.run(["pip", "install", "--upgrade", "yt-dlp"], check=True)

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

DOWNLOAD_FOLDER = './downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Clean old files on startup
for file in os.listdir(DOWNLOAD_FOLDER):
    file_path = os.path.join(DOWNLOAD_FOLDER, file)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error removing {file_path}: {e}")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = """
<b>𝗞𝗜𝗥𝗔𝗞 𝗗𝗢𝗪𝗡𝗟𝗢𝗔𝗗 𝗠𝗣𝟯 - 𝗕𝗢𝗧</b>

សួស្តី! ជម្រាបសួរមកកាន់ KIRAK Download MP3 Bot

📥 <b>របៀបប្រើប្រាស់:</b>
គ្រាន់តែផ្ញើតំណ YouTube មកខ្ញុំ

🌐 <b>គាំទ្រ:</b> YouTube, YouTube Shorts, YouTube Music
🎧 <b>គុណភាព:</b> MP3 320kbps

📞 <b>សម្រាប់ជំនួយ:</b> @kirak_itadori

🚀 <b>Bot Status:</b> Online 24/7
"""
    
    await update.message.reply_text("🟢")
    
    photo_url = "https://i.ibb.co/dJ6c0ctk/IMG-20260130-081334-718.jpg"
    
    try:
        await context.bot.send_photo(
            chat_id=update.message.chat_id,
            photo=photo_url,
            caption=welcome_message,
            parse_mode='HTML'
        )
        logger.info("✅ Welcome photo sent successfully")
        
    except Exception as e:
        logger.error(f"❌ Error sending photo: {str(e)[:100]}")
        try:
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo="https://i.ibb.co/dJ6c0ctk/IMG-20260130-081334-718.jpg",
                caption=welcome_message,
                parse_mode='HTML'
            )
            logger.info("✅ Alternative photo sent successfully")
        except:
            await update.message.reply_text(welcome_message, parse_mode='HTML')
            logger.info("✅ Text-only welcome sent")

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text and update.message.text.startswith('/'):
        return
    
    chat_id = update.message.chat_id
    user_message = update.message.text.strip() if update.message.text else ""

    if user_message and ('youtube.com' in user_message or 'youtu.be' in user_message):
        try:
            youtube_url = user_message
            
            # Show downloading status
            status_msg = await update.message.reply_text("📥 កំពុងទាញយក... សូមរង់ចាំសិន! (នេះអាចមានពេល 1-2 នាទី)")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title).50s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'noplaylist': True,
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                audio_file = ydl.prepare_filename(info_dict)
                mp3_file_path = audio_file.rsplit('.', 1)[0] + '.mp3'

            await status_msg.edit_text("✅ ទាញយករួច! កំពុងផ្ញើ MP3...")
            
            # Get video title and uploader
            title = info_dict.get('title', 'Audio')[:64]
            uploader = info_dict.get('uploader', 'Unknown')[:64]
            
            # Send the MP3 file
            with open(mp3_file_path, 'rb') as audio:
                await context.bot.send_audio(
                    chat_id=chat_id, 
                    audio=audio,
                    title=title,
                    performer=uploader,
                    caption=f"🎵 {title}\n👤 {uploader}\n\nបានទាញយកដោយ KIRAK MP3 Bot"
                )

            # Clean up
            if os.path.exists(mp3_file_path):
                os.remove(mp3_file_path)
            
            logger.info(f"✅ Successfully downloaded and sent: {title}")

        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            await update.message.reply_text(f"❌ មានកំហុស:\n{str(e)[:200]}\n\nសូមព្យាយាមម្តងទៀត ឬផ្ញើតំណផ្សេង")

    elif user_message:
        await update.message.reply_text(
            "⚠️ សូមផ្ញើតំណ YouTube ត្រឹមត្រូវ\n\n"
            "ឧទាហរណ៍:\n"
            "• https://youtu.be/xxxx\n"
            "• https://youtube.com/watch?v=xxxx\n"
            "• https://www.youtube.com/shorts/xxxx"
        )

async def keep_alive():
    """Keep the bot alive by sending periodic logs"""
    while True:
        logger.info("🤖 Bot is still running...")
        await asyncio.sleep(3600)  # Log every hour

def main() -> None:
    if not TOKEN:
        print("❌ ERROR: Add TELEGRAM_BOT_TOKEN to .env file")
        print("📝 Create .env file with: TELEGRAM_BOT_TOKEN=your_token_here")
        return
    
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))
    
    # Add help command
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📚 **ជំនួយ**:\n\n"
            "1. ផ្ញើតំណ YouTube មកខ្ញុំ\n"
            "2. ខ្ញុំនឹងបម្លែងវាទៅជា MP3\n"
            "3. ទាញយកភ្លាមៗ!\n\n"
            "បញ្ហាបច្ចេកទេស? @kirak_itadori",
            parse_mode='Markdown'
        )
    
    application.add_handler(CommandHandler("help", help_command))

    print("=" * 50)
    print("🤖 KIRAK MP3 Download Bot Starting...")
    print(f"📁 Download folder: {DOWNLOAD_FOLDER}")
    print(f"🌐 Flask server running on port 8080")
    print("=" * 50)
    
    # Start keep-alive task
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())
    
    # Start the bot
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()
