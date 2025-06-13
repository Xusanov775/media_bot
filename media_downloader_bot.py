import logging
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from tempfile import NamedTemporaryFile
from shazamio import Shazam
from pydub import AudioSegment

API_TOKEN = '7970865964:AAGtKAb2v_t2Yx5kLrp6xOhz_g8CdZ4f1ls'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@dp.message()
async def handle_message(message: types.Message):
    url = message.text.strip()

    if not re.match(r'https?://', url):
        await message.reply("Iltimos, Instagram, YouTube yoki TikTok linkini yuboring.")
        return

    # "Yuklanmoqda..." xabarini yuborib saqlaymiz
    loading_msg = await message.answer("⏳ Yuklanmoqda...")

    video_file, audio_preview = await download_video_and_extract_audio(url)
    if not audio_preview:
        await loading_msg.delete()
        await message.reply("Musiqa aniqlanmadi.")
        return

    song_name = await recognize_song(audio_preview)
    if not song_name:
        await loading_msg.delete()
        await message.reply("Musiqa nomini aniqlab bo‘lmadi.")
        return

    full_audio_file = await download_full_audio(song_name)

    # Yuklanmoqda xabarini o‘chiramiz
    await loading_msg.delete()

    if video_file:
        await message.answer_video(FSInputFile(video_file))
    if full_audio_file and os.path.exists(full_audio_file):
        await message.answer_audio(FSInputFile(full_audio_file), caption=f"🎵 Topilgan musiqa: {song_name}")
    else:
        await message.answer("Musiqa topilmadi.")

async def download_video_and_extract_audio(url):
    video_path = audio_path = None
    try:
        ydl_opts_video = {
            'format': 'mp4',
            'outtmpl': f'{DOWNLOAD_DIR}/video.%(ext)s',
            'noplaylist': True,
            'quiet': True
        }

        with YoutubeDL(ydl_opts_video) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            if not video_path.endswith('.mp4'):
                video_path = os.path.splitext(video_path)[0] + '.mp4'

        # Extract first 15 seconds audio from video
        audio_temp = os.path.join(DOWNLOAD_DIR, "preview.mp3")
        audio = AudioSegment.from_file(video_path)
        audio[:15000].export(audio_temp, format="mp3")
        audio_path = audio_temp

    except Exception as e:
        print(f"Xatolik: {e}")

    return video_path, audio_path

async def recognize_song(audio_path):
    try:
        shazam = Shazam()
        out = await shazam.recognize_song(audio_path)
        if out['track']:
            title = out['track']['title']
            subtitle = out['track']['subtitle']
            return f"{title} {subtitle}"
    except Exception as e:
        print(f"Musiqa aniqlashda xatolik: {e}")
    return None

async def download_full_audio(song_name):
    try:
        ydl_opts_audio = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/full_audio.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with YoutubeDL(ydl_opts_audio) as ydl:
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
            filename = ydl.prepare_filename(info['entries'][0])
            return os.path.splitext(filename)[0] + ".mp3"

    except Exception as e:
        print(f"To‘liq musiqa yuklashda xatolik: {e}")
        return None

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
