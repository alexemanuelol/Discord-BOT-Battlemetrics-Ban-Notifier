#!/usr/bin/env python3

"""
    SquadBanNotifier
    modified by lukeg3

    This is a Discord bot to read squad bans (or bans of any game supported by Battlemetrics RCON)
    adapted from the Discord Bot Battlemetrics Ban Notifier created by Alexemanuelol@GitHub

    This bot uses the Battlemetrics API to poll information about recently banned players at a regular intervaland updates
    a discord server's text channel automatically whenever a new ban is detected.

    See the README.md for how to configure the config.ini file prior to running this script.

"""
# import neccesary modules
import configparser
from lib2to3.pgen2.token import NOTEQUAL
import discord
import json
import requests
import os
import threading

from enum import Enum

# Read configuration file
config = configparser.ConfigParser()
config.read(os.path.abspath(__file__).replace(os.path.basename(__file__), "config.ini"))

"""Values pulled from config file loaded in"""
PREFIX = config["General"]["prefix"] #discord command prefix

DC_ADMINS = config["Discord"]["admins"].replace(" ", "").split(",") #discord admins list
DC_TOKEN = config["Discord"]["discordToken"] #discord Oauth token 
DC_TEXT_CHANNEL_ID = int(config["Discord"]["discordTextChannelId"]) #discord channel identifier

BM_TOKEN = config["Battlemetrics"]["battlemetricsToken"] #battlemetric api token
BM_BANLIST_ID = config["Battlemetrics"]["banListId"] #battlemetrics ban list id
BM_POLLING_INTERVAL = int(config["Battlemetrics"]["pollingInterval"]) #how often the api is polled (default 10 minutes)

HEADERS = {"Authorization" : "Bearer " + BM_TOKEN}
URL = "https://api.battlemetrics.com/bans?filter[banList]=" + BM_BANLIST_ID + "&include=user,server"

"""Define class used for storing ban information"""
class BanInfo(Enum):
    PLAYER_NAME     = 0
    STEAM_ID        = 1
    REASON          = 2
    NOTE            = 3
    TIME_BANNED     = 4
    TIME_UNBANNED   = 5
    SERVER          = 6
    ADMIN_NAME      = 7

class squadBanNotifier(discord.Client):
    """ Discord Ban Bot """
    def __init__(self, **options):
        """ Initialize """
        super().__init__(**options)
        self.prevList = None

        self.event = threading.Event()
        self.thread = threading.Thread(target=self.polling_thread, args=(self.event,))
        self.thread.start()

    async def on_ready(self):
        """ on_ready. """
        print('Logged on as', self.user)

    async def on_message(self, message):
        """ Whenever there is a new message in the discord channel. """
        messageUpper = message.content.upper()
        
        if message.author == self.user: #if its our bots message, the bot won't respond
            return

        print(str(message.author) + ": " + str(message.content))

        """Define Discord channel commands"""
        if str(message.author) in DC_ADMINS and message.content.startswith(PREFIX):
            command = messageUpper[len(PREFIX):]
            if command == "MANUALBANLISTPOLL": #command refreshs from api manually
                print("Running manual poll")
                await message.author.send("Manually pulled ban list")
                self.update()
            elif command == "LASTBAN": #command DMs the user that executes the command the last ban
                print("Pulling last ban")
                banList = get_banlist(URL, HEADERS)
                if banList != []:
                    await message.author.send(embed=self.create_embed_of_ban(banList[0]))
            elif command == "HELP": #command DMs the bot commands to the user that executes the command
                print("Messaging help information")
                await message.author.send(embed=self.create_help_embed())

    def polling_thread(self, event):
        """ Polling thread that runs every UPDATE_TIMER second """
        while True:
            self.update()
            event.wait(BM_POLLING_INTERVAL) # Wait for next poll

    def update(self):
        """ Poll from Battlemetrics API and if there is new data, display it in the discord text channel. """
        print("Polling from Battlemetrics API...\nURL: " + str(URL))
        banList = get_banlist(URL, HEADERS)
        if banList: # If poll was successful
            print("Poll was successful.")
            diff = self.get_banlist_difference(banList)
            if len(diff) > 0: #there is something new when diff length >0
                print("New bans detected!\n" + str(diff))
                self.update_text_channel(self, diff)
            else:
                print("Nothing new...")
        else:
            print("Poll was not successful...")

    def get_banlist_difference(self, newList):
        """ Returns a list of the difference between newList  and self.prevList. """
        if self.prevList == None: #if its the first time, fill prevlist with the current list
            self.prevList = newList
            return []

        difference = [item for item in newList if item not in self.prevList] #holds the differences between the last poll and current poll
        self.prevList = newList
        return difference

    def update_text_channel(temporary, self, newBans):
        """ Update text channel with the new bans. """
        print("Transmit new ban information to the discord text channel...")
        for ban in newBans:
            embedVar = self.create_embed_of_ban(ban)
            self.send_embed_to_text_channel(embedVar)
        print("Successfully sent to text channel")

    def create_help_embed(self):
        """ Create help embed for this bot. """
        embedVar = discord.Embed(title="Discord Command List", color=0x00ff00)
        embedVar.add_field(name="!help", value="Displays this help message", inline=False)
        embedVar.add_field(name="!manualbanlistpoll", value="Manually refreshes ban list and checks for changes", inline=False)
        embedVar.add_field(name="!lastban", value="DMs you the last ban made and its information", inline=False)
        return embedVar

    def create_embed_of_ban(self, ban):
        """ Creates an embed of a ban. """
        embedVar = discord.Embed(title="New Ban Information", color=0x00ff00)
        embedVar.add_field(name="PLAYER NAME", value=ban[BanInfo.PLAYER_NAME.value], inline=False)
        embedVar.add_field(name="STEAMID", value=ban[BanInfo.STEAM_ID.value], inline=False)
        embedVar.add_field(name="REASON", value=ban[BanInfo.REASON.value], inline=False)
        embedVar.add_field(name="NOTE", value=ban[BanInfo.NOTE.value], inline=False)
        embedVar.add_field(name="DATE", value=ban[BanInfo.TIME_BANNED.value], inline=False)
        embedVar.add_field(name="EXPIRES", value=ban[BanInfo.TIME_UNBANNED.value], inline=False)
        embedVar.add_field(name="SERVER", value=ban[BanInfo.SERVER.value], inline=False)
        embedVar.add_field(name="ADMIN NAME", value=ban[BanInfo.ADMIN_NAME.value], inline=False)
        return embedVar

    def send_embed_to_text_channel(self, embedVar):
        """ Send embed to text channel. """
        self.loop.create_task(self.get_channel(DC_TEXT_CHANNEL_ID).send(embed=embedVar))


