import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp
from collections import deque
import asyncio

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')

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
    ctx.guild.voice_client.stop()
    ctx.send("Done! Playing next song")
    play_next(ctx)


@bot.command()
async def clear(ctx):
    ctx.guild.voice_client.stop()
    ctx.send("Queue is cleared")


@bot.command()
async def play_audio(ctx, arg):
    try:
        stream_url = await get_stream_url(arg)
        if stream_url:
            source = discord.FFmpegPCMAudio(stream_url)
            
            def after_playing(error):
                coro = play_next(ctx)
                asyncio.run_coroutine_threadsafe(coro, bot.loop)
            
            ctx.guild.voice_client.play(source, after=after_playing)
            await ctx.send(f"Now playing: {arg}")
        
        else:
            await ctx.send("Could not retrieve audio stream.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


async def get_stream_url(url):
    try:
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"ytsearch:{url}"
        
        ydl_opts = {'format': 'bestaudio'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info['url']
        return stream_url
    except Exception as e:
        print(f"Error getting stream URL: {e}")
        return None


bot.run(bot_token)