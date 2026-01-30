import subprocess
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# Ensure yt-dlp is always updated
subprocess.run(["pip", "install", "--upgrade", "yt-dlp"], check=True)

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

DOWNLOAD_FOLDER = './'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # សារ welcome តាមភាសាខ្មែរ
    welcome_message = """
<b>𝗞𝗜𝗥𝗔𝗞 𝗗𝗢𝗪𝗡𝗟𝗢𝗔𝗗 𝗠𝗣𝟯 - 𝗕𝗢𝗧</b>

សួស្តី! ជម្រាបសួរមកកាន់ KIRAK Download MP3 Bot

📥 <b>របៀបប្រើប្រាស់:</b>
គ្រាន់តែផ្ញើតំណ YouTube មកខ្ញុំ

🌐 <b>គាំទ្រ:</b> YouTube, YouTube Shorts, YouTube Music
🎧 <b>គុណភាព:</b> MP3 320kbps

📞 <b>សម្រាប់ជំនួយ:</b> @kirak_itadori
"""
    
    # សាកផ្ញើសារមុន
    await update.message.reply_text("🟢")
    
    # URL រូបភាព
    photo_url = "https://i.ibb.co/dJ6c0ctk/IMG-20260130-081334-718.jpg"
    
    try:
        # ផ្ញើរូបភាព
        await context.bot.send_photo(
            chat_id=update.message.chat_id,
            photo=photo_url,
            caption=welcome_message,
            parse_mode='HTML'
        )
        logging.info("✅ Welcome photo sent successfully")
        
    except Exception as e:
        logging.error(f"❌ Error sending photo: {str(e)[:100]}")
        
        # សាកជំនួស URL ថ្មី
        try:
            # ប្រើ URL រូបភាពពី Telegram servers
            alternative_url = "https://i.ibb.co/dJ6c0ctk/IMG-20260130-081334-718.jpg"
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=alternative_url,
                caption=welcome_message,
                parse_mode='HTML'
            )
            logging.info("✅ Alternative photo sent successfully")
        except:
            # បើមិនអាចផ្ញើរូបភាពទេ ផ្ញើតែសារ
            await update.message.reply_text(welcome_message, parse_mode='HTML')
            logging.info("✅ Text-only welcome sent")

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ប្រសិនបើគេបញ្ជូន command កុំឲ្យដំណើរការ download
    if update.message.text and update.message.text.startswith('/'):
        return
    
    chat_id = update.message.chat_id
    user_message = update.message.text.strip() if update.message.text else ""

    if user_message and ('youtube.com' in user_message or 'youtu.be' in user_message):
        try:
            youtube_url = user_message
            
            # ផ្ញើសារប្រាប់អ្នកប្រើ
            await update.message.reply_text("📥 កំពុងទាញយក... សូមរង់ចាំសិន!")
            
            # Download the audio using yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'noplaylist': True,
                'quiet': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                audio_file = ydl.prepare_filename(info_dict)
                mp3_file_path = audio_file.rsplit('.', 1)[0] + '.mp3'

            # ផ្ញើសារប្រាប់ថាទាញយករួច
            await update.message.reply_text("✅ ទាញយករួច! កំពុងផ្ញើ MP3...")
            
            # Send the MP3 file to the user
            with open(mp3_file_path, 'rb') as audio:
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