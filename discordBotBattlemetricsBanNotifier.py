#!/usr/bin/env python3

"""
    Discord Bot Battlemetrics Ban Notifier

    Author: Alexemanuelol@GitHub

    A bot that uses the Battlemetrics API to poll information about recently banned players and updates
    a discord servers 'wall of shame' text channel automatically whenever it detect new bans.

    Use the config.ini file to set discordToken, discordTextChannelId, battlemetricsToken, banListId. You
    can also set the polling interval (time between every poll of banlist data), prefix for commands and a
    comma seperated list of names of admins that are allowed to operate bot commands.

"""

import configparser
import discord
import json
import requests
import os
import threading

from enum import Enum

# Read configuration file
config = configparser.ConfigParser()
config.read(os.path.abspath(__file__).replace(os.path.basename(__file__), "config.ini"))


PREFIX = config["General"]["prefix"]

DC_ADMINS = config["Discord"]["admins"].replace(" ", "").split(",")
DC_TOKEN = config["Discord"]["discordToken"]
DC_TEXT_CHANNEL_ID = int(config["Discord"]["discordTextChannelId"])

BM_TOKEN = config["Battlemetrics"]["battlemetricsToken"]
BM_BANLIST_ID = config["Battlemetrics"]["banListId"]
BM_POLLING_INTERVAL = int(config["Battlemetrics"]["pollingInterval"])

HEADERS = {"Authorization" : "Bearer " + BM_TOKEN}
URL = "https://api.battlemetrics.com/bans?filter[banList]=" + BM_BANLIST_ID + "&include=user,server"


class BanInfo(Enum):
    PLAYER_NAME     = 0
    STEAM_ID        = 1
    REASON          = 2
    TIME_BANNED     = 3
    TIME_UNBANNED   = 4
    SERVER          = 5
    ADMIN_NAME      = 6

class DiscordBotBattlemetricsBanNotifier(discord.Client):
    """ Discord Ban Bot """
    def __init__(self, **options):
        """ Init. """
        super().__init__(**options)
        self.prevList = None

        self.event = threading.Event()
        self.thread = threading.Thread(target=self.polling_thread, args=(self.event,))
        self.thread.start()

    async def on_ready(self):
        """ on_ready. """
        print('Logged on as', self.user)

    async def on_message(self, message):
        """ Whenever there is a new message. """
        messageUpper = message.content.upper()

        # don't respond to ourselves
        if message.author == self.user:
            return

        print(str(message.author) + ": " + str(message.content))

        # Add possible commands below
        if str(message.author) in DC_ADMINS and message.content.startswith(PREFIX):
            command = messageUpper[len(PREFIX):]
            if command == "MANUALBANLISTPOLL":
                print("Running manual poll")
                self.update()
            elif command == "LASTBAN":
                banList = get_banlist(URL, HEADERS)
                if banList != []:
                    await message.author.send(embed=self.create_embed_of_ban(banList[0]))

    def polling_thread(self, event):
        """ Polling thread that runs every UPDATE_TIMER second """
        while True:
            self.update()
            event.wait(BM_POLLING_INTERVAL) # Wait for next poll

    def update(self):
        """ Poll from Battrlematrics API and if there is new data, display it in the discord text channel. """
        print("Polling from Battlemetrics API...\nURL: " + str(URL))
        banList = get_banlist(URL, HEADERS)
        if banList: # If poll was successful
            print("Poll was successful.")
            diff = self.get_banlist_difference(banList)
            if len(diff) > 0: # Something new
                print("New bans detected!\n" + str(diff))
                self.update_text_channel(self, diff)
            else:
                print("Nothing new...")
        else:
            print("Poll was not successful...")

    def get_banlist_difference(self, newList):
        """ Returns a list of the difference between newList  and self.prevList. """
        if self.prevList == None: # First time
            self.prevList = newList
            return []

        difference = [item for item in newList if item not in self.prevList]
        self.prevList = newList
        return difference

    def update_text_channel(self, newBans):
        """ Update text channel with the new bans. """
        print("Transmit new ban information to the discord text channel...")
        for ban in newBans:
            embedVar = self.create_embed_of_ban(ban)
            self.send_embed_to_text_channel(embedVar)
        print("Transmition was successful.")

    def create_embed_of_ban(self, ban):
        """ Creates an embed of a ban. """
        embedVar = discord.Embed(title="WALL OF SHAME", color=0x00ff00)
        embedVar.add_field(name="PLAYER NAME", value=ban[BanInfo.PLAYER_NAME.value], inline=False)
        embedVar.add_field(name="STEAMID", value=ban[BanInfo.STEAM_ID.value], inline=False)
        embedVar.add_field(name="REASON", value=ban[BanInfo.REASON.value], inline=False)
        embedVar.add_field(name="DATE", value=ban[BanInfo.TIME_BANNED.value], inline=False)
        embedVar.add_field(name="EXPIRES", value=ban[BanInfo.TIME_UNBANNED.value], inline=False)
        embedVar.add_field(name="SERVER", value=ban[BanInfo.SERVER.value], inline=False)
        embedVar.add_field(name="ADMIN NAME", value=ban[BanInfo.ADMIN_NAME.value], inline=False)
        return embedVar

    def send_embed_to_text_channel(self, embedVar):
        """ Send embed to text channel. """
        self.loop.create_task(self.get_channel(self.channel).send(embed=embedVar))


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
        if include["type"] == "server":
            tempServer[include["id"]] = include["attributes"]["name"]
        elif include["type"] == "user":
            tempBanner[include["id"]] = include["attributes"]["nickname"]

    playerNames, steamIds, banReasons, timeBanned, timeUnbanned, server, banner = ([] for i in range(7))
    for ban in banList["data"]:
        playerNames.append(ban["meta"]["player"])
        steamIds.append(ban["attributes"]["identifiers"][0]["metadata"]["profile"]["steamid"])
        banReasons.append(ban["attributes"]["reason"].replace(" ({{duration}} ban) - Expires in {{timeLeft}}.", ""))
        timeBanned.append(ban["attributes"]["timestamp"].replace("T", " ")[:-5])
        expires = ban["attributes"]["expires"]
        timeUnbanned.append(expires.replace("T", " ")[:-5] if expires != None else "Indefinitely")
        server.append(tempServer[ban["relationships"]["server"]["data"]["id"]])
        banner.append(tempBanner[ban["relationships"]["user"]["data"]["id"]])

    returnList = []
    for l in list(zip(playerNames, steamIds, banReasons, timeBanned, timeUnbanned, server, banner)):
        returnList.append(dict(zip([0,1,2,3,4,5,6], l)))
    return returnList


def config_check():
    """ Verify that config is set. """
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



if __name__ == "__main__":
    config_check()
    bot = DiscordBotBattlemetricsBanNotifier()
    bot.run(DC_TOKEN)
