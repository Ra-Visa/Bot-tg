import os
import sys
import logging
import subprocess
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    print("1. On Railway: Settings → Variables → Add TELEGRAM_BOT_TOKEN")
    print("2. On Render: Environment → Add TELEGRAM_BOT_TOKEN")
    sys.exit(1)

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

# ==================== CHECK SYSTEM ====================
def check_system():
    """Check if system has required tools"""
    print("🔧 Checking system...")
    
    # Check Python version
    print(f"🐍 Python: {sys.version[:20]}")
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if 'ffmpeg version' in result.stdout:
            print("✅ FFmpeg: Installed")
            return True
        else:
            print("❌ FFmpeg: Not found")
            return False
    except:
        print("❌ FFmpeg: Not installed")
        return False

# ==================== BOT FUNCTIONS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    await update.message.reply_text(
        f"🎵 <b>KIRAK MP3 BOT</b>\n\n"
        f"Hello {user.first_name}! 👋\n\n"
        f"<b>How to use:</b>\n"
        f"1. Send any YouTube URL\n"
        f"2. Wait for download\n"
        f"3. Receive MP3 file\n\n"
        f"<b>Supported:</b>\n"
        f"• YouTube videos\n"
        f"• YouTube Shorts\n"
        f"• YouTube Music\n\n"
        f"<b>Help:</b> @KIRAK_SML",
        parse_mode='HTML'
    )

