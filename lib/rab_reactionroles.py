# This was the file I was going to use to port the reaction role content into a Pycord cog. I never actually finished it, and the refactor will be removing this function anyways since it's essentially obsolete.

import discord
from discord.ext import commands

class ReactionRoleHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# TODO: Continue here and separate the role handling bot components into this cog!