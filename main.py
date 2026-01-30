import os
import sys
import logging
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Check FFmpeg
def check_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("✅ FFmpeg is available")
            return True
        else:
            logging.error("❌ FFmpeg not working")
            return False
    except Exception as e:
        logging.error(f"❌ FFmpeg check failed: {e}")
        return False

# Simple MP3 download without FFmpeg post-processing
async def download_audio_simple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url or ('youtube.com' not in url and 'youtu.be' not in url):
        await update.message.reply_text("⚠️ សូមផ្ញើតំណ YouTube")
        return
    
    try:
        # Send initial message
        await update.message.reply_text("📥 កំពុងទាញយក...")
        
        # Use yt-dlp to get direct audio URL
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            # Get video info
            info = ydl.extract_info(url, download=False)
            
            # Send audio directly (no conversion)
            await update.message.reply_text(f"🎵 បានទាញយក: {info.get('title', 'Audio')}")
            
            # Try to send audio file
            try:
                # Download to temp file
                temp_file = f"/tmp/{info['id']}.m4a"
                ydl_opts_download = {
                    'format': 'bestaudio[ext=m4a]',
                    'outtmpl': temp_file,
                    'quiet': True,
                }
                
                with YoutubeDL(ydl_opts_download) as ydl2:
                    ydl2.extract_info(url, download=True)
                
                # Send as audio (Telegram supports m4a)
                with open(temp_file, 'rb') as audio_file:
                    await context.bot.send_audio(
                        chat_id=update.message.chat_id,
                        audio=audio_file,
                        title=info.get('title', 'Audio')[:50],
                        performer=info.get('uploader', 'Unknown')[:30]
                    )
                
                # Cleanup
                os.remove(temp_file)
                
            except Exception as e:
                logging.error(f"Send error: {e}")
                await update.message.reply_text(f"❌ មិនអាចផ្ញើឯកសារ: {str(e)[:100]}")
        
    except Exception as e:
        logging.error(f"Download error: {e}")
        await update.message.reply_text(f"❌ កំហុស: {str(e)[:100]}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 KIRAK MP3 BOT\n\n"
        "Send YouTube link to download audio\n\n"
        "📞 @KIRAK_SML"
    )

def main():
    if not TOKEN:
        logging.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    # Check system
    has_ffmpeg = check_ffmpeg()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio_simple))
    
    logging.info(f"🤖 Bot starting (FFmpeg: {'✅' if has_ffmpeg else '❌'})")
    app.run_polling()

if __name__ == '__main__':
    main(            with open(mp3_file_path, 'rb') as audio:
                await context.bot.send_audio(
                    chat_id=chat_id, 
                    audio=audio,
                    title=info_dict.get('title', 'Audio')[:64],
                    performer=info_dict.get('uploader', 'Unknown')[:64]
                )

            # Clean up the MP3 file
            if os.path.exists(mp3_file_path):
                os.remove(mp3_file_path)

        except Exception as e:
            logging.error(f"Error: {str(e)}")
            await update.message.reply_text("❌ មានកំហុស! សូមព្យាយាមម្តងទៀត")

    elif user_message:
        await update.message.reply_text(
            "⚠️ សូមផ្ញើតំណ YouTube\n\n"
            "ឧទាហរណ៍:\n"
            "• https://youtu.be/xxxx\n"
            "• https://youtube.com/watch?v=xxxx"
        )

def main() -> None:
    if not TOKEN:
        print("❌ ERROR: Add TELEGRAM_BOT_TOKEN to .env file")
        return
    
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    print("🤖 Bot starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
