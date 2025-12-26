import argparse
import asyncio
import discord
from discord.ext import commands, tasks
import json
import os
import re
import requests
from datetime import datetime, timezone


# Setup argparse to handle command line arguments
# TODO: Set up if __name__ == "__main__" to run the bot
# TODO: Add images to each picture
parser = argparse.ArgumentParser(description="Run the Discord bot.")
parser.add_argument('--debug', action='store_true', help='Run the bot in debug mode')
args = parser.parse_args()

# Set environment variable based on the presence of the --debug flag
os.environ['DEBUG'] = 'True' if args.debug else 'False'

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='~', intents=intents)

TOKEN = os.getenv('DISCORD_LOG_CHASERS_APP_TOKEN')
if TOKEN is None:
    raise ValueError("No Discord token found. Please set the DISCORD_LOG_CHASERS_APP_TOKEN environment variable.")



# Convert environment variable to a Boolean
DEBUG = os.getenv('DEBUG', 'False') == 'True'

if DEBUG:
    channels = ["bot-spam"]
else:
    channels = ["bot-spam", "milestone-bot"]

# TODO: Add a way to add than a string for Staff roles 
allowed_role = "Staff"

group_id = 2802  # group ID. Log Chasers: 2802, FGRU: 2112
# group_id = 2112  # group ID. Log Chasers: 2802, FGRU: 2112

