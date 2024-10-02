import discord
from discord.ext import commands
import pickle
import os

tempVoiceCmdIds = { # 0: Rename, 1: Limit, 2: Lock, 3: Unlock, 4: Claim
    0 : "Rename",
    1 : "Limit",
    2 : "Lock",
    3 : "Unlock",
    4 : "Claim"
}

class TempVoiceInterface(discord.ui.Button): # Button for the Temp Voice Interface
    def __init__(self, cmdId : int): # cmdId is the command id
        super().__init__( # create the button
            label=tempVoiceCmdIds[cmdId], # set the label to the command name
            style=discord.ButtonStyle.secondary, # set the style to secondary
            custom_id=str(cmdId), # set the custom id to the command id
        )

    async def callback(self, interaction: discord.Interaction): # when the button is clicked
        cmdId = int(self.custom_id) # get the command id
        noVoiceChannelText = "You don't have a temporary voice channel!"
        if cmdId == 0: # if the command id is 0
            if not memberIsChannelOwner(interaction.user): # if the member is not the channel owner
                return await interaction.response.send_message(noVoiceChannelText, ephemeral=True) # send a message that the member does not have a temporary voice channel
            await interaction.response.send_modal(RenameChannel(title="Rename your voice channel")) # send the rename channel modal
        elif cmdId == 1: # if the command id is 1
            if not memberIsChannelOwner(interaction.user): # if the member is not the channel owner
                return await interaction.response.send_message(noVoiceChannelText, ephemeral=True) # send a message that the member does not have a temporary voice channel
            await interaction.response.send_modal(LimitChannel(title="Set Userlimit")) # send the limit channel modal
        elif cmdId == 2: # if the command id is 2
            if not memberIsChannelOwner(interaction.user): # if the member is not the channel owner
                return await interaction.response.send_message(noVoiceChannelText, ephemeral=True) # send a message that the member does not have a temporary voice channel
            await LockChannel().callback(interaction) # lock the channel
        elif cmdId == 3: # if the command id is 3
            if not memberIsChannelOwner(interaction.user): # if the member is not the channel owner
                return await interaction.response.send_message(noVoiceChannelText, ephemeral=True) # send a message that the member does not have a temporary voice channel
            await UnlockChannel().callback(interaction) # unlock the channel
        elif cmdId == 4: # if the command id is 4
            await ClaimChannel().callback(interaction) # claim the channel

class TempVoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="temp-voice-interface", description="Sends the message for the voicechannel Interface (Only Bot Owner)") # Pfotenclub Server
    #@commands.slash_command(name="temp-voice-interface", guild_ids=[1001916230069911703], description="Sendet die Nachricht für das Sprachkanal Interface. (Nur für Bot Owner)") # Wolfiiis Server
    async def rolebutton(self, ctx: discord.ApplicationContext): # when the command is called
        if ctx.author.id != 327880195476422656: # if the author is not the bot owner
            return await ctx.respond("You are not the Bot Owner!", ephemeral=True) # send a message that the author is not the bot owner
        view = discord.ui.View(timeout=None) # create a view

        embed = discord.Embed( # create an embed
            title="Temp Voice Interface", # set the title
            description="This Interface can be used to configure the temporary voice channels!", # set the description
            color=discord.Color.blurple() # set the color
        )

        embed.set_footer(text="⚙️ Click on the buttons to use the interface!") # set the footer

        for cmdId in tempVoiceCmdIds: # for every command id
            view.add_item(TempVoiceInterface(cmdId)) # add the button to the view
        await ctx.send(embed=embed, view=view) # send the embed with the view
    
    @commands.Cog.listener() # when the bot is ready
    async def on_ready(self): # when the bot is ready
        view = discord.ui.View(timeout=None) # create a view
        for cmdId in tempVoiceCmdIds: # for every command id
            view.add_item(TempVoiceInterface(cmdId)) # add the button to the view
        self.bot.add_view(view) # add the view to the bot

class RenameChannel(discord.ui.Modal): # Modal for renaming the channel
    def __init__(self, *args, **kwargs) -> None: # when the modal is created
        super().__init__( # create the modal
            discord.ui.InputText( # create an input text
                label="Choose a new name for your channel!", # set the label
                placeholder="Leave blank to reset", # set the placeholder
                required=False, # set required to false
            ),
            *args,
            **kwargs,
        )
    async def callback(self, interaction: discord.Interaction): # when the modal is submitted

        channel = getTempChannelFromMember(interaction.user) # get the channel
        if channel is not None: # if the channel exists
            if self.children[0].value: # if the value is not empty
                await channel.edit(name=self.children[0].value) # set the name to the value
            else: 
                await channel.edit(name=f"{interaction.user.display_name}'s Channel") # set the name to the default name

        embed = discord.Embed( # create an embed
            title="Update successful!", # set the title
            description=f"Your channel is now named {channel.name}!", # set the description
        color=discord.Color.embed_background(), # set the color
        )
        await interaction.response.send_message(embeds=[embed], ephemeral=True) # send the embed
        
