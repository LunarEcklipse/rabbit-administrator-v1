# This was a master file I used for carrying shared objects around the codebase. I prefer to keep all of my objects in a separate master file rather than with the parts of code that these objects interact with because it helps me avoid circular imports. There's pros and cons to this strategy, but it works well enough for me.

import discord
from typing import List, Union
from datetime import datetime, timedelta
import aiohttp
import asyncio
import json
import os

absolute_path = os.path.abspath(__file__) # Ensures the current working directory is correct.
directory_name = os.path.dirname(absolute_path)
os.chdir(directory_name)
twitch_data_filepath = os.path.join(directory_name, "..", "twitch_data.json")

class ReactionRole: # Tracks which emoji reaction corresponds to which role.
    Emoji: discord.Emoji
    Role: discord.Role
    def __init__(self, emoji: str, role: discord.Role):
        self.Emoji = str(emoji)
        self.Role = role
        return
    
    def ConvertToDict(self) -> dict: # Converts this to a dict for saving.
        dc = {
            "Emoji": str(self.Emoji),
            "RoleID": int(self.Role.id)
        }
        return dc

class ReactableMessage: # Stores a reference to a discord message as well as all its reactions.
    PrimaryID: str
    ReferenceChannel: discord.TextChannel
    ReferenceMessage: discord.Message
    ReactionRoles: List[ReactionRole]
    def __init__(self, primary_id: str, reference_channel: discord.TextChannel, reference_msg: discord.Message, reaction_role_list: List[ReactionRole]):
        self.PrimaryID = primary_id
        self.ReferenceChannel = reference_channel
        self.ReferenceMessage = reference_msg
        self.ReactionRoles = reaction_role_list
        return
    

