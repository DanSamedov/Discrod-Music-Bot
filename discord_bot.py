import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
audio_path = os.getenv('AUDIO_PATH')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)


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

        try:
            await download_with_yt_dlp(arg)
            await ctx.send("Success! Starting to play the audio.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

        if os.path.exists(audio_path):
            source = discord.FFmpegPCMAudio(executable="ffmpeg", source=audio_path)
            voice.play(source)
        else:
            await ctx.send("Error: Audio file not found.")

    else:
        await ctx.send("You need to be in a voice channel to use this command.")


@bot.command()
async def clear(ctx):
    pass


@bot.command()
async def loop(ctx, arg):
    pass


@bot.command()
async def outro(ctx, arg):
    pass


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
async def queue(ctx, arg):
    pass


@bot.command()
async def skip(ctx):
    pass


@bot.command()
async def stfu(ctx):
    if ctx.voice_client is not None:
        await ctx.send(f"Bot has left the voice channel: {ctx.voice_client.channel}")
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("Bot is not in a voice channel.")


@bot.command()
async def speed(ctx, arg):
    pass


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