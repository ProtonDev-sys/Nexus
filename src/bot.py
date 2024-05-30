import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import logging
from time import sleep
# Load environment variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Use all intents
intents = discord.Intents.all()

# Create bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=1,name="you"))
    logger.info(f'Logged in as {bot.user.name}')
    sleep(5)
    await bot.tree.sync(guild=discord.Object(1203047551813816380))
    await bot.tree.sync()
    

async def load_cogs(bot):
    # Get the directory of the current script (bot.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Path to the cogs directory
    cogs_dir = os.path.join(script_dir, "cogs")

    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            logger.info(f"loading {filename}")
            cog_path = f"cogs.{filename[:-3]}"
            await bot.load_extension(cog_path)
            
logger = None
async def main():
    global logger
    log_file_path = os.path.join('logs', 'bot.log')
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=log_file_path,
                        filemode='a')
    logger = logging.getLogger(__name__)
    await load_cogs(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
    # Run the bot
    bot.run(token)