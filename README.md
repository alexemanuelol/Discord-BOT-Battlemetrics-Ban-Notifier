# Discord Battlemetrics Ban Bot

A bot that uses the Battlemetrics API to poll information about recently banned players and updates
a discord servers 'wall of shame' text channel automatically whenever it detect new bans.

Use the config.ini file to set discordToken, discordTextChannelId, battlemetricsToken, banListId. You
can also set the polling interval (time between every poll of banlist data), prefix for commands and a
comma seperated list of names of admins that are allowed to operate bot commands.

## Setup

Script is written in Python 3.8

Run the following to setup the environment:

    $ pip install -r requirements.txt

## Other information

This have only been tested with Battlemtrics Rust servers, but should work with any other Battlemetrics integrated
server.

## Sources

[Discord PyPI API wrapper](https://pypi.org/project/discord.py/)

[Battlemetrics API Documentation](https://www.battlemetrics.com/developers/documentation)
