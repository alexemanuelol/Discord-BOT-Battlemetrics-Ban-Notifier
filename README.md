# Discord Bot Squad Ban Notifier

modified by lukeg3

This is a Discord bot to read squad bans (or probably 
bans of any game supported by Battlemetrics RCON)
adapted from the Discord Bot Battlemetrics Ban Notifier created by Alexemanuelol@GitHub

This bot uses the Battlemetrics API to poll information about recently banned players at a regular intervaland updates
a discord server's text channel automatically whenever a new ban is detected.

## Environment Setup

Script is written in Python 3.10

Run the following to setup the environment:

    $ pip install -r requirements.txt

## Configuration

Setting up the config.ini file
### General
set the prefix for commands in the discord server (default option is "!" so a command would be "!help")

### Discord
set the admins that can execute commands in the Discord server in the admins field, use commas to seperate admins (format: name#0000)

Set up the discord bot by following this guide [Discord Developer Portal Getting Started](https://discord.com/developers/docs/getting-started#overview) and then put the bot token in the discordToken field in the config.ini file, DO NOT SHARE THIS TOKEN WITH
ANYONE.

Choose which channel you want the bot to put embeds in the discord server and then right click on the channel and "Copy ID". Paste this id into the discordTextChannelId field in the config.ini file.

### Battlemetrics
Get a battlemetrics token by going to the [Battlemetrics Developers Area](https://www.battlemetrics.com/developers), select 
"New Token" then make sure "Ban Lists", "Bans", and "RCON" are fully checked. Click "Create Token", then copy the access token
and put it in the battlemetricsToken field in the config.ini file, DO NOT SHARE THIS TOKEN WITH ANYONE.

Get the battlemetrics ban list id from [Battlemetrics Ban Lists](https://www.battlemetrics.com/rcon/ban-lists), click "View 
Bans" on the ban list you want to use. Then your URL will be https://www.battlemetrics.com/rcon/bans/?
filter%5BbanList%5D="BANLIST ID IS HERE" copy the part that is where "BANLIST ID IS HERE" is and put it in the banListId field 
in the config.ini file.

Finally set the polling interval (in seconds) to determine how often the ban list is updated. The recommended time is 10 minutes 
which is 600 seconds.

## Games this works with

At this time, this bot has only been tested with Squad. It should work for other games. 

## Contact

Message me on discord at LukeG01#7531 with questions or concerns.

## Future Plans

If this bot is adopted, it will be modified to be able to pull multiple ban lists and update the same or seperate channels for the embeds.

## Sources

[Discord PyPI API wrapper](https://pypi.org/project/discord.py/)

[Battlemetrics API Documentation](https://www.battlemetrics.com/developers/documentation)