async def download_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download YouTube video as MP3"""
    if not update.message or not update.message.text:
        return
    
    url = update.message.text.strip()
    chat_id = update.message.chat_id
    
    # Validate URL
    if not url or ('youtube.com' not in url and 'youtu.be' not in url):
        await update.message.reply_text(
            "⚠️ <b>Please send a valid YouTube URL</b>\n\n"
            "Examples:\n"
            "• https://youtu.be/dQw4w9WgXcQ\n"
            "• https://www.youtube.com/watch?v=xxxx",
            parse_mode='HTML'
        )
        return
    
    try:
        # Step 1: Send initial message
        status_msg = await update.message.reply_text(
            "🔍 <b>Checking URL...</b>\n"
            "⏳ Please wait...",
            parse_mode='HTML'
        )
        
        # Step 2: Create temp directory
        temp_dir = tempfile.mkdtemp(prefix="yt_download_")
        logger.info(f"Temp dir: {temp_dir}")
        
        # Step 3: Configure yt-dlp with WORKING settings
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',  # 192kbps is reliable
                },
                {
                    'key': 'FFmpegMetadata',  # Add metadata
                }
            ],
            'writethumbnail': True,  # Download thumbnail
            'postprocessor_args': {
                'ffmpeg': [
                    '-i', '%(thumbnails.-1.filepath)s',  # Add thumbnail to audio
                    '-map', '0',
                    '-map', '1',
                    '-c', 'copy',
                    '-disposition:v', 'attached_pic'
                ]
            },
            'quiet': False,  # Show logs for debugging
            'no_warnings': False,
            'extract_flat': False,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'ignoreerrors': False,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],  # Skip problematic formats
                    'player_client': ['android', 'web']
                }
            },
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'cookiefile': None,
            'nocheckcertificate': True,
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'noplaylist': True,
            'logger': logger,
        }
        
        # Step 4: Get video info first
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text="📥 <b>Getting video info...</b>",
            parse_mode='HTML'
        )
        
        with YoutubeDL(ydl_opts) as ydl:
            try:
                # Get info without downloading first
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                
                # Check duration (limit to 30 minutes for free tier)
                if duration > 1800:  # 30 minutes
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                        text=f"⚠️ <b>Video too long</b>\n"
                             f"Duration: {duration//60} minutes\n"
                             f"Max: 30 minutes (free tier limit)",
                        parse_mode='HTML'
                    )
                    return
                
                # Step 5: Download with progress updates
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text=f"🎵 <b>{video_title[:40]}...</b>\n"
                         f"📥 Downloading audio...",
                    parse_mode='HTML'
                )
                
                # Actually download
                info = ydl.extract_info(url, download=True)
                
                # Find the downloaded MP3 file
                downloaded_files = list(Path(temp_dir).glob("*.mp3"))
                if not downloaded_files:
                    # Try to find any audio file
                    downloaded_files = list(Path(temp_dir).glob("*.*"))
                
                if downloaded_files:
                    mp3_file = downloaded_files[0]
                    file_size = mp3_file.stat().st_size
                    
                    if file_size < 1024:  # Less than 1KB = failed
                        raise Exception("Downloaded file is too small")
                    
                    # Step 6: Send progress update
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                        text=f"✅ <b>Download complete!</b>\n"
                             f"📦 Size: {file_size//1024} KB\n"
                             f"📤 Sending MP3...",
                        parse_mode='HTML'
                    )
                    
                    # Step 7: Send the MP3 file
                    with open(mp3_file, 'rb') as audio_file:
                        await context.bot.send_audio(
                            chat_id=chat_id,
                            audio=audio_file,
                            title=video_title[:64],
                            performer=info.get('uploader', 'Unknown')[:32],
                            duration=duration,
                            caption=f"🎵 {video_title}\n⬇️ via @KIRAK_MP3_Bot",
                            parse_mode='HTML'
                        )
                    
                    # Step 8: Success message
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                        text=f"✅ <b>Successfully sent!</b>\n"
                             f"🎵 {video_title[:50]}...\n"
                             f"👤 Enjoy your music!",
                        parse_mode='HTML'
                    )
                    
                    logger.info(f"Success: {video_title} ({file_size} bytes)")
                    
                else:
                    raise Exception("No audio file found after download")
                
            except Exception as e:
                logger.error(f"Download error: {str(e)}")
                raise e
            
            finally:
                # Cleanup temp directory
                import shutil
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        
        # User-friendly error messages
        error_msg = str(e).lower()
        
        if 'private' in error_msg:
            user_error = "🔒 This video is private or requires login"
        elif 'unavailable' in error_msg:
            user_error = "❌ Video is unavailable or deleted"
        elif 'copyright' in error_msg:
            user_error = "⚠️ Copyright restrictions"
        elif 'members only' in error_msg:
            user_error = "👥 Members-only video"
        elif 'age restricted' in error_msg:
            user_error = "🔞 Age-restricted (requires login)"
        elif 'too long' in error_msg:
            user_error = "⏱️ Video too long (max 30 minutes)"
        elif 'ffmpeg' in error_msg:
            user_error = "🔄 FFmpeg error. Platform may not support audio conversion"
        elif 'sign in' in error_msg or 'login' in error_msg:
            user_error = "🔐 Video requires YouTube login"
        else:
            user_error = f"❌ Error: {str(e)[:80]}"
        
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id if 'status_msg' in locals() else None,
                text=f"{user_error}\n\nTry another video or shorter video.",
                parse_mode='HTML'
            )
        except:
            await update.message.reply_text(user_error)

# ==================== MAIN FUNCTION ====================
def main():
    """Main function"""
    print("=" * 50)
    print("🚀 Starting KIRAK MP3 BOT")
    print("=" * 50)
    
    # Check system
    has_ffmpeg = check_system()
    
    if not has_ffmpeg:
        print("⚠️ WARNING: FFmpeg not found. Some videos may not work.")
        print("On Railway/Render, FFmpeg should be auto-installed.")
    
    # Create bot application
    try:
        application = ApplicationBuilder() \
            .token(TOKEN) \
            .read_timeout(30) \
            .write_timeout(30) \
            .connect_timeout(30) \
            .pool_timeout(30) \
            .build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_mp3))
        
        # Start bot
        print("🤖 Bot is starting...")
        print("✅ Ready! Send /start in Telegram")
        print("=" * 50)
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            timeout=30,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30
        )
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        print(f"❌ Bot failed: {e}")
        print("🔄 Restarting in 10 seconds...")
        import time
        time.sleep(10)
        main()  # Restart

# ==================== ENTRY POINT ====================
if __name__ == '__main__':
    main()            with open(mp3_file_path, 'rb') as audio:
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