def save_last_checked_time(name, timestamp):
    try:
        # Load existing data from the JSON file
        with open('last_activity_time.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is invalid, start with an empty dictionary
        data = {}

    # Update the specific entry
    data[name] = timestamp
    with open('last_activity_time.json', 'w') as f:
        json.dump(data, f)

def get_last_checked_time(name):
    """Get the last checked time for activity or log from a JSON file."""
    try:
        with open('last_activity_time.json', 'r') as f:
            data = json.load(f)
            # Convert the stored string time to a datetime object
            return datetime.strptime(data[name], "%Y-%m-%d %H:%M:%S")
    except (FileNotFoundError, json.JSONDecodeError):
        # If there's an error, return the maximum possible datetime
        return datetime.max

def format_achievement_message(achievement):
    """Helper function to format an achievement message."""
    user = achievement['Username']
    skill = achievement['Skill'] # [Abyssal Sire, Attack, Ehp, Overall, etc.]
    achievement_type = achievement['Type']  #[Pvm, Skill]
    milestone = achievement['Milestone']
    xp_or_kc = "{:,}".format(int(achievement['Xp'])) 
    # return f"{achievement}"

    # TODO: Add emojis for each message sent.   
    # skill = 'Overall'
    # emoji = activity_to_emoji[skill]
    # return f"{user} reached {xp_or_kc} {skill} {emoji}"
    if achievement_type == "Pvm":
        if skill == "Clue_all": #custom exception for All Clues
            return f"{user} completed {xp_or_kc} Clues"
        elif skill == "Clue_master":
            return f"{user} completed {xp_or_kc} Master Clues"
        elif skill == "Clue_elite": 
            return f"{user} completed {xp_or_kc} Elite Clues"
        elif skill == "Clue_hard":
            return f"{user} completed {xp_or_kc} Hard Clues"
        elif skill == "Clue_medium":
            return f"{user} completed {xp_or_kc} Medium Clues"
        elif skill == "Clue_easy":
            return f"{user} completed {xp_or_kc} Easy Clues"
        elif skill == "Clue_beginner":
            return f"{user} completed {xp_or_kc} Beginner Clues"
        elif skill == "Colosseum Glory": #custom exception for Colosseum Glory
            return f"{user} reached {xp_or_kc} Colosseum Glory"
        elif skill == 'Ehb':
            return f"{user} reached {xp_or_kc} EHB"
        elif skill == "LMS":
            return f"{user} reached {xp_or_kc} LMS score"
        else:
            return f"{user} reached {xp_or_kc} KC at {skill}"
    elif achievement_type == "Skill":
        if skill == 'Ehp':  # These are usually treated as cumulative counters, not xp
            return f"{user} reached {xp_or_kc} EHP"
        if milestone == "XP": 
            if skill == "Overall":
                return f"{user} reached {xp_or_kc} XP {skill}"
            else: 
                return f"{user} reached {xp_or_kc} XP in {skill}"
        if milestone == "Level":
            if skill == "Overall": 
                return f"{user} reached {xp_or_kc} Total Level"
            else:
                return f"{user} reached Level {xp_or_kc} in {skill}"
        else:
            return f"{user} reached {xp_or_kc} XP in {skill}"
    else:
        return f"{user} reached {xp_or_kc} {skill}"

def format_embed_message(achievement):
    """Helper function to format an achievement message into an embed."""
    # print(achievement)
    user = achievement['Username']
    skill = achievement['Skill']  # [Abyssal Sire, Attack, Ehp, Overall, etc.]
    achievement_type = achievement['Type']  # [Pvm, Skill]
    milestone = achievement['Milestone']
    xp_or_kc = "{:,}".format(int(achievement['Xp']))
    timestamp = datetime.strptime(achievement['Date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

    embed = discord.Embed(
        title=f"{user} has reached a milestone",
        color=discord.Color.blue(), 
        timestamp=timestamp
    )
    # embed.set_thumbnail(url="https://oldschool.runescape.wiki/images/Stats_icon.png?1b467")
    embed.set_footer(text="Log Chasers x TempleOSRS", icon_url="https://pbs.twimg.com/profile_images/1845743084274876434/siKDEd4S_400x400.jpg")
    if achievement_type == "Pvm":
        if skill == "Clue_all":  # custom exception for All Clues
            embed.add_field(name=f"Clues", value=f"All", inline=True)
            embed.add_field(name=f"Completed", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == "Clue_master":
            embed.add_field(name=f"Clues", value=f"Master", inline=True)
            embed.add_field(name=f"Completed", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == "Clue_elite":
            embed.add_field(name=f"Clues", value=f"Elite", inline=True)
            embed.add_field(name=f"Completed", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == "Clue_hard":
            embed.add_field(name=f"Clues", value=f"Hard", inline=True)   
            embed.add_field(name=f"Completed", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == "Clue_medium":
            embed.add_field(name=f"Clues", value=f"Medium", inline=True)   
            embed.add_field(name=f"Completed", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == "Clue_easy":
            embed.add_field(name=f"Clues", value=f"Easy", inline=True)   
            embed.add_field(name=f"Completed", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == "Clue_beginner":
            embed.add_field(name=f"Clues", value=f"Beginner", inline=True)   
            embed.add_field(name=f"Completed", value=f"{xp_or_kc}", inline=True)
            return embed
        # TODO: might need to take a look at this again.
        elif skill == "Colosseum Glory": #custom exception for Colosseum Glory
            embed.add_field(name=f"Activity", value=f"{skill}", inline=True)   
            embed.add_field(name=f"Glory", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == 'Ehb':
            # TODO: Test all caps 
            embed.add_field(name=f"Achievement", value=f"EHB", inline=True)   
            embed.add_field(name=f"Total", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == "LMS":
            embed.add_field(name=f"Activity", value=f"LMS", inline=True)   
            embed.add_field(name=f"LMS score", value=f"{xp_or_kc}", inline=True)
            return embed
        elif skill == "Collections": 
            embed.add_field(name=f"Activity", value=f"Collection Logs", inline=True)   
            embed.add_field(name=f"Logs", value=f"{xp_or_kc}", inline=True)
            return embed 
        else:
            embed.add_field(name=f"Boss", value=f"{skill}", inline=True)   
            embed.add_field(name=f"KC", value=f"{xp_or_kc}", inline=True)
            return embed 
    elif achievement_type == "Skill":
        if skill == 'Ehp':  # These are usually treated as cumulative counters, not xp
            embed.add_field(name=f"Skill", value=f"EHP", inline=True)   
            embed.add_field(name=f"Total", value=f"{xp_or_kc}", inline=True)
            return embed 
        if milestone == "XP": 
            if skill == "Overall":
                embed.add_field(name=f"Skill", value=f"{skill}", inline=True)   
                embed.add_field(name=f"XP", value=f"{xp_or_kc}", inline=True)
                return embed 
            else: 
                embed.add_field(name=f"Skill", value=f"{skill}", inline=True)   
                embed.add_field(name=f"XP", value=f"{xp_or_kc}", inline=True)
                return embed 
        if milestone == "Level":
            if skill == "Overall": 
                embed.add_field(name=f"Skill", value=f"{skill}", inline=True)   
                embed.add_field(name=f"Total Level", value=f"{xp_or_kc}", inline=True)
                return embed 
            else:
                embed.add_field(name=f"Skill", value=f"{skill}", inline=True)   
                embed.add_field(name=f"Level", value=f"{xp_or_kc}", inline=True)
                return embed 
        else:
            embed.add_field(name=f"Skill", value=f"{skill}", inline=True)   
            embed.add_field(name=f"XP", value=f"{xp_or_kc}", inline=True)
            return embed 
    else:
        embed.add_field(name=f"Skill", value=f"{skill}", inline=True)   
        embed.add_field(name=f"Level", value=f"{xp_or_kc}", inline=True)
        return embed 
    # TODO: Add EHC ? 

def is_notable(achievement):
    """Check if an achievement is notable"""
    # Filter Skill XP for only 200m
    if achievement['Type'] == "Skill" and achievement['Skill'] not in ["Overall", "Ehp"]:
        return achievement['Xp'] == 200000000

    # Filter Overall XP interval (every 1b or 4.6b)
    if achievement['Type'] == "Skill" and achievement['Skill'] == "Overall":
        return achievement['Xp'] % 1000000000 == 0 or achievement['Xp'] == 4600000000

    # Filter EHP interval (every 1,000)
    if achievement['Type'] == "Skill" and achievement['Skill'] == "Ehp":
        return achievement['Xp'] % 1000 == 0

    # Filter EHB interval (every 1,000)
    if achievement['Type'] == "Pvm" and achievement['Skill'] == "Ehb":
        return achievement['Xp'] % 1000 == 0

    # Filter Elite + Master clue interval (every 1,000)
    if achievement['Type'] == "Pvm" and achievement['Skill'] in ["Clue_elite", "Clue_master"]:
        return achievement['Xp'] % 1000 == 0

    # Filter collections interval (every 100)
    if achievement['Type'] == "Pvm" and achievement['Skill'] == "Collections":
        return achievement['Xp'] % 100 == 0

    # All else is not notable
    return False

def get_player_info(group_id: int = 2802, username: str = "Oldton") -> dict:
    """
    Fetches all available TempleOSRS data for a player in a given group.

    Args:
        group_id (int): The TempleOSRS group ID.
        username (str): The player's username (case-insensitive).

    Returns:
        dict: A dictionary of the player's data, or an error message.
    """
    def error_result(code: str, message: str) -> dict:
        return {"error": code, "message": message}

    url = f"https://templeosrs.com/api/group_member_info.php?id={group_id}&details=true"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        return error_result("RequestException", f"HTTP request failed: {e}")

    try:
        data = response.json()
    except ValueError:
        print("Response is not valid JSON:")
        print(response.text)
        return error_result("InvalidJSON", "Response was not valid JSON.")

    memberlist = data.get("data", {}).get("memberlist", {})
    if not isinstance(memberlist, dict):
        return error_result("InvalidFormat", "Expected memberlist to be a dictionary.")

    # Use lowercase matching for flexibility
    for player_key, player_data in memberlist.items():
        if player_key.lower() == username.lower():
            return player_data

    return error_result("PlayerNotFound", f"Player '{username}' is not in Log Chasers.")





# player_info = get_player_info()
# pprint(player_info, sort_dicts=False)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Command Prefix: {bot.command_prefix}')
    print("Commands loaded:")
    for command in bot.commands:
        print(command.name)
    print()
    fetch_and_post_recent_activity.start()  # Start the activity loop
    fetch_and_post_recent_logs.start()    # Start the log loop

@bot.command(name="recentlog")
@commands.has_role("Staff")  
async def recent_log(ctx, count: int = 1, only_notable: bool = True):
    """Send recent notable logs. ~recentlog <1-20>. Default: 1"""
    # TODO: This can't fetch more than 1 item? 
    if count < 1 or count > 20:
        await ctx.send("Please provide a count between 1 and 20.")
        return
    base_url = "https://templeosrs.com/api/collection-log/group_recent_items.php"
    params = {
        "group": 2802,
        "count": count,
        "onlynotable": 1 if only_notable else 0
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

    # TODO: Add back grouping functionliaty in
    # grouping them all together isn't a bad idea to be honest. 
        if 'data' in data and data['data']:
            # Sort achievements by date assuming 'Date' is in a sortable format
            achievements = sorted(data['data'], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
            recent_achievements = achievements[:count]  # Get the recent achievement after sorting
            embeds = [] 
            for achievement in recent_achievements:
                print(achievement)
                timestamp = datetime.strptime(achievement['date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                embed = discord.Embed(
                    title=f"{achievement['player_name_with_capitalization']} received a new collection log",
                    color=discord.Color.gold(), 
                    timestamp=timestamp
                    # TODO: figure out if you can have it be dyanmic based on timezone you're in. 
                
            )
                if achievement['notable_item']:
                    embed.add_field(
                        name=f"Notable Item", 
                        value=f"{achievement['name']}",
                        inline=True
                    )

                embed.set_footer(text="Log Chasers x TempleOSRS", icon_url="https://pbs.twimg.com/profile_images/1845743084274876434/siKDEd4S_400x400.jpg")
                embeds.append(embed)
            for embed in embeds:
                await ctx.send(embed=embed)
    except requests.RequestException as e:
        await ctx.send(f"Failed to fetch data from API: {str(e)}")

@bot.command(name="recentactivity")
@commands.has_role("Staff")
async def recent_activity(ctx, count: int = 1):
    """Send recent activity. ~recentactivity <1-20>. Default: 1"""
    if count < 1 or count > 20:
        await ctx.send("Please provide a count between 1 and 20.")
        return

    url = f"https://templeosrs.com/api/group_achievements.php?id={group_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        data = response.json()  # Parse JSON response

        if 'data' in data and data['data']:
            # Sort achievements by date assuming 'Date' is in a sortable format
            achievements = sorted(data['data'], key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
            recent_achievements = achievements[:count]  # Get the recent achievement after sorting

            # Aggregate all messages into one
            messages = []
            embeds = []
            for achievement in recent_achievements:
                print(achievement)
                embeds.append(format_embed_message(achievement))

            for embed in embeds:
                await ctx.send(embed=embed)

        else:
            await ctx.send("No data available or group ID not found.")
    except requests.RequestException as e:
        await ctx.send(f"Failed to fetch data from API: {str(e)}")


@bot.command(name="recentnotableactivity")
@commands.has_role("Staff")
async def recent_notable_activity(ctx, count: int = 20):
    """Send recent notable activity, if any."""
    url = f"https://templeosrs.com/api/group_achievements.php?id={group_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        data = response.json()  # Parse JSON response

        if 'data' in data and data['data']:
            # Sort achievements by date assuming 'Date' is in a sortable format
            achievements = sorted(data['data'], key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
            recent_achievements = achievements[:count]  # Get the recent achievement after sorting
            embeds = []
            for achievement in recent_achievements:
                if is_notable(achievement):
                    print(achievement)
                    embeds.append(format_embed_message(achievement))

            for embed in embeds:
                await ctx.send(embed=embed)

        else:
            await ctx.send("No data available or group ID not found.")
    except requests.RequestException as e:
        await ctx.send(f"Failed to fetch data from API: {str(e)}")

@bot.command(name="sendto")
@commands.has_role("Staff")
async def send_to_channel(ctx, channel_name: str, *, message: str):
    """Send a message to a channel. ~sendto <channel_name> <message>"""
    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    if channel:
        try:
            await channel.send(message)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages in that channel.")
        except discord.HTTPException:
            await ctx.send("Failed to send the message due to an HTTP error.")
    else:
        await ctx.send(f"Channel named '{channel_name}' not found.")


@bot.command(name="send")
@commands.has_role("Staff")
async def send_message(ctx, message: str):
    """Send a custom formatted message. ~send <message>"""
    await ctx.send(message)

@bot.command(name="joindate")
# @commands.has_role("Member")
async def join_date(ctx, *, username: str = None):
    """
    Get the join date of a player.
    Usage: ~joindate <username> or ~joindate (defaults to your display name)
    """
    requester_name = ctx.author.display_name
    target_name = username or requester_name

    def _send_error(message):
        return ctx.send(f"{message}")

    player_info = get_player_info(username=target_name)

    if 'error' in player_info:
        error_type = player_info['error']
        if error_type == "PlayerNotFound":
            return await _send_error(f"Hmm. Why don't you try <#1267596110109605930>?")
        return await _send_error(f"error: {player_info['message']}")

    join_date_raw = player_info.get('join_date')
    if not join_date_raw:
        return await _send_error(f"join date for '{target_name}' not found.")

    try:
        join_date_str = datetime.strptime(join_date_raw, "%Y-%m-%d %H:%M:%S").strftime("%B %d, %Y")
    except ValueError:
        return await _send_error(f"join date format for '{target_name}' is invalid.")

    await ctx.send(f"{target_name} joined on {join_date_str}.")

@bot.command(name="logcount")
@commands.has_role("Member")
async def get_logcount(ctx, *, username: str = None):
    """
    Show how many collection logs a player has completed.
    Usage: ~logcount <username> or ~logcount (defaults to 'Oldton')
    """

    target_name = username if username else ctx.author.display_name

    url = f"https://templeosrs.com/api/collection-log/player_collection_log.php?player={target_name}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        player_data = data.get("data", {})

        if not isinstance(player_data, dict):
            return await ctx.send(f"Player '{target_name}' not found or response was malformed.")

        count = player_data.get("total_collections_finished")
        if count is None:
            return await ctx.send(f"Could not find log count for '{target_name}'.")

        await ctx.send(f"{target_name} has completed {count:,} collection logs.")

    except Exception as e:
        await ctx.send(f"Error fetching log count for '{target_name}': {e}")

@bot.command(name="ehc")
@commands.has_role("Member")
async def get_ehc(ctx, *, username: str = None):
    """
    Show a player's EHC (Gilded algorithm).
    Usage: ~ehc <username> or ~ehc (defaults to 'Oldton')
    """
    
    target_name = username if username else ctx.author.display_name

    url = f"https://templeosrs.com/api/collection-log/player_collection_log.php?player={target_name}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        player_data = data.get("data", {})

        if not isinstance(player_data, dict):
            return await ctx.send(f"Player '{target_name}' not found or response was malformed.")

        # main = 0, iron = 1 
        # Main 
        if player_data.get("game_mode") == 0:
            ehc = player_data.get("ehc_gilded")
            await ctx.send(f"{target_name} has an EHC (Gilded) of {round(ehc):,} hours.")
        # Iron 
        elif player_data.get("game_mode") == 1:
            ehc = player_data.get("ehc_gilded_im")
            await ctx.send(f"{target_name} has an Iron EHC (Gilded) of {round(ehc):,} hours.")
        if ehc is None:
            return await ctx.send(f"Could not find EHC for '{target_name}'.")

    except Exception as e:
        await ctx.send(f"Error fetching EHC for '{target_name}': {e}")


@bot.command(name="2025")
@commands.has_role("Member")
# async def get_2025_stats(ctx):
# uncomment if you want to let other people check someone's 2025 stats
async def get_2025_stats(ctx, *, username: str = None):
    # TODO: Allow someone else to check someone's year of clogs? 
    """
    Show's the yearly summary of the a member from 2025
    Usage: ~2025 <username> or ~2025 (defaults to your display name)
    # TODO: for now, only allowing members of the cc to check their own stats. 

    Top 25 EHC 2025
    username    2025_ehc_gain
    Blom    5087.6172
    Browntree    3852.7013
    Kongherodes    2980.7925
    Siptar    2861.8267
    Swerve Q P    2787.4667
    Jabbau    2761.2737
    Jiqonix    2745.9797
    Kaiserbruno    2739.8936
    Weaki    2721.5772
    Cewl Hwip    2648.1867
    Biglenz    2640.2642
    Karilol    2627.5611
    Salii    2585.7048
    Retrohiili    2533.8368
    Fehz    2497.6902
    Ice Caves    2487.0152
    Bioterrorism    2477.0278
    Tails    2444.4198
    Paulest Paul    2410.9695
    Hypermark    2406.2316
    T Ylor    2388.1998
    Ir0n Crow    2385.9294
    Xiny    2366.9717
    Yak Of Iron    2348.1275
    Highnoobjhin    2333.8297

    Log Chasers | Top 10 EHC 2025 
    1.  Browntree     3852.7013
    2.  Siptar        2861.8267
    3.  werve q p     2787.4667
    4.  Jabbau        2761.2737
    5.  Weaki         2721.5772
    6.  Karilol       2627.5611
    7.  Retrohiili    2533.8368
    8.  Ice Caves     2487.0152
    9.  Bioterrorism  2477.0278
    10. Tails         2444.4198

    If people want to have their sync fixed, just ask Mikael 
    """
    
    # Uncomment if we want to allow you to check other people's years
    target_name = username if username else ctx.author.display_name
    # target_name = ctx.author.display_name

    await ctx.send(f"Generating **Year in OSRS 2025** for `{target_name}`...")
    # TODO: Do we really want to have a simulation time here...
    # await asyncio.sleep(2.5)  # Simulate processing time

    # url = f"https://templeosrs.com/api/collection-log/player_collection_log.php?player={target_name}"
    ts_2025_end = 1767254399 # Timestamp for December 31, 2025 23:59:59
    ts_2025_start = 1735718400 # Timestamp for January 1, 2025
    ts_2024_start = 1704099661 # Timestamp for January 1, 2024
    # url = f"https://templeosrs.com/api/player_gains.php?player={target_name}&time={time_since_2025_start}&bosses=1"
    # url = f"https://templeosrs.com/api/player_datapoints.php?player={target_name}&time={time_since_2025_start}&date=2025-12-31 00:00:00"
    url_2025_end = f"https://templeosrs.com/api/player_stats.php?player={target_name}&date={ts_2025_end}&bosses=1"
    url_2025_start = f"https://templeosrs.com/api/player_stats.php?player={target_name}&date={ts_2025_start}&bosses=1"
    url_2024_start = f"https://templeosrs.com/api/player_stats.php?player={target_name}&date={ts_2024_start}&bosses=1"

    url_ehc_yearlygains = f"https://templeosrs.com/api/collection-log/player_collection_log.php?player={target_name}&yearlygains=1"

    # TODO: 
    # Get current value of 2025 
    # EHC: 2000
    # EHB: 2000
    # EHP: 2000 

    # Get end of year value of 2024
    # EHC: 1500
    # EHB: 1500
    # EHP: 1500

    # Get end of year value of 2023 
    # EHC: 1250
    # EHB: 1250 
    # EhP: 1250

    # Get beginning of year value of 2023 


    # TODO: make group checking a lot faster. 
    # def _send_error(message):
    #     return ctx.send(f"{message}")

    # # Check if the person trying to call is in Log Chasers
    # player_info = get_player_info(username=target_name)
    # if 'error' in player_info:
    #     error_type = player_info['error']
    #     if error_type == "PlayerNotFound":
    #         return await _send_error(f"Sorry, `{target_name}` is not a member of Log Chasers.")
    #     return await _send_error(f"error: {player_info['message']}")

    
    

    try:
        response_2025_end = requests.get(url_2025_end)
        response_2025_start = requests.get(url_2025_start)
        response_2024_start = requests.get(url_2024_start)
        response_yearlygains = requests.get(url_ehc_yearlygains)
        response_2025_end.raise_for_status()
        data_2025_end = response_2025_end.json()
        data_2025_start = response_2025_start.json()
        data_2024_start = response_2024_start.json()
        data_yearlygains = response_yearlygains.json()
        player_data_2025_end = data_2025_end.get("data", {})
        # print(player_data_2025_end)
        # print()
        player_data_2025_start = data_2025_start.get("data", {})
        # print(player_data_2025_start)
        # print()
        player_data_2024_start = data_2024_start.get("data", {})
        # print(player_data_2024_start)
        # print()
        player_yearlygains = data_yearlygains.get("data", {})
        print(player_yearlygains)

        if not isinstance(player_data_2025_end, dict):
            return await ctx.send(f"Player '{target_name}' not found or response was malformed.")

        # main = 0, iron = 1 
        gamemode = player_data_2025_end["info"]["Game mode"]

        # Main 
        if gamemode == 0:
            # Get EHP
            start_2025_ehp = player_data_2025_start.get("Overall_ehp")
            start_2024_ehp = player_data_2024_start.get("Overall_ehp")
            if start_2024_ehp is None:
                start_2024_ehp = 0
            end_2025_ehp = player_data_2025_end.get("Overall_ehp")

            # Get EHB 
            start_2025_ehb = player_data_2025_start.get("Ehb")
            start_2024_ehb = player_data_2024_start.get("Ehb")
            if start_2024_ehb is None:
                start_2024_ehb = 0
            end_2025_ehb = player_data_2025_end.get("Ehb")         

        # Iron 
        elif gamemode == 1:
            # Get EHP
            start_2025_ehp = player_data_2025_start.get("Im_ehp")
            start_2024_ehp = player_data_2024_start.get("Im_ehp")
            if start_2024_ehp is None:
                start_2024_ehp = 0
            end_2025_ehp = player_data_2025_end.get("Im_ehp")

            # Get EHB 
            start_2025_ehb = player_data_2025_start.get("Im_ehb")
            start_2024_ehb = player_data_2024_start.get("Im_ehb")
            if start_2024_ehb is None:
                start_2024_ehb = 0
            end_2025_ehb = player_data_2025_end.get("Im_ehb")        

        # Calculate EHP stats
        ehp_gained_2025 = end_2025_ehp - start_2025_ehp
        ehp_gained_2024 = start_2025_ehp - start_2024_ehp
        ehp_percent_difference = ((ehp_gained_2025 - ehp_gained_2024) / ehp_gained_2024) * 100 if ehp_gained_2024 != 0 else 0

        # Calculate EHB stats
        ehb_gained_2025 = end_2025_ehb - start_2025_ehb
        ehb_gained_2024 = start_2025_ehb - start_2024_ehb
        ehb_percent_difference = ((ehb_gained_2025 - ehb_gained_2024) / ehb_gained_2024) * 100 if ehb_gained_2024 != 0 else 0
        
        # Calculate EHC stats
        ehc_2024 = player_yearlygains.get("yearly_gains", 0)['2024']
        ehc_2025 = player_yearlygains.get("yearly_gains", 0)['2025']
        ehc_percent_difference = ((ehc_2025 - ehc_2024) / ehc_2024) * 100 if ehc_2024 != 0 else 0


        # Calculate totals 
        total_gained_2025 = ehc_2025 + ehp_gained_2025 + ehb_gained_2025
        total_gained_2024 = ehc_2024 + ehp_gained_2024 + ehb_gained_2024
        total_percent_difference = ((total_gained_2025 - total_gained_2024) / total_gained_2024) * 100 if total_gained_2024 != 0 else 0

        total_message = f"{round(total_gained_2025):,} hrs" if target_name != 'Oldton' else '1411 hrs'
        total_percent_difference_message = f"{"{arrow} ".format(arrow="↑" if total_percent_difference >= 0 else "↓") + f"{abs(round(total_percent_difference)):,}%" if target_name != 'Oldton' else '↑ 36%'}"

        # Handle errors with EHP data 
        # Default message
        ehp_percent_difference_message = "{arrow} ".format(arrow="↑" if ehp_percent_difference >= 0 else "↓") + f"{abs(round(ehp_percent_difference)):,}%"
        if start_2024_ehp == None or start_2024_ehp == 0:
            ehp_percent_difference_message = "N/A"
            total_percent_difference_message = "N/A"
        # Handle errors with EHB data 
        # Default message
        ehb_percent_difference_message = "{arrow} ".format(arrow="↑" if ehb_percent_difference >= 0 else "↓") + f"{abs(round(ehb_percent_difference)):,}%"
        if start_2024_ehb == None or start_2024_ehb == 0:
            ehb_percent_difference_message = "N/A"
            total_percent_difference_message = "N/A"
        # Handle errors with EHC data 
        # Default message
        ehc_message = f"{round(ehc_2025):,} hrs" if target_name != 'Oldton' else '828 hrs'
        ehc_percent_difference_message = "{arrow} ".format(arrow="↑" if ehc_percent_difference >= 0 else "↓") + f"{abs(round(ehc_percent_difference)):,}%"
        # ehc_percent_difference_message = "{arrow} ".format(arrow="↑" if ehp_percent_difference >= 0 else "↓") + f"{abs(round(ehc_percent_difference)):,}%" if target_name != 'Oldton' else '↑ 91%'

        # Users has no 2025 EHC (data filtered out by TempleOSRS) 
        if ehc_2025 == 0: 
            ehc_message = "N/A"
        # User has no 2024 EHC (data filtered out by TempleOSRS) 
        # if ehc_2024 == 0 and target_name != 'Oldton': 
        if ehc_2024 == 0: 
            ehc_percent_difference_message = "N/A"
            total_percent_difference_message = "N/A"

        # Create the embed 
        embed = discord.Embed(title = f"{target_name}", color=discord.Color.dark_green())
        embed.set_author(name=f"Year in OSRS 2025", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(
            name=f"EHC", 
            value=ehc_message,
            inline=True
        )
    
        embed.add_field(
            name=f"vs. 2024", 
            value=ehc_percent_difference_message,
            inline=True 
        )

        embed.add_field(
            name="\u200b", 
            value=f"\u200b",
            inline=True
        )

        embed.add_field(
            name=f"EHP", 
            value=f"{round(ehp_gained_2025):,} hrs", 
            inline=True
        )
    
        embed.add_field(
            name=f"vs. 2024", 
            value=ehp_percent_difference_message,
            inline=True 
        )

        embed.add_field(
            name="\u200b", 
            value=f"\u200b",
            inline=True
        )

        embed.add_field(
            name=f"EHB", 
            value=f"{round(ehb_gained_2025):,} hrs",
            inline=True
        )

        embed.add_field(
            name="vs. 2024", 
            value=ehb_percent_difference_message,
            inline=True
        )

        embed.add_field(
            name="\u200b", 
            value=f"\u200b",
            inline=True
        )

        embed.add_field(
            name=f"Total", 
            value=total_message,
            inline=True
        )

        embed.add_field(
            name="vs. 2024", 
            value=total_percent_difference_message,
            inline=True
        )

        embed.add_field(
            name="\u200b", 
            value=f"\u200b",
            inline=True
        )

        embed.set_footer(text="Log Chasers x TempleOSRS | Year in OSRS 2025", icon_url="https://pbs.twimg.com/profile_images/1845743084274876434/siKDEd4S_400x400.jpg")
        await ctx.send(embed=embed)


        if start_2025_ehp is None:
            return await ctx.send(f"Could not find stats for '{target_name}'.")

    except Exception as e:
        await ctx.send(f"Error generating 2025 Year in OSRS for '{target_name}': {e}")

@tasks.loop(seconds=60)
async def fetch_and_post_recent_logs(count: int = 1, only_notable: bool = True):
    current_time = datetime.now()
    last_checked_time = get_last_checked_time('last_log_time')

    base_url = "https://templeosrs.com/api/collection-log/group_recent_items.php"
    params = {
        "group": 2802,
        "count": count,
        "onlynotable": 1 if only_notable else 0
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'data' in data and data['data']:
            achievements = sorted(data['data'], key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"))
            new_achievements = [a for a in achievements if datetime.strptime(a['date'], "%Y-%m-%d %H:%M:%S") > last_checked_time]
            if new_achievements:
                for achievement in new_achievements:
                    print(achievement)
                    timestamp = datetime.strptime(achievement['date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    embed = discord.Embed(
                        title=f"{achievement['player_name_with_capitalization']} received a new collection log",
                        color=discord.Color.gold(), 
                        timestamp=timestamp
                    )
                    if achievement['notable_item']:
                        embed.add_field(
                            name=f"Notable Item", 
                            value=f"{achievement['name']}",
                            inline=True
                        )
                    else: 
                        embed.add_field(
                            name=f"Common Item", 
                            value=f"{achievement['name']}",
                            inline=True
                        )

                    embed.set_footer(text="Log Chasers x TempleOSRS", icon_url="https://pbs.twimg.com/profile_images/1845743084274876434/siKDEd4S_400x400.jpg")
                    for channel_name in channels:
                        channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
                        if channel:
                            await channel.send(embed=embed)
                
                # Update the last checked time to the timestamp of the last new log processed
                recent_activity_time = datetime.strptime(new_achievements[-1]['date'], "%Y-%m-%d %H:%M:%S")
                save_last_checked_time('last_log_time', recent_activity_time.strftime("%Y-%m-%d %H:%M:%S"))
                print(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} - Posted new logs.")
            else:
                print(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} - No new logs to post.")

    except requests.RequestException as e:
        print(f"Failed to fetch data from API: {str(e)}")

@tasks.loop(seconds=60)
async def fetch_and_post_recent_activity():
    current_time = datetime.now()
    last_checked_time = get_last_checked_time(name='last_activity_time')

    url = f"https://templeosrs.com/api/group_achievements.php?id={group_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'data' in data and data['data']:
            achievements = sorted(data['data'], key=lambda x: datetime.strptime(x['Date'], "%Y-%m-%d %H:%M:%S"))
            new_achievements = [a for a in achievements if datetime.strptime(a['Date'], "%Y-%m-%d %H:%M:%S") > last_checked_time]

            if new_achievements:
                for achievement in new_achievements:
                    print(achievement)
                    embed = format_embed_message(achievement)
                    
                    for channel_name in channels:
                        channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
                        if channel: 
                            if is_notable(achievement) and channel_name == "milestone-bot":
                                await channel.send(embed=embed)
                            elif channel_name =="bot-spam": 
                                await channel.send(embed=embed)

                
                # Update the last checked time to the timestamp of the last new achievement processed
                recent_activity_time = datetime.strptime(new_achievements[-1]['Date'], "%Y-%m-%d %H:%M:%S")
                save_last_checked_time('last_activity_time', recent_activity_time.strftime("%Y-%m-%d %H:%M:%S"))
                print(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} - Posted new activities.")
            else:
                print(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} - No new activities to post.")

    except requests.RequestException as e:
        print(f"Failed to fetch data from API: {str(e)}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return

    if message.content.startswith('Hello FGRU'):
        await message.channel.send('Hello!')

    allowed_channels = ['bot-spam', 'achievements']
    if message.channel.name in allowed_channels:
        react = False
        if message.attachments:
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                    react = True
                    break

        # Check for X.com links
        if not react:
            if re.search(r"https?://(www\.)?x\.com/[\w\.-]+", message.content):
                react = True

        # Check for any Imgur links, including direct image links
        if not react and re.search(r"https?://(i\.)?imgur\.com/[\w\.-]+", message.content):
            react = True

        if react:
            emoji = '<:gz:1219333822731255828>'
            await message.add_reaction(emoji)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("You do not have the required role to execute this command.")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Error in command execution: {error.original}")
    elif isinstance(error, commands.CommandNotFound):
        return 
        # await ctx.send("Command not found, please check the command and try again.")
    else:
        await ctx.send(f"An unexpected error occurred: {error}")

bot.run(TOKEN)