def get_banlist(url, headers):
    """ Returns a list of the most recent banned players, default 10 players.
        Returns an empty list if request went wrong.
    """
    try:
        response = requests.get(url, headers=headers) 
    except Exception as e:
        print(e)
        return []

    banList = response.json()
   
    tempServer, tempBanner = dict(), dict()
    
    for include in banList["included"]:
        if include["type"] == "server": #list of server names
            tempServer[include["id"]] = include["attributes"]["name"]
        elif include["type"] == "user": #list of admin names
            tempBanner[include["id"]] = include["attributes"]["nickname"]
    playerNames, steamIds, banReasons, note, timeBanned, timeUnbanned, server, banner = ([] for i in range(8))
    for ban in banList["data"]: #fill all the fields for the embed
        try:
            playerNames.append(ban["meta"]["player"])
        except Exception as e:
            print("Unknown Player Name",e)
            playerNames.append("Unknown Player")
        steamIds.append(ban["attributes"]["identifiers"][0]["identifier"])
        banReasons.append(ban["attributes"]["reason"].replace(" ({{duration}} ban) - Expires in {{timeLeft}}.", ""))
        note.append(ban["attributes"]["note"])
        timeBanned.append(ban["attributes"]["timestamp"].replace("T", " ")[:-5])
        expires = ban["attributes"]["expires"]
        timeUnbanned.append(expires.replace("T", " ")[:-5] if expires != None else "Indefinitely")
        server.append(tempServer[ban["relationships"]["server"]["data"]["id"]])
        banner.append(tempBanner[ban["relationships"]["user"]["data"]["id"]])
    returnList = []
    for l in list(zip(playerNames, steamIds, banReasons, note, timeBanned, timeUnbanned, server, banner)):
        returnList.append(dict(zip([0,1,2,3,4,5,6,7], l)))
    return returnList


def config_check():
    """ Verify that config is set. """
    cfg = config["General"]["prefix"]
    if cfg == "None":
        raise Exception("Discord command prefix is not set.")
    
    cfg = config["Discord"]["discordToken"]
    if cfg == "None":
        raise Exception("Discord token is not set.")

    cfg = config["Discord"]["discordTextChannelId"]
    if cfg == "None":
        raise Exception("Discord text channel id is not set.")

    cfg = config["Battlemetrics"]["battlemetricsToken"]
    if cfg == "None":
        raise Exception("Battlemetrics token is not set.")

    cfg = config["Battlemetrics"]["banListId"]
    if cfg == "None":
        raise Exception("Battlemetrics banlist id is not set.")
    
    cfg = config["Battlemetrics"]["pollingInterval"]
    if cfg == "None":
        raise Exception("Battlemetrics polling interval is not set.")





if __name__ == "__main__":
    config_check()
    bot = squadBanNotifier()
    bot.run(DC_TOKEN)
