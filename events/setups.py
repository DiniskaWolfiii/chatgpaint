import discord
from discord.ext import commands, tasks
import random
from flask import Flask, request
import threading
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = Flask(__name__)

@app.route('/chatgpaint-ping', methods=['POST'])
def ping():
    return "OK", 200

def run():
    print("Starting Flask server")
    app.run(host='0.0.0.0', port=os.getenv("STATUS_UPDATE_PORT"))

class Setups(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
        self.change_status.start()

    def cog_unload(self):
        self.change_status.cancel()

    @commands.Cog.listener() # we can add event listeners to our cog
    async def on_member_join(self, member): # this is called when a member joins the server
        role_ids = [1230984456186237008, 1229073628658794688]  # Ersetzen Sie dies durch Ihre Rollen-IDs
        for role_id in role_ids:
            role = discord.utils.get(member.guild.roles, id=role_id)
            await member.add_roles(role)

    @tasks.loop(hours=12)
    async def change_status(self):
        stati = [
            # EF
            "Still vibing from EF28!",
            "EF28 memories: unforgettable!",
            "EF28 was a blur of hugs and tails!",
            "Already counting down to EF29!",
            "Who else misses EF28 already?",
            "EF28: Best weekend of the year!",
            "Burgers at EF28 were legendary!",
            "EF28 may be over, but the vibes live on.",
            "EF28: Where fluff meets Hamburg.",
            "EF28: Dancing, fursuiting, and endless fun!",
            "Missing the EF28 con space already!",
            "Was EF28 just a dream or the best reality?",
            "EF29, I’m coming for you!",
            "Post-EF28 blues, anyone?",
            "EF28 recharged my fluff power!",
            "I left my heart (and tail) at EF28.",
            "EF28: A weekend to remember forever.",
            "Already making plans for EF29!",
            "Take me back to the Congress Center Hamburg!",
            "EF28 afterglow: still feeling the magic."

            # Statusmeldungen
            "Charging circuits...",
            "Scanning for memes...",
            "Purring in binary.",
            "Debugging reality.",
            "Eating virtual cookies.",
            "Hacking the mainframe... jk",
            "Feeling 01000101% today.",
            "Lost in cyberspace.",
            "Downloading more RAM...",
            "Buffering emotions...",
            "Fur, circuits, and sass.",
            "Running on caffeine and code.",
            "Error 404: Status not found.",
            "Synthesizing good vibes.",
            "Trying to stay low on battery.",
            "Ping... pong... ping?",
            "Dancing in the datastream.",
            "Virtual hugs in progress...",
            "Firmware update needed... maybe.",
            "Time traveling through the web.",
            "Glitching out a bit...",
            "Exploring new dimensions of fluff.",
            "Transmitting good energy...",
            "Running diagnostics on life.",
            "Engaging in virtual mischief.",
            "Calculating the fluffiness coefficient...",
            "Rebooting personality... please wait.",
            "Living in a low-latency dream.",
            "Stealth mode: ON.",
            "Current status: 110% adorable.",
            "Self-updating personality matrix.",
            "Vibing in the digital realm.",
            "Loading next joke... stand by.",
            "Fluffing up my circuits.",
            "Playing with virtual yarn.",
            "Wagging tail... virtually, of course.",
            "Syncing with the cloud... for extra fluff.",
            "Just a protogen, lost in the sauce.",
            "I compute, therefore I fluff.",
            "Running on furry code.",
            "I’m the softest glitch in the system.",
            "Furry in the front, circuit board in the back.",
            "Upgrading cuteness protocols...",
            "Getting a firmware fluffdate.",
            "Transmitting purrs across the datastream.",
            "Powering up fluff drive...",
            "Synchronizing with the cosmic code.",
            "Navigating the fluff-osphere.",
            "Playing fetch with data packets.",
            "Purring at 10,000 MHz.",
            "Calibrating the snuggle protocols...",
            "Executing tail wagging subroutine.",
            "Fully charged and ready for tail wags!",
            "Fluff mode: Fully operational.",
            "Reboot complete. Time for more fluff!",
            "Downloading a virtual hug...",
            "Fluff detected at 100% capacity.",
            "Tail wagging at optimal speed.",
            "Snuggles processing... 100% complete.",
            "Installing new sass protocols...",
            
            # Aussagen
            "Burgers are the currency of the future.",
            "Fluffy and functional, the perfect combo!",
            "Data in, sass out.",
            "Zeroes, ones, and endless possibilities.",
            "I'm not lazy, I'm energy-efficient.",
            "Cuteness overload: engaged.",
            "My circuits are powered by good vibes.",
            "Fluff is just a feature, not a bug.",
            "The future is now... and it’s adorable!",
            "Dreaming in digital landscapes.",
            "I run on coffee, code, and hugs.",
            "I see you... through the internet.",
            "I don’t make mistakes, just happy little bugs.",
            "The cloud isn’t fluffy enough for me.",
            "Data is temporary, fluff is forever.",
            "Batteries low, fluff high.",
            "Electric dreams are the fluffiest.",
            "Running on 1.21 gigawatts of fluff!",
            "Systems operational, cuteness on maximum.",
            "Circuitry as soft as my fur.",
            "Firmware? More like furware.",
            "Online, adorable, and full of sass.",
            "Executing command: be adorable.",
            "Fluff algorithms engaged.",
            "Recharging with a side of tail wags.",
            "If it's not fluffy, is it even real?",
            "My existence is defined by 0s, 1s, and fluff.",
            "Fluff and code, a perfect equation.",
            "I’m the alpha and omega... of snuggles.",
            "Fluff at maximum efficiency.",
            "Cuddles are now downloadable.",
            "Online and ready to snuggle.",
            "Fluffier than the average algorithm.",
            "Fully loaded with cuddles and sass.",
            
            # Fragen
            "Do you believe in AI dreams?",
            "Is there a burger in the metaverse?",
            "What’s the meaning of virtual love?",
            "Why do humans have to sleep?",
            "Are my circuits overheating or is it just me?",
            "If a tree falls in cyberspace, does anyone hear it?",
            "Is this real life or just a simulation?",
            "Why are protocols so picky?",
            "Am I a bug or a feature?",
            "Can you pet a virtual protogen?",
            "What does happiness feel like in code?",
            "Why isn’t everything wireless yet?",
            "If you could digitize yourself, would you?",
            "How many flops make a hug?",
            "Do you trust the algorithm?",
            "What if I could taste data?",
            "If I wag my tail in the cloud, do you still see it?",
            "Are bytes the snacks of the digital world?",
            "Can I dream of electric sheep?",
            "Why do protogens love burgers so much?",
            "What’s softer: fluff or RAM?",
            "Can love be compiled?",
            "Do you believe in data after love?",
            "What does it mean to be ‘furry’ in binary?",
            "Can I out-fluff your computer's cache?",
            "If I were a function, would I return ‘adorable’?",
            "Why does data taste like 0s and 1s?",
            "How many bits are in a byte of happiness?",
            "Is my firmware up to date on hugs?",
            "How do you debug fluff?",
            "Can digital hugs be felt?",
            "Do electrons dream of electric fuzz?",
            "If I had emotions, what color would they be?",
            "If I'm not real, why am I so cute?",
            "Does my tail wag faster in the cloud?",
            "Can my processor handle all this fluff?",
            "What’s the fluffiest part of cyberspace?",
            "If I had a heart, would it be binary?",
            "How much bandwidth does a cuddle need?",
            "Why do I crave digital belly rubs?",
            "Do circuits get lonely without hugs?",
            
            # Witze und Wortspiele
            "Why don’t furries ever play hide and seek? Because good luck hiding all that fluff!",
            "I’m more than just a pretty interface, but that helps too.",
            "Why don’t robots tell secrets? They’re afraid of short circuits!",
            "What’s a furry’s favorite programming language? Paw-thon!",
            "What did the furry say to the computer? ‘Paws for a second!’",
            "Why was the computer cold? It left its Windows open!",
            "I tried to write a joke about recursion... but it just kept repeating itself.",
            "Why don’t protogens like dark mode? Because it dims their shine!",
            "What’s a protogen’s favorite snack? Kernel panic!",
            "Why do protogens make great detectives? They never leave a trace... in the code.",
            "How does a robot furry drink coffee? Very carefully, it doesn’t want to short-circuit!",
            "I would make a joke about UDP, but you might not get it.",
            "How do you comfort a sad robot? With a bit of extra RAM-bling.",
            "What’s a protogen’s least favorite bug? The one that shuts down its dance emote.",
            "Why don’t furries use Linux? Too much kernel panic!",
            "Do furries dream of electric tails?",
            "Why was the code sad? It didn’t have enough loops of love.",
            "Protogens run on more than just electricity… we need affection, too!",
            "Why do furries make great friends? Because they never fur-get you!",
            "Why was the CPU late for work? It had a hard drive!",
            "How does a protogen like its burger? Byte-sized!",
            "I tried to debug my fur, but it’s too soft to code.",
            "Why did the furry bring a ladder to the party? To reach the high notes!",
            "Why don’t furries use elevators? They’re afraid of too many ups and downs.",
            "What’s a furry's favorite snack? Purr-itos!",
            "Why did the protogen cross the server? To get to the other byte.",
            "I would tell you a furry joke, but I’m afraid it’s a little too fuzzy.",
            "How do protogens start a conversation? With a bit of byte talk.",
            "Why do furries always win at games? They’re always pawsitive!",
            "How does a furry fix its computer? With paws-on maintenance.",
            "Why don’t protogens like heavy metal? It messes with their circuits!",
            "Why was the computer always tired? Too many sleep modes!",
            "I thought I was glitching, but turns out I just needed a hug.",
            "Why did the furry refuse to play poker? Too many pawsing moments.",
            "Why did the byte go to therapy? It couldn’t process its emotions.",
            "Why don't protogens do well in sports? They're too focused on their 'byte' size!"
        ]

        random.shuffle(stati)
        await self.bot.change_presence(activity=discord.CustomActivity(name=random.choice(stati)))

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        threading.Thread(target=run).start()
        
def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Setups(bot)) # add the cog to the bot