import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

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
            await ctx.send(f'Joined {channel}')
            source = discord.FFmpegPCMAudio(executable="ffmpeg", source=r"C:\Users\danas\Desktop\prog\discord_bot\sounds\test.mp3")
            voice.play(source)
        else:
            await ctx.send("Error")

    else:
        ctx.send('You need to be in a voice channel to use this command.')



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
    pass

@bot.command()
async def queue(ctx, arg):
    pass

@bot.command()
async def skip(ctx):
    pass

@bot.command()
async def stfu(ctx):
    if ctx.voice_client is not None:
        ctx.voice_client.disconnect()
        ctx.send(f'Bot has left the voice channel: {ctx.voice_client.channel}')
    else:
        ctx.send('Bot is not in a voice channel.')

@bot.command()
async def speed(ctx, arg):
    pass

bot.run(bot_token)