import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def oleg_joins():
    pass

@bot.command()
async def play(ctx, arg):
    await ctx.send(arg)

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
    pass

@bot.command()
async def speed(ctx, arg):
    pass

bot.run(bot_token)