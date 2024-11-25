import discord
from discord.ext import commands
import os

class NightclubInterface(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Approve Me!"
            )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Welcome to the nightclub!", ephemeral=True)

class Nightclub(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
    @commands.slash_command(name="nightclub", description="Enter the nightclub", guild_ids=[1056514064081231872])
    async def nightclub(self, ctx):
        if ctx.author.id != 327880195476422656:
            return await ctx.respond("You are not the owner of the bot!", ephemeral=True)
        view = discord.ui.View()
        view.add_item(NightclubInterface())

        embed = discord.Embed(
            title="Nightclub",
            description="Click the button to get approved to join the Nightclub!\r\nPlease note that this will start a manual verification process. Only click on this button if you are 18+.",
            color=discord.Color.blurple()
            )

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Nightclub(bot)) # add the cog to the bot