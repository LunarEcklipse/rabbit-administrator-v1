### This file was used to help me learn how Pycord handled raw reaction events. This was my first time working with Pycord's raw action events, so I did this to help be build a fundamental understanding of how they worked.

import discord, os, dotenv

absolute_path = os.path.abspath(__file__) # Ensures the current working directory is correct.
directory_name = os.path.dirname(absolute_path)
os.chdir(directory_name)

### ENV SETUP ###

dotenv.load_dotenv()
bot_token = str(os.getenv("DISCORD_BOT_TOKEN"))

rabbot_intents = discord.Intents.default()
rabbot_intents.reactions = True
rabbot_intents.members = True
rabbot_intents.messages = True
rabbot_intents.message_content = True
rabbot = discord.Bot(intents=rabbot_intents)

@rabbot.event
async def on_ready():
    channel = await rabbot.fetch_channel(0) # Note that the Channel and Message IDs here were replaced with 0s for the privacy of the person the bot was made for, and should be changed if you use this.
    msg = await channel.fetch_message(0)
    for i in msg.reactions:
        print(i.emoji)
        print(type(i.emoji))

@rabbot.event 
async def on_raw_reaction_add(pl: discord.RawReactionActionEvent): # Handles reactions being added.
    print(type(pl.emoji))
    print(pl.emoji)
    
@rabbot.event
async def on_message(msg):
    print(msg)

rabbot.run(bot_token)