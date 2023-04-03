### This is the file I was building to handle the conversion from .json data to SQLite prior to my overall refactor. If I had known how much the scope of the bot would have grown from the beginning, I would have just used SQLite to begin with. Doesn't matter anymore though, as I'm retooling this bot from scratch.
### I never actually finished this, so this SQLite integration won't work and is probably the largest fail point the bot currently has.

import sqlite3, os, dotenv, uuid

absolute_path = os.path.abspath(__file__) # Ensures the current working directory is correct.
directory_name = os.path.dirname(absolute_path)
os.chdir(directory_name)

db_path = os.path.join(directory_name, "..", "rabbot.db")

def ConnectToDB() -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    return con

def CreateDBIfNotExists():
    dbase = ConnectToDB()
    dbcs = dbase.cursor()
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Discord_ReactionMessages 
    (Reactable_ID TEXT PRIMARY KEY NOT NULL,
    Guild_ID: INT NOT NULL,
    Channel_ID INT NOT NULL,
    Message_ID INT NOT NULL)''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Discord_ReactionRoles
    (Reactable_ID TEXT NOT NULL,
    Emoji_Str TEXT NOT NULL,
    Role_ID INT NOT NULL
    FOREIGN KEY(Reactable_ID) REFERENCES Discord_ReactionMessages(Reactable_ID))''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Twitch_Streamers
    (Broadcaster_ID TEXT PRIMARY KEY NOT NULL, 
    Broadcaster_URL TEXT NOT NULL,
    Display_Name TEXT,
    Broadcaster_Type TEXT,
    Description TEXT,
    Profile_Image_URL TEXT,
    Channel_Created_Timestamp TEXT,
    Most_Recent_Stream_ID TEXT)''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Twitch_Game_Info
    (Game_ID TEXT PRIMARY KEY NOT NULL,
    Game_Name TEXT NOT NULL,
    Box_Art_URL TEXT,
    IGDB_ID TEXT)''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Twitch_Stream_Info
    (Broadcaster_ID TEXT PRIMARY KEY NOT NULL,
    Stream_ID TEXT NOT NULL,
    Stream_Game_ID TEXT,
    Stream_Title TEXT,
    Stream_Viewer_Count INT,
    Stream_Started_At TEXT,
    FOREIGN KEY(Broadcaster_ID) REFERENCES Twitch_Streamers(Broadcaster_ID),
    FOREIGN KEY(Stream_Game_ID) REFERENCES Twitch_Game_Info(Game_ID))''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Twitch_Stream_Discord_Channel_Updates
    (Broadcaster_ID TEXT NOT NULL,
    Discord_Guild_ID INT NOT NULL,
    Discord_Channel_ID INT NOT NULL,
    Discord_Role_ID INT,
    FOREIGN KEY(Broadcaster_ID) REFERENCES Twitch_Streamers(Broadcaster_ID))''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Discord_Twitch_Connections
    (Discord_User_ID INT NOT NULL,
    Twitch_Broadcaster_ID TEXT NOT NULL,
    FOREIGN KEY(Twitch_Broadcaster_ID) REFERENCES Twitch_Streamers(Broadcaster_ID))''') # We can kind of hack this for now but later we'll need to do oauth grants.
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Account_Speedrun_Connections
    (Discord_User_ID INT NOT NULL,
    Speedrun_Dot_Com_ID TEXT NOT NULL)''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Speedrun_Game_Info
    (Game_ID TEXT PRIMARY KEY NOT NULL,
    Game_Name TEXT NOT NULL,
    Game_Name_Twitch TEXT,
    Web_URL TEXT,
    Release_Date TEXT)''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Speedrun_Game_Categories
    (Game_ID TEXT NOT NULL,
    Category_ID TEXT NOT NULL,
    Category_Name TEXT NOT NULL,
    Category_Web_URL TEXT,
    Is_Miscellaneous INT NOT NULL,
    FOREIGN KEY(Game_ID) REFERENCES Speedrun_Game_Info(Game_ID))''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Speedrun_Game_Levels
    (Game_ID TEXT NOT NULL,
    Level_ID TEXT NOT NULL,
    Level_Name TEXT NOT NULL,
    Level_Web_URL TEXT,
    FOREIGN KEY(Game_ID) REFERENCES Speedrun_Game_Info(Game_ID))''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Speedrun_Game_Leaderboards
    (Leaderboard_ID TEXT PRIMARY KEY NOT NULL,
    Game_ID TEXT NOT NULL,
    Category_ID TEXT,
    Level_ID TEXT,
    Leaderboard_Web_URL TEXT,
    FOREIGN KEY(Game_ID) REFERENCES Speedrun_Game_Info(Game_ID),
    FOREIGN KEY(Category_ID) REFERENCES Speedrun_Game_Categories(Category_ID),
    FOREIGN KEY(Level_ID) REFERENCES Speedrun_Game_Levels(Level_ID))''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Speedrun_Leaderboard_Runs
    (Leaderboard_ID TEXT NOT NULL,
    Leaderboard_Position INT,
    Run_Time TEXT NOT NULL,
    Runner_ID TEXT NOT NULL,
    Runner_Name TEXT,
    Run_Comment TEXT,
    Is_Run_Verified INT NOT NULL,
    Submission_Date TEXT,
    Video_Link TEXT,
    FOREIGN KEY(Leaderboard_ID) REFERENCES Speedrun_Game_Leaderboards(Leaderboard_ID))''')
    dbcs.execute('''CREATE TABLE IF NOT EXISTS Personal_Speedrun_Information
    (Internal_Run_ID TEXT PRIMARY KEY NOT NULL,
    Speedrun_Dot_Com_ID TEXT,
    Video_Link TEXT,
    Runner_ID_Discord TEXT,
    Time TEXT NOT NULL,
    Is_PB INT NOT NULL)''')
    return

def GetPersonalBestsByDiscordID():
    pass