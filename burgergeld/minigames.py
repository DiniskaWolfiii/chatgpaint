import discord
from discord.ext import commands
import aiosqlite

class Minigames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bg_path = "./../data/burgergeld.db"

def setup(bot):
    bot.add_cog(Minigames(bot))