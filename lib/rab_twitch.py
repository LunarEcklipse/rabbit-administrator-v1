import os, dotenv
from datetime import datetime
import discord
from discord.ext import tasks, commands
import lib.rabobj as rabobj
import asyncio
import random

twitch_connection = None
twitch_connection_lock = asyncio.Lock()

absolute_path = os.path.abspath(__file__) # Ensures the current working directory is correct.
directory_name = os.path.dirname(absolute_path)
os.chdir(directory_name)

class TwitchFetch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch_loop.start()

    def cog_unload(self):
        self.twitch_loop.cancel()

    @tasks.loop(seconds=60.0)
    async def twitch_loop(self):
        global twitch_connection
        time_left = twitch_connection.Auth.Expiration - datetime.now()
        if twitch_connection.Auth.IsValid == False or (time_left.total_seconds() <= 3600):
            while twitch_connection.Auth.IsValid == False or time_left <= 3600:
                res = twitch_connection.Auth.authenticate()
                if res == True:
                    break
                else:           
                    asyncio.sleep(3.0)
        twitch_connection.Stream = await twitch_connection.get_stream()
        if type(twitch_connection.Stream) == rabobj.TwitchConnection.TwitchStream:
            if twitch_connection.Stream.StreamID != twitch_connection.MostRecentStreamID: # Holy shit there's a new stream
                twitch_connection.MostRecentStreamID = twitch_connection.Stream.StreamID
                twitch_connection.write_data_file_data()
                ds_channel = await self.bot.fetch_channel(twitch_connection.DiscordStreamUpdateChannelID)
                titleprint = None
                match twitch_connection.Stream.Game.Name: # Trust me, the stuff in here is funnier in context. As a note this is a match statement, so make sure you're using python3.10 or higher!
                    case "Just Chatting":
                        titleprint = "(PERSON) is Live Chatting on Stream!" # Anywhere indicated by (PERSON) is a place I replaced the user's original username with here to protect their privacy.
                    case "Pizza Tower":
                        randomls = ["Pizza Hut", "Domino's", "Papa John's", "Boston Pizza", "Little Caesars", "Chuck E. Cheese"]
                        randomstr = random.choice(randomls)
                        titleprint = f"(PERSON) just got fired from {randomstr}!"
                    case "Barotrauma":
                        randomls = ["Crawler", "Fractal Guardian", "Husk", "Husked Crawler", "Mudraptor", "Spineling", "Crawler Broodmother", "Bone Thresher", "Giant Spineling", "Hammerhead", "Tiger Thresher", "Moloch", "Hammerhead Matriarch", "Watcher", "Charybdis", "Endworm", "Latcher"]
                        randomstr = random.choice(randomls)
                        titleprint = f"(PERSON) just got eaten alive by a {randomstr}!"
                    case "Stellaris":
                        randomls = ["is breaching Galactic Law again!", "is the senate!", "is reclassifying humans as \"livestock\"!", "is committing war crimes!", "is contacting The Shroud!"]
                        randomstr = random.choice(randomls)
                        titleprint = f"(PERSON) {randomstr}"
                    case "RimWorld":
                        randomls = ["is committing war crimes again!", "is firing babies from mortar cannons!", "is harvesting organs!", "is selling organs again!", "is constructing killboxes!"]
                        randomstr = random.choice(randomls)
                        titleprint = f"(PERSON) {randomstr}"
                    case "Project Zomboid":
                        randomls = ["Left Foot", "Right Foot", "Left Shin", "Right Shin", "Left Thigh", "Right Thigh", "Left Hand", "Right Hand", "Left Forearm", "Right Forearm", "Left Upper Arm", "Right Upper Arm", "Groin", "Lower Torso", "Upper Torso", "Neck", "Head"]
                        randomstr = random.choice(randomls)
                        titleprint = f"(PERSON) just got bit on their {randomstr}!"
                    case "Sea of Thieves":
                        randomls = ["is deploying a Banana Bomb!", "is sinking Dark Adventurer sweats!", "is sinking Gold Curse sweats!", "is making fun of Reaper Pajamas!", "is tucking on someone's ship!", "is tucking at Reaper's Hideout!", "hasn't found the Shrouded Ghost yet!", "is getting Krakened. Again."]
                        randomstr = random.choice(randomls)
                        titleprint = f"(PERSON) {randomstr}"
                    case "ULTRAKILL":
                        randomls = ["is going to ULTRAKILL you!", "spiked an infant into a field goal!"]
                        randomstr = random.choice(randomls)
                        titleprint = f"(PERSON) {randomstr}"
                    case other:
                        titleprint = f"(PERSON) is Live Playing {twitch_connection.Stream.Game.Name}!"
                await ds_channel.send(f"<@&{str(twitch_connection.DiscordStreamUpdateRoleID)}> https://twitch.tv/(PERSON) {titleprint}\n\n{twitch_connection.Stream.StreamTitle}")

    @twitch_loop.before_loop
    async def before_twitch_loop(self): # Fetches the initial data of the bot right off the bat before waiting for the bot to fully ready up.
        global twitch_connection
        async with twitch_connection_lock: # Fetch the bot's initial data.
            twitch_connection = rabobj.TwitchConnection(str(os.getenv("TWITCH_CLIENT")), str(os.getenv("TWITCH_SECRET")), str(os.getenv("CHANNEL_ID")))
            await twitch_connection.Auth.authenticate()
            twitch_connection.Stream = await twitch_connection.get_stream()
        await self.bot.wait_until_ready()