class LimitChannel(discord.ui.Modal): # Modal for setting the user limit
    def __init__(self, *args, **kwargs) -> None: # when the modal is created
        super().__init__( # create the modal
            discord.ui.InputText(  # create an input text
                label="Choose the new limit for your channel!", # set the label
                placeholder="Leave blank to reset the limit", # set the placeholder
                required=False, # set required to false
                max_length=2, # set the max length to 2
            ),
            *args,
            **kwargs,
        )
    async def callback(self, interaction: discord.Interaction): # when the modal is submitted
            
            if not self.children[0].value: # if the value is empty
                channel = getTempChannelFromMember(interaction.user) # get the channel
                await channel.edit(user_limit=5) # set the limit to 5
            elif self.children[0].value.isnumeric(): # if the value is a number
                channel = getTempChannelFromMember(interaction.user) # get the channel
                await channel.edit(user_limit=int(self.children[0].value)) # set the limit to the value
            else:
                return await interaction.response.send_message("Please enter a valid number! (1 - 99)", ephemeral=True) # send a message that the value is not a number
            embed = discord.Embed( # create an embed
                    title="Update successful!", # set the title
                    description=f"Your channel now has a limit of {interaction.user.voice.channel.user_limit}!", # set the description
                    color=discord.Color.embed_background(), # set the color
                )
            await interaction.response.send_message(embeds=[embed], ephemeral=True) # send the embed

class ClaimChannel():
    async def callback(self, interaction: discord.Interaction): # when the command is called
        
        if interaction.user.voice is None: # if the user is not in a voice channel
            return await interaction.response.send_message("You must be in a voice channel to claim a temporary voice channel!", ephemeral=True) # send a message that the user has to be in a voice channel
        elif memberIsChannelOwner(interaction.user): # if the member is the channel owner
            return await interaction.response.send_message("You already have a temporary voice channel!", ephemeral=True) # send a message that the member already has a temporary voice channel

        channel_id, member_id = pickle.load(open(f"temp-voice-ids/{interaction.user.voice.channel.id}.pkl", "rb")) # get the channel id and member id

        for member in interaction.user.voice.channel.members: # for every member in the channel
            if member.id == member_id: # if the member id is the same as the member id
                return await interaction.response.send_message("The channel owner is already in the temporary voice channel!", ephemeral=True) # send a message that the channel owner is already in the channel
        
        os.remove(f"temp-voice-ids/{channel_id}.pkl") # remove the file
        pickle.dump((channel_id, member.id), open(f"temp-voice-ids/{channel_id}.pkl", "wb")) # dump the new file

        await interaction.user.voice.channel.edit(name=f"{interaction.user.display_name}'s Channel") # set the name of the channel to the member's name

        embed = discord.Embed( # create an embed
            title="Temporary voice channel claimed!", # set the title
            description="You have successfully claimed the temporary voice channel!", # set the description
            color=discord.Color.blurple() # set the color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True) # send the embed

class LockChannel():
    async def callback(self, interaction: discord.Interaction): # when the command is called
        
        channel = getTempChannelFromMember(interaction.user) # get the channel
        await channel.set_permissions(interaction.guild.default_role, connect=False) # set the permissions
        embed = discord.Embed( # create an embed
            title="Update successful!", # set the title
            description="Your temporary voice channel has been successfully locked!", # set the description
            color=discord.Color.blurple() # set the color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True) # send the embed

class UnlockChannel(): # when the command is called
    async def callback(self, interaction: discord.Interaction): # when the command is called
        
        channel = getTempChannelFromMember(interaction.user) # get the channel
        await channel.set_permissions(interaction.guild.default_role, connect=True) # set the permissions
        embed = discord.Embed( # create an embed
            title="Update successful!", # set the title
            description="Your temporary voice channel has been successfully unlocked!", # set the description
            color=discord.Color.blurple() # set the color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True) # send the embed

def setup(bot):
    bot.add_cog(TempVoiceCog(bot))

def memberIsChannelOwner(member):
    for filename in os.listdir("temp-voice-ids"): # for every file in the directory
        if filename.endswith(".pkl"): # if the file is a pickle file
            channel_id, member_id = pickle.load(open(f"temp-voice-ids/{filename}", "rb")) # load the file
            if member_id == member.id: # if the member id is the same as the member id
                return True # return true
    return False

def getTempChannelFromMember(member): # get the channel from the member
    for filename in os.listdir("temp-voice-ids"): # for every file in the directory
        if filename.endswith(".pkl"): # if the file is a pickle file
            channel_id, member_id = pickle.load(open(f"temp-voice-ids/{filename}", "rb")) # load the file
            if member_id == member.id: # if the member id is the same as the member id
                return member.guild.get_channel(channel_id) # return the channel
    return None