class TwitchConnection:

    ### CLASSES ###

    class TwitchAuth: # Handles OAuth2
        ClientID: str
        ClientSecret: str
        AccessToken: str
        RefreshToken: str
        Expiration: datetime
        TokenType: str
        IsValid: bool

        def __init__(self, client_id: str, client_secret: str):
            self.ClientID = client_id
            self.ClientSecret = client_secret
            self.AccessToken = None
            self.Expiration = None
            self.TokenType = None
            self.IsValid = False

        async def authenticate(self) -> bool: # This function forcefully updates the bot's access token regardless of whether or not it needs to be updated. Should only be called in an on_ready or when you know that the token is invalid.
            url = "https://id.twitch.tv/oauth2/token"
            auth_params = {
                "client_id": self.ClientID,
                "client_secret": self.ClientSecret,
                "grant_type": "client_credentials"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=auth_params) as resp:
                    js = None
                    if resp.status == 200:
                        js = await resp.json()
                        self.AccessToken = js["access_token"]
                        self.Expiration = datetime.now() + timedelta(seconds=js["expires_in"]) # Keep the expiration time in a datetime because it's easy as piss to do.
                        self.TokenType = js["token_type"]
                        self.IsValid = True
                        return True
                    else:
                        print(f"Unable to fetch authorization token: Received status code: {resp.status} from Twitch.")
                        self.AccessToken = None
                        self.Expiration = None
                        self.TokenType = None
                        self.IsValid = False
                        return False

    class TwitchStream:
        class TwitchGame:
            GameID: str
            Name: str
            BoxArtURL: str
            IgdbID: str

            def __init__(self, game_id: str, name: str, box_art_url: str, igdb_id: str):
                self.GameID = game_id
                self.Name = name
                self.BoxArtURL = box_art_url
                self.IgdbID = igdb_id

        StreamID: str
        UserLogin: str
        Username: str
        Game: TwitchGame
        StreamTitle: str
        StreamStartTime: datetime
        StreamThumbnailUrl: str
        StreamTags: list
        StreamIsMature: bool
        StreamViewerCount: int

        def __init__(self, stream_id: str,
                    user_login: str,
                    username: str,
                    game: TwitchGame,
                    title: str,
                    viewer_count: int,
                    started_at: str,
                    thumbnail_url: str,
                    is_mature: bool,
                    tags: list = []):
            self.StreamID = stream_id
            self.UserLogin = user_login
            self.Username = username
            self.Game = game
            self.StreamTitle = title
            self.StreamViewerCount = viewer_count # 2021-03-10T15:04:21Z
            self.StreamStartTime = datetime.strptime(started_at, "%Y-%m-%dT%H:%M:%SZ") # This datetime is in UTC.
            self.StreamViewerCount = viewer_count
            self.StreamThumbnailUrl = thumbnail_url
            self.StreamIsMature = is_mature
            self.StreamTags = tags

    class TwitchClip:
        pass

    ### VARIABLES ###

    Auth: TwitchAuth
    BroadcasterID: str
    AIOSession: aiohttp.ClientSession
    Stream: TwitchStream

    ### DATA FILE VARIABLES ### 
    MostRecentStreamID: str
    DiscordStreamUpdateGuildID: int
    DiscordStreamUpdateChannelID: int
    DiscordStreamUpdateRoleID: int

    def __init__(self, client_id: str, client_secret: str, broadcaster_id: str):
        self.Auth = TwitchConnection.TwitchAuth(client_id, client_secret)
        self.BroadcasterID = broadcaster_id
        self.AIOSession = aiohttp.ClientSession()
        self.Stream = None
        self.MostRecentStreamID = None
        self.DiscordStreamUpdateGuildID = None
        self.DiscordStreamUpdateChannelID = None
        self.DiscordStreamUpdateRoleID = None
        self.get_data_file_data()
        return

    async def get_stream(self) -> Union[TwitchStream, None]:
        url = "https://api.twitch.tv/helix/streams"
        params = {
            "user_id": self.BroadcasterID,
            "type": "live"
        }
        headers = {
            "Authorization": f"Bearer {self.Auth.AccessToken}",
            "Client-Id": self.Auth.ClientID
        }
        async with self.AIOSession.get(url, params=params, headers=headers) as resp:
            if resp.status == 200:
                js = await resp.json()
                if len(js["data"]) == 0: # No stream is live at the moment.
                    return None
                rawstrm = js["data"][0] # This will only ever have 1 stream in it at position 0 if it's not empty.
                game = await self.get_game(rawstrm["game_id"])
                return TwitchConnection.TwitchStream(rawstrm["id"], rawstrm["user_login"], rawstrm["user_name"], game, rawstrm["title"], rawstrm["viewer_count"], rawstrm["started_at"], rawstrm["thumbnail_url"], rawstrm["is_mature"], rawstrm["tags"])
            elif resp.status == 401: # We need to refresh our access token.
                self.Auth.IsValid == False
                return None
    
    async def get_game(self, game_id: str) -> TwitchStream.TwitchGame: # Fetches a game listing from the Twitch API.
        url = "https://api.twitch.tv/helix/games"
        params = {"id": game_id}
        headers = {
            "Authorization": f"Bearer {self.Auth.AccessToken}",
            "Client-Id": self.Auth.ClientID
        }
        async with self.AIOSession.get(url, params=params, headers=headers) as resp:
            if resp.status == 200:
                js = await resp.json()
                if len(js["data"]) == 0:
                    return None
                rawgm = js["data"][0] # This will only ever have 1 game in it at position 0 if it's not empty.
                return TwitchConnection.TwitchStream.TwitchGame(rawgm["id"], rawgm["name"], rawgm["box_art_url"], rawgm["igdb_id"])
            elif resp.status == 401: # We need to refresh our access token.
                self.Auth.IsValid == False
                return None
            
    def get_data_file_data(self):
        try:
            dat = None
            with open(twitch_data_filepath, 'r', encoding='utf-8') as f:
                raw = f.read()
                dat = json.loads(raw)
            self.MostRecentStreamID = dat["most_recent_stream_id"]
            self.DiscordStreamUpdateGuildID = dat["discord_stream_update_guild"]
            self.DiscordStreamUpdateChannelID = dat["discord_stream_update_channel"]
            self.DiscordStreamUpdateRoleID = dat["discord_stream_update_role"]

        except (FileNotFoundError, json.JSONDecodeError):
            dc = {
                    "most_recent_stream_id": self.MostRecentStreamID,
                    "discord_stream_update_guild": self.DiscordStreamUpdateGuildID,
                    "discord_stream_update_channel": self.DiscordStreamUpdateChannelID,
                    "discord_stream_update_role": self.DiscordStreamUpdateRoleID
                }
            with open(twitch_data_filepath, 'w', encoding='utf-8') as f:
                f.write(json.dumps(dc))
            return dc
        
    def write_data_file_data(self):
        with open(twitch_data_filepath, 'w', encoding="utf-8") as f:
            dc = {
                    "most_recent_stream_id": self.MostRecentStreamID,
                    "discord_stream_update_guild": self.DiscordStreamUpdateGuildID,
                    "discord_stream_update_channel": self.DiscordStreamUpdateChannelID,
                    "discord_stream_update_role": self.DiscordStreamUpdateRoleID
                }
            f.write(json.dumps(dc))
        return

class PersonalSpeedrun:
    InternalID: str
    SpeedrunDotComID: str
    VideoURL: str
    RunnerDiscordID: int
    Time: timedelta
    IsPB: bool

    def __init__(self, internal_id: str, speedrun_dot_com_id: str, video_url: str, runner_discord_id: int, time: timedelta, is_pb: bool):
        self.InternalID = internal_id
        self.SpeedrunDotComID = speedrun_dot_com_id
        self.VideoURL = video_url
        self.RunnerDiscordID = runner_discord_id
        self.Time = time
        self.IsPB = is_pb
        return
    
    