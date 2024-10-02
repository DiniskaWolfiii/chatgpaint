from discord.ext import commands
import discord
import os # default module
from dotenv import load_dotenv
load_dotenv() # load all the variables from the env file
#bot = commands.Bot(debug_guilds=[1001916230069911703], intents=discord.Intents.all())
bot = commands.Bot(intents=discord.Intents.all())
@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

if __name__ == '__main__':
    if os.path.isdir("commands"):
        os.chdir("commands")
    else:
        os.chdir("app/commands")
    for i in os.listdir():
        if i.endswith(".py"):
            try:
                bot.load_extension(f"commands.{i[:-3]}")
            except Exception as error:
                print('{} konnte nicht geladen werden. [{}]'.format(i, error))
            else:
                print(f"{i} wurde geladen")
    if os.path.isdir("./../events"):
        os.chdir("./../events")
    else:
        os.chdir("./../app/events")
    for i in os.listdir():
        if i.endswith(".py"):
            try:
                bot.load_extension(f"events.{i[:-3]}")
            except Exception as error:
                print('{} konnte nicht geladen werden. [{}]'.format(i, error))
            else:
                print(f"{i} wurde geladen")

    if os.path.isdir("./../temp-voice"): # if the temp-voice folder exists
        os.chdir("./../temp-voice") # change the directory to the temp-voice folder
    else:
        os.chdir("./../temp-voice") # change the directory to the app/temp-voice folder
    for i in os.listdir(): # for every file in the directory
        if i.endswith(".py"): # if the file is a python file
            try:
                bot.load_extension(f"temp-voice.{i[:-3]}") # load the extension
            except Exception as error: # if there is an error
                print('{} konnte nicht geladen werden. [{}]'.format(i, error)) # print the error
            else:
                print(f"{i} wurde geladen") # print that the file was loaded
    
    if os.path.isdir("./../burgergeld"):
        os.chdir("./../burgergeld")
    else:
        os.chdir("./../app/burgergeld")
    for i in os.listdir():
        if i.endswith(".py"):
            try:
                bot.load_extension(f"burgergeld.{i[:-3]}")
            except Exception as error:
                print('{} konnte nicht geladen werden. [{}]'.format(i, error))
            else:
                print(f"{i} wurde geladen")


bot.run(os.getenv('TOKEN')) # run the bot with the token

# Test
