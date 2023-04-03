import os, json, discord, dotenv
import asyncio
import lib.rabobj as rabobj
from typing import List
import lib.rab_twitch as rab_twitch

### CWD SETUP ###

absolute_path = os.path.abspath(__file__) # Ensures the current working directory is correct.
directory_name = os.path.dirname(absolute_path)
os.chdir(directory_name)

### ENV SETUP ###

message_list = []
msg_list_lock = asyncio.Lock() # This ensures that multiple things aren't trying to do the same thing at once.

dotenv.load_dotenv()
bot_token = str(os.getenv("DISCORD_BOT_TOKEN"))

### BASIC SETUP ###

rabbot_intents = discord.Intents.default()
rabbot_intents.reactions = True
rabbot_intents.members = True
rabbot_intents.messages = True
rabbot_intents.message_content = True

rabbot = discord.Bot(intents=rabbot_intents)
del rabbot_intents
print("Adding cog")
rabbot.add_cog(rab_twitch.TwitchFetch(rabbot))

### JSON READ/WRITE ###
def ReadFromDataFile() -> List[dict]:
    out = None
    try:
        with open("msg_data.json", 'r', encoding="utf-8") as f:
            raw = f.read()
        out = json.loads(raw)
    except FileNotFoundError: # Creates an empty file if not found.
        with open("msg_data.json", 'w', encoding="utf-8") as f:
            f.write("[]")
        out = []
    return out

