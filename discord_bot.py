import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp
from collections import deque
import asyncio
import logging

# Load environment variables
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
my_user_id = int(os.getenv('MY_USER_ID'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

songs_queue = deque()
looping_song = None


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")


@bot.event
async def on_voice_state_update(member, before, after):
    """Plays a song when a specific user joins a voice channel."""
    if member.id == my_user_id and after.channel is not None and before.channel != after.channel:
        channel = after.channel
        voice = member.guild.voice_client

        if voice is None:
            voice = await channel.connect()
        elif voice.channel != channel:
            await voice.move_to(channel)

        stream_url, song_title = await get_stream_url("https://www.youtube.com/watch?v=3_-a9nVZYjk&ab_channel=TrapNation")

        if stream_url:
            source = discord.FFmpegPCMAudio(stream_url, options="-vn")

            if voice.is_playing():
                voice.stop()

            voice.play(source)


@bot.command()
async def play(ctx, *, query):
    """Plays a song from YouTube."""
    if not ctx.author.voice:
        return await ctx.send("You need to be in a voice channel to use this command.")
    
    voice = ctx.guild.voice_client or await ctx.author.voice.channel.connect()
    stream_url, song_title = await get_stream_url(query)
    
    if stream_url:
        songs_queue.append((stream_url, song_title))
        if not voice.is_playing():
            await play_next(ctx)
        else:
            await ctx.send(f"Added to queue: `{song_title}`")
    else:
        await ctx.send("Could not retrieve audio stream.")


@bot.command()
async def pause(ctx):
    """Pauses the current song."""
    voice = ctx.guild.voice_client
    if voice and voice.is_playing():
        voice.pause()
        await ctx.send("⏸️ Paused the song.")
    else:
        await ctx.send("❌ No song is currently playing.")


@bot.command()
async def resume(ctx):
    """Resumes the paused song."""
    voice = ctx.guild.voice_client
    if voice and voice.is_paused():
        voice.resume()
        await ctx.send("▶️ Resumed the song.")
    else:
        await ctx.send("❌ No song is currently paused.")


@bot.command()
async def skip(ctx):
    """Skips the current song."""
    voice = ctx.guild.voice_client
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("Skipping current song...")
        await play_next(ctx)
    else:
        await ctx.send("Nothing is playing.")


@bot.command()
async def loop(ctx, *, query):
    """Loops a song indefinitely."""
    global looping_song
    if not ctx.author.voice:
        return await ctx.send("You need to be in a voice channel to use this command.")
    
    looping_song = query
    await ctx.send(f"Looping `{query}`")
    
    if not ctx.guild.voice_client or not ctx.guild.voice_client.is_playing():
        await play_audio(ctx, query)


@bot.command()
async def stoploop(ctx):
    """Stops the looping song."""
    global looping_song
    looping_song = None
    await ctx.send("Looping stopped.")


@bot.command()
async def queue(ctx):
    """Displays the song queue."""
    if songs_queue:
        queue_list = [title for _, title in songs_queue]
        await ctx.send(f"Queue: `{', '.join(queue_list)}`")
    else:
        await ctx.send("Queue is empty.")


@bot.command()
async def clear(ctx):
    """Clears the queue."""
    songs_queue.clear()
    await ctx.send("Queue cleared.")


@bot.command()
async def leave(ctx):
    """Disconnects the bot from the voice channel."""
    if ctx.voice_client:
        songs_queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("Bot has left the voice channel.")
    else:
        await ctx.send("Bot is not in a voice channel.")


@bot.command()
async def outro(ctx):
    """Plays an outro song, then disconnects everyone and leaves."""
    
    url = 'https://www.youtube.com/watch?v=3_-a9nVZYjk&ab_channel=TrapNation'
    stream_url, song_title = await get_stream_url(url)

    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        voice = ctx.guild.voice_client
        members = voice_channel.members

        if voice is None:
            voice = await voice_channel.connect()

        source = discord.FFmpegPCMAudio(stream_url, options="-t 56 -vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")

        if voice.is_playing():
            voice.stop()

        voice.play(source)
        await ctx.send(f"🎶 Playing outro: `{song_title}`")

        await asyncio.sleep(56)

        for member in members:
            if member != ctx.guild.me:
                await member.move_to(None)

        await ctx.voice_client.disconnect()
        await ctx.send("👋 Disconnected everyone and left the channel.")

    else:
        await ctx.send("❌ You need to be in a voice channel to use this command.")


async def play_audio(ctx, url, title=None):
    """Plays audio from a given URL."""
    try:
        stream_url, song_title = await get_stream_url(url)
        song_title = title or song_title
        
        voice = ctx.guild.voice_client
        if not voice:
            return

        source = discord.FFmpegPCMAudio(stream_url, options="-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        
        def after_playing(error):
            if error:
                logger.error(f"Error playing audio: {error}")
            
            if songs_queue:
                coro = play_next(ctx)
                asyncio.run_coroutine_threadsafe(coro, bot.loop)
            else:
                logger.info("Queue is empty, no more songs to play.")


        voice.play(source, after=after_playing)
        await ctx.send(f"Now playing: `{song_title}`")
    except Exception as e:
        logger.error(f"Error in play_audio: {e}")
        await ctx.send(f"An error occurred: `{e}`")


async def play_next(ctx):
    global looping_song
    voice = ctx.guild.voice_client

    if looping_song:
        await play_audio(ctx, looping_song)
    elif songs_queue:
        stream_url, song_title = songs_queue.popleft()
        await play_audio(ctx, stream_url, song_title)
    else:
        await asyncio.sleep(2)  # Ensure the song fully stops before clearing
        logger.info("Playback finished. Queue is empty.")


async def get_stream_url(url):
    """Retrieves the audio stream URL from YouTube."""
    try:
        if not url.startswith(("http://", "https://")):
            url = f"ytsearch:{url}"

        ydl_opts = {
            'format': 'bestaudio',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            return info['url'], info.get('title', 'Unknown Title')
    except yt_dlp.utils.DownloadError:
        return None, "Error: Could not extract audio stream. Try another link."
    except Exception as e:
        logger.error(f"Error getting stream URL: {e}")
        return None, f"Error: {str(e)}"


bot.run(bot_token)
