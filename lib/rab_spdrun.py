# This segment was a work-in-progress prior to my decision to refactor this code. It is incomplete.

import os, dotenv
from datetime import datetime, timedelta
from typing import List
import discord
from discord.ext import commands
import lib.rabobj as rabobj
import asyncio
import random

spd_data = None
spd_data_lock = asyncio.Lock()

absolute_path = os.path.abspath(__file__) # Ensures the current working directory is correct.
directory_name = os.path.dirname(absolute_path)
os.chdir(directory_name)

class SpeedrunBestTime():
    TotalTimeSeconds: int
    GameName: str
    VideoURL: str
    
    def __init__(self, total_time_seconds: int, game_name: str, video_url: str):
        self.TotalTimeSeconds = total_time_seconds
        self.GameName = game_name
        self.VideoURL = video_url
        return

class SpeedrunCMD(commands.Cog):
    SpeedrunTimes: List[SpeedrunBestTime]

    def __init__(self, bot: discord.Bot):
        self.bot = bot

        def getSpeedTime(self):
            with open(os.path.join(directory_name, "..", "spd_data.json"), 'r', encoding="utf-8") as f:
                pass
        
        