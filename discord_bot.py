import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp
from collections import deque
import asyncio

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
my_user_id = int(os.getenv('MY_USER_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

songs_queue = deque()
looping = False


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_voice_state_update(member, before, after):
    specific_user_id = my_user_id

    if member.id == specific_user_id and after.channel is not None and before.channel != after.channel:
        channel = after.channel

        if not member.guild.voice_client or member.guild.voice_client.channel != channel:
            await channel.connect()

        stream_url, song_title = await get_stream_url('https://www.youtube.com/watch?v=NcPmSohIl9k&ab_channel=Apothegm')
        
        if stream_url:
            voice = member.guild.voice_client
            source = discord.FFmpegPCMAudio(stream_url, options="-vn")
            
            if voice.is_playing():
                voice.stop()
            voice.play(source)


@bot.command()
async def play(ctx, *, arg):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        voice = ctx.guild.voice_client

        if voice is None:
            voice = await channel.connect()
            await ctx.send(f"Joined `{channel}`")
        
        _, song_title = await get_stream_url(arg)
        if voice.is_playing():
            queue_song(arg)
            await ctx.send(f"Added to queue: `{song_title}`")
        else:
            queue_song(arg)
            await play_next(ctx)
    else:
        await ctx.send("You need to be in a voice channel to use this command.")


@bot.command()
async def pause(ctx):
    global looping
    voice = ctx.guild.voice_client
    
    if voice.is_paused():
        looping = True
        voice.resume()
        await ctx.send("Audio is resumed.")
    else:
        looping = False
        voice.pause()
        await ctx.send("Audio is paused.")


@bot.command()
async def stfu(ctx):
    global looping
    looping = False

    if ctx.voice_client is not None:
        songs_queue.clear()
        await ctx.send(f"Bot has left the voice channel: `{ctx.voice_client.channel}`")
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("Bot is not in a voice channel.")


@bot.command()
async def loop(ctx, *, arg):
    global looping
    looping = True

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        voice = ctx.guild.voice_client

        if voice is None:
            voice = await channel.connect()
            await ctx.send(f"Joined {channel}")
        
        if voice.is_playing():
            await ctx.send("Wait till the end of the audio")
        else:
            while looping:
                queue_song(arg)
                await play_next(ctx)

                await asyncio.sleep(1)
                while voice.is_playing():
                    await asyncio.sleep(1)
    else:
        await ctx.send("You need to be in a voice channel to use this command.")


@bot.command()
async def outro(ctx):

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
        await asyncio.sleep(56)

        for member in members:
            await member.move_to(None)

        await ctx.voice_client.disconnect()

    else:
        await ctx.send(f"You need to be in a voice channel to use this command.")


def queue_song(arg):
    global songs_queue
    songs_queue.append(arg)


@bot.command()
async def print_queue(ctx):
    queue_list = list(songs_queue)
    await ctx.send(f"List of songs: `{queue_list}`")


async def play_next(ctx):
    if songs_queue:
        next_song = songs_queue.popleft()
        await play_audio(ctx, next_song)


@bot.command()
async def skip(ctx):
    global looping
    looping = False
    
    ctx.guild.voice_client.stop()
    await ctx.send(f"Skipping current song...")
    play_next(ctx)


@bot.command()
async def clear(ctx):
    global songs_queue

    songs_queue = deque()
    await ctx.send("Queue is cleared")


@bot.command()
async def play_audio(ctx, arg):
    try:
        stream_url, song_title = await get_stream_url(arg)
        voice = ctx.guild.voice_client

        if stream_url:
            source = discord.FFmpegPCMAudio(stream_url, options="-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
            
            def after_playing(error):
                if error:
                    print(f"Error while playing: `{error}`")
                coro = play_next(ctx)
                asyncio.run_coroutine_threadsafe(coro, bot.loop)
            
            if voice.is_playing():
                voice.stop()

            voice.play(source, after=after_playing)
            await ctx.send(f"Now playing: `{song_title}`")
        
        else:
            await ctx.send("Could not retrieve audio stream.")
    except Exception as e:
        await ctx.send(f"An error occurred: `{e}`")


async def get_stream_url(url):
    try:
        if not (url.startswith("http://") or url.startswith("https://")):
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

            song_title = info.get('title')
            stream_url = info['url']

        return stream_url, song_title
        
    except Exception as e:
        print(f"Error getting stream URL: `{e}`")
        return None


bot.run(bot_token)