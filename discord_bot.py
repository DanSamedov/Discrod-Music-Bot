import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp
from collections import deque
import asyncio

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
audio_path = os.getenv('AUDIO_PATH')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)

songs_queue = deque()


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def oleg_joins():
    pass


@bot.command()
async def play(ctx, arg):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        voice = ctx.guild.voice_client

        if voice is None:
            voice = await channel.connect()
            await ctx.send(f"Joined {channel}")
        
        if voice.is_playing():
            queue_song(arg)
            await ctx.send(f"Added to queue: {arg}")
        else:
            queue_song(arg)
            await play_next(ctx)
    else:
        await ctx.send("You need to be in a voice channel to use this command.")


@bot.command()
async def pause(ctx):
    voice = ctx.guild.voice_client
    
    if voice.is_paused():
        voice.resume()
        await ctx.send("Audio is resumed.")
    else:
        voice.pause()
        await ctx.send("Audio is paused.")


@bot.command()
async def stfu(ctx):
    if ctx.voice_client is not None:
        songs_queue.clear()
        await ctx.send(f"Bot has left the voice channel: {ctx.voice_client.channel}")
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("Bot is not in a voice channel.")


@bot.command()
async def loop(ctx, arg):
    pass


@bot.command()
async def outro(ctx, arg):
    pass


def queue_song(arg):
    global songs_queue
    songs_queue.append(arg)


@bot.command()
async def print_queue(ctx):
    queue_list = list(songs_queue)
    await ctx.send(f"List of songs: {queue_list}")


async def play_next(ctx):
    if songs_queue:
        next_song = songs_queue.popleft()
        await play_audio(ctx, next_song)


@bot.command()
async def skip(ctx):
    pass


@bot.command()
async def clear(ctx):
    pass


@bot.command()
async def play_audio(ctx, arg):
    try:
        await download_with_yt_dlp(arg)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

    if os.path.exists(audio_path):
        source = discord.FFmpegPCMAudio(executable="ffmpeg", source=audio_path)

        def after_playing(error):
            coro = play_next(ctx)
            asyncio.run_coroutine_threadsafe(coro, bot.loop)

        ctx.guild.voice_client.play(source, after=after_playing)
    else:
        await ctx.send("Error: Audio file not found.")


async def download_with_yt_dlp(url):
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.splitext(audio_path)[0],
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


bot.run(bot_token)