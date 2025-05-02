import argparse
import discord
from discord.ext import commands, tasks
import json
import os
import re
import requests
from datetime import datetime

# TODO: Add a way to add than a string for Staff roles 
# Setup argparse to handle command line arguments
parser = argparse.ArgumentParser(description="Run the Discord bot.")
parser.add_argument('--debug', action='store_true', help='Run the bot in debug mode')
args = parser.parse_args()

# Set environment variable based on the presence of the --debug flag
os.environ['DEBUG'] = 'True' if args.debug else 'False'

# Convert environment variable to a Boolean
DEBUG = os.getenv('DEBUG', 'False') == 'True'

if DEBUG:
    channels = ["bot-spam"]
else:
    channels = ["bot-spam", "clogging-bot"]

TOKEN = os.getenv('DISCORD_LOG_CHASERS_APP_TOKEN')
if TOKEN is None:
    raise ValueError("No Discord token found. Please set the DISCORD_LOG_CHASERS_APP_TOKEN environment variable.")

allowed_role = "Staff"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='~', intents=intents)

group_id = 2802  # group ID. Log Chasers: 2802, FGRU: 2112

activity_to_emoji = {
    'Overall': '<:skilling:1161180798163107880>',
}

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
    print(achievement)
    user = achievement['Username']
    skill = achievement['Skill'] # [Abyssal Sire, Attack, Ehp, Overall, etc.]
    achievement_type = achievement['Type']  #[Pvm, Skill]
    milestone = achievement['Milestone']
    xp_or_kc = "{:,}".format(int(achievement['Xp'])) 
    timestamp = datetime.strptime(achievement['Date'], "%Y-%m-%d %H:%M:%S")
    # return f"{achievement}"

    # TODO: Add emojis for each message sent.   
    # skill = 'Overall'
    # emoji = activity_to_emoji[skill]
    # return f"{user} reached {xp_or_kc} {skill} {emoji}"

    embed = discord.Embed(
        title=f"{user} has reached a milestone",
        color=discord.Color.blue(), 
        timestamp=timestamp
    )
    # embed.add_field(name=f"{achievement_type}", value=f"{skill}", inline=True)
    # embed.add_field(name=f"test", value=f"{xp_or_kc}", inline=True)
    # TODO: add all images to a folder and use them to set thumbnail. 
    # embed.set_thumbnail(url="https://oldschool.runescape.wiki/images/Pet_snakeling.png")  # Replace with your emoji/image URL

    embed.set_footer(text="Log Chasers x TempleOSRS", icon_url="https://pbs.twimg.com/profile_images/1845743084274876434/siKDEd4S_400x400.jpg")
    # return embed

    if achievement_type == "Pvm":
        if skill == "Clue_all": #custom exception for All Clues
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

# async def fetch_group_recent_collection_log(group_id: int, count: int = 1, only_notable: bool = False):
#     """
#     Fetches recent collection log items for a group from TempleOSRS API.

#     Args:
#         group_id (int): The group ID to fetch data for.
#         count (int, optional): How many items to fetch (default 1, max 200).
#         only_notable (bool, optional): Whether to fetch only notable items (default False).

#     Returns:
#         List of dictionaries, each representing an obtained item.
#     """
#     base_url = "https://templeosrs.com/api/collection-log/group_recent_items.php"
#     params = {
#         "group": group_id,
#         "count": count,
#         "onlynotable": 1 if only_notable else 0
#     }
#     try:
#         response = requests.get(base_url, params=params)
#         response.raise_for_status()
#         data = response.json()
#         return data

#     except Exception as e:
#         await ctx.send(f"Failed to fetch data from API: {str(e)}")

format

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
                embed = discord.Embed(
                    title=f"{achievement['player_name_with_capitalization']} received a new collection log",
                    color=discord.Color.gold(),
                    timestamp = datetime.strptime(achievement['date'], "%Y-%m-%d %H:%M:%S")
                
            )
                if achievement['notable_item']:
                    embed.add_field(
                        name=f"Notable Item", 
                        value=f"{achievement['name']}",
                        inline=True
                    )
                # else: 
                #     embed.add_field(
                #         name=f"Common Item", 
                #         value=f"{achievement['name']}",
                #         inline=True
                #     )

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
                messages.append(format_achievement_message(achievement))
                embeds.append(format_embed_message(achievement))

            # Join all formatted messages into one large message
            final_message = "\n".join(messages)
            if len(final_message) > 2000:
                await ctx.send("The message is too long to send in one go. Consider reducing the number of activities.")
            else:
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
    """Send a custom formatted message. ~sendto <message>"""
    await ctx.send(message)

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
                    embed = discord.Embed(
                        title=f"{achievement['player_name_with_capitalization']} received a new collection log",
                        color=discord.Color.gold(),
                        timestamp = datetime.strptime(achievement['date'], "%Y-%m-%d %H:%M:%S")
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
                    msg = format_achievement_message(achievement)
                    embed = format_embed_message(achievement)
                    for channel_name in channels:
                        channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
                        if channel:
                            await channel.send(embed=embed)
                            # await channel.send(msg)
                
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
        await ctx.send("Command not found, please check the command and try again.")
    else:
        await ctx.send(f"An unexpected error occurred: {error}")

bot.run(TOKEN)