def WriteToDataFile(data: List[dict]):
    with open("msg_data.json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(data))
    return

### ERROR LOGGING ###
async def Warn(guild: discord.Guild, message: str): # Sends a message out if the bot had to clear data for one reason or another.
    pass

async def WarnInvalidDataUponLoad(inMsg: dict): # Tries to recover a guild ID from an invalid data piece. If it succeeds, then let the guild owner know that the data failed.
    pass

### CATCH UP FUNCTIONS ###

def ValidateJSONData(in_data: dict) -> bool: # Checks if a component from the JSON data is fully intact.
    if "GuildID" not in in_data:
        return False
    elif type(in_data["GuildID"]) != int:
        return False
    elif "ChannelID" not in in_data:
        return False
    elif type(in_data["ChannelID"]) != int:
        return False
    elif "MessageID" not in in_data:
        return False
    elif type(in_data["MessageID"]) != int:
         return False
    elif "ReactionRoles" not in in_data:
        return False
    elif type(in_data["ReactionRoles"]) != list:
         return False
    for i in in_data["ReactionRoles"]:
        if "Emoji" not in i:
            return False
        if type(i["Emoji"]) != str:
            return False
        elif "RoleID" not in i:
            return False
        elif type(i["RoleID"]) != int:
            return False
    return True

def ConvertJSONDataToReactionRole(guild: discord.Guild, in_data: dict) -> rabobj.ReactionRole:
    inEmoji = in_data["Emoji"]
    if type(in_data["Emoji"]) == str:
        in_emoji = in_data["Emoji"]
    in_role = guild.get_role(in_data["RoleID"])
    return rabobj.ReactionRole(in_emoji, in_role)

async def ConvertJSONDataToReactableMessage(in_data: dict) -> rabobj.ReactableMessage:
    if ValidateJSONData(in_data) == False:
        return None
    in_guild = rabbot.get_guild(in_data["GuildID"])
    try:
        in_channel = await rabbot.fetch_channel(in_data["ChannelID"])
        in_msg = await in_channel.fetch_message(in_data["MessageID"])
    except discord.errors.NotFound:
        return None
    reactionrolelist = []
    for i in in_data["ReactionRoles"]:
        reactionrolelist.append(ConvertJSONDataToReactionRole(in_guild, i))
    return rabobj.ReactableMessage(in_channel, in_msg, reactionrolelist)

async def ValidateMessageComponentSynced(inMsg: rabobj.ReactableMessage) -> bool: # Checks if a ReactableMessage is synced properly. If not, then 
    if type(inMsg.ReferenceMessage) != discord.Message:
        return False
    for i in inMsg.ReactionRoles:
        if i.Emoji == None or i.Role == None:
            return False
    return True

async def ValidateAllMessageComponentsSynced(): # Goes through and makes sure that the components of everything in the message list still actually exists. If not, then remove it from the list to prevent problems.
    async with msg_list_lock:
        global message_list
        valid_messages = []
        for i in message_list:
            if await ValidateMessageComponentSynced(i):
                valid_messages.append(i)
        message_list = valid_messages


async def CatchUpUnroledReactions(): # Goes through the list of messages and catches up on reactions that have not been updated.
    global message_list
    for i in message_list:
        for j in i.ReferenceMessage.reactions:
            emojiinlist = False # Checks if the emoji that reactions are being viewed for is in the list of reactionroles
            reactionrole = None
            for k in i.ReactionRoles:
                if str(k.Emoji) == str(j.emoji):
                    emojiinlist = True
                    reactionrole = k
                    break
            if emojiinlist:
                users = await j.users().flatten()
                for k in users:
                    if k.id == rabbot.user.id: # Check if the given user is actually the bot so we don't accidentally nuke the base reaction.
                        continue
                    if type(k) == discord.Member: # This makes sure the user is a member and not a user. Users can't have roles added this way and only should be getting passed for users who left the guild anyways
                        if k.get_role(reactionrole.Role.id) == None: # If they don't have the role, add it.
                            await k.add_roles(reactionrole.Role, reason="Role automatically granted via bot following reaction request.")
                        else: # If they do have the role, remove it.
                            await k.remove_roles(reactionrole.Role, reason="Role automatically removed via bot following reaction request.")
                    await j.remove(k)
    return

async def CheckAllReactionsAreInPlace(): # Goes through the list of messages again and makes sure that no reactions disappeared while the bot was down.
    global message_list
    for i in message_list:
        for j in i.ReactionRoles:
            await i.ReferenceMessage.add_reaction(str(j.Emoji))
    return

### BOT EVENTS ###

@rabbot.event
async def on_ready():
    auth = rabobj.TwitchConnection.TwitchAuth(os.getenv("TWITCH_CLIENT"), os.getenv("TWITCH_SECRET"))
    await auth.authenticate()
    global message_list
    jsn = ReadFromDataFile() # Fetch data from JSON then check it against the guild list the bot has
    checkedlist = []
    for i in rabbot.guilds:
        for j in jsn:
            try:
                if i.id == j["GuildID"]:
                    checkedlist.append(i)
            except KeyError: # A way to filter out potentially bad data.
                continue
    for i in jsn:
        dat = await ConvertJSONDataToReactableMessage(i)
        if dat != None:
            message_list.append(dat)
    await ValidateAllMessageComponentsSynced()
    checkedlist = []
    for i in message_list:
        checkedlist.append(i.ConvertToDict())
    WriteToDataFile(checkedlist) # Saves all of the now validated data to avoid issues later down the road.
    await CheckAllReactionsAreInPlace()
    await CatchUpUnroledReactions()

@rabbot.event 
async def on_raw_reaction_add(pl: discord.RawReactionActionEvent): # Handles reactions being added.
    global message_list
    if pl.guild_id == None: # If this didn't take place in a guild, we don't care.
        return
    if pl.user_id == rabbot.user.id: # If *we* made this reaction, we ignore it.
        return
    channel = await rabbot.fetch_channel(pl.channel_id)
    message = await channel.fetch_message(pl.message_id)
    for i in message_list:
        if i.ReferenceMessage.id == message.id:
            member = pl.member
            
            emoji = str(pl.emoji) # TODO: Update this to check for unicode emojis
            for j in i.ReactionRoles:
                if str(j.Emoji) == str(emoji):
                    if member.get_role(j.Role.id) == None:
                        await member.add_roles(j.Role, reason="Role automatically granted via bot following reaction request.")
                    else:
                        await member.remove_roles(j.Role, reason="Role automatically removed via bot following reaction request.")
                    for k in message.reactions: # Unfortunately to actually remove this reaction we have to go actually find it now. A bit annoying but it is what it is.
                        if str(k.emoji) == str(emoji):
                            await k.remove(member)
                            return # We can just straight up return from this point because we found what we were looking for and handled it.
    return

@rabbot.event
async def on_raw_reaction_remove(pl: discord.RawReactionActionEvent): # When a reaction gets removed from a role, double check if that message is one from the list. If it is, then make sure the reaction the bot leaves on said message wasn't fucked.
    global message_list
    if pl.guild_id == None: # We don't care if this wasn't in a guild.
        return
    if pl.user_id != rabbot.user.id: # If we aren't the one whose reaction was removed, then we don't care.
        return
    channel = await rabbot.fetch_channel(pl.channel_id)
    msg = await rabbot.fetch_message(pl.message_id)
    for i in message_list:
        if i.ReferencedMessage.id == msg.id: # We still do all these checks as the data will be taken out of our message list if it's no longer valid.
            for j in msg.reactions:
                for k in i.ReactionRoles:
                    if str(k.Emoji) == str(j.emoji): # As stated before, we still actually run all these checks to see if the data exists in the back. If this data has been removed from the message list we don't want to try to keep tracking it anyways.
                        await msg.add_reaction(str(k.Emoji))
                        return # We can return here.

@rabbot.event
async def on_raw_reaction_clear(pl: discord.RawReactionClearEvent): # Check if the message was one being tracked by the bot. If so, re-add all reactions as to not cause problems.
    if pl.guild_id == None:
        return
    if pl.user_id == rabbot.user.id:
        return
    channel = await rabbot.fetch_channel(pl.channel_id)
    msg = await rabbot.fetch_message(pl.message_id)
    for i in message_list:
        if i.ReferencedMessage.id == msg.id:
            for j in i.ReactionRoles:
                await msg.add_reaction(str(j.Emoji))

@rabbot.event # TODO: Finish this
async def on_raw_reaction_clear_emoji(pl: discord.RawReactionClearEmojiEvent): # Check if the emoji was one being tracked by the bot. If so, re-add the reaction as to not cause problems.
    if pl.guild_id == None:
        return
    if pl.user_id == rabbot.user.id:
        return
    channel = await rabbot.fetch_channel(pl.channel_id)
    msg = await rabbot.fetch_message(pl.message_id)
    for i in message_list:
        if i.ReferencedMessage.id == msg.id:
            for j in msg.reactions:
                for k in i.ReactionRoles:
                    if str(k.Emoji) == str(j.emoji): # As stated before, we still actually run all these checks to see if the data exists in the back. If this data has been removed from the message list we don't want to try to keep tracking it anyways.
                        await msg.add_reaction(str(k.Emoji))
                        return # We can return here.

@rabbot.event # TODO: Finish this
async def on_guild_remove(guild: discord.Guild): # Nuke any data in that guild from the bot.
    async with msg_list_lock:
        message_list = filter(lambda x: (x.ReferenceChannel.guild.id != guild.id), message_list) # Removes all messages from that guild from the message list.

@rabbot.event # TODO: Finish this
async def on_guild_role_delete(role: discord.Role): # Check if the role was one that was being tracked. If so, nuke that reaction to prevent a dangling reference.
    async with msg_list_lock:
        new_msg_list = []
        for i in message_list:
            if i.ReferenceChannel.guild.id == role.guild.id: # We don't want to do anything unless the guild is correct to prevent an unlikely but definitely possible double delete.
                i.ReactionRoles = filter(lambda x: (i.Role.id != role.id), i.ReactionRoles)
            new_msg_list.append(i)
        message_list = new_msg_list

@rabbot.event # TODO: Finish this
async def on_raw_message_delete(pl: discord.RawMessageDeleteEvent): # Check if the deleted message was one being tracked. If so, nuke the data for it in the bot to prevent a dangling reference.
    if pl.guild_id == None:
        return
    async with msg_list_lock:
        message_list = filter(lambda x: ((x.ReferenceChannel.id != pl.channel_id) and (x.ReferenceMessage.id != pl.message_id)), message_list)

### START DISCORD ###
rabbot.run(bot_token)