import argparse
import discord
from discord.ext import commands, tasks
import json
import os
import re
import requests
from datetime import datetime

# Setup argparse to handle command line arguments
parser = argparse.ArgumentParser(description="Run the Discord bot.")
parser.add_argument('--debug', action='store_true', help='Run the bot in debug mode')
args = parser.parse_args()

# Set environment variable based on the presence of the --debug flag
os.environ['DEBUG'] = 'True' if args.debug else 'False'

# Convert environment variable to a Boolean
DEBUG = os.getenv('DEBUG', 'False') == 'True'

if DEBUG:
    channels = ["bot-testing"]
else:
    channels = ["bot-testing", "adventure-log"]

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise ValueError("No Discord token found. Please set the DISCORD_TOKEN environment variable.")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

group_id = 2112  # group ID

activity_to_emoji = {
    'Overall': '<:skilling:1161180798163107880>',
}

def save_last_checked_time(timestamp):
    with open('last_activity_time.json', 'w') as f:
        json.dump({'last_activity_time': timestamp}, f)

def get_last_checked_time():
    try:
        with open('last_activity_time.json', 'r') as f:
            data = json.load(f)
            # Convert the stored string time to a datetime object
            return datetime.strptime(data['last_activity_time'], "%Y-%m-%d %H:%M:%S")
    except (FileNotFoundError, json.JSONDecodeError):
        # If there's an error, return the earliest possible datetime
        return datetime.min

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


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Command Prefix: {bot.command_prefix}')
    print("Commands loaded:")
    for command in bot.commands:
        print(command.name)
    print()
    fetch_and_post_latest_activity.start()  # Start the loop

@bot.command(name="latestactivity")
@commands.has_role("Oldton")
async def latest_activity(ctx, count: int = 1):
    """Command to fetch and display the latest group achievement from TempleOSRS API."""
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
            latest_achievements = achievements[:count]  # Get the latest achievement after sorting

            # Aggregate all messages into one
            messages = []
            for achievement in latest_achievements:
                messages.append(format_achievement_message(achievement))

            # Join all formatted messages into one large message
            final_message = "\n".join(messages)
            if len(final_message) > 2000:
                await ctx.send("The message is too long to send in one go. Consider reducing the number of activities.")
            else:
                await ctx.send(final_message)

        else:
            await ctx.send("No data available or group ID not found.")
    except requests.RequestException as e:
        await ctx.send(f"Failed to fetch data from API: {str(e)}")

@bot.command(name="sendto")
@commands.has_role("Oldton")
async def send_to_channel(ctx, channel_name: str, *, message: str):
    """Send a message to a specific channel by name."""
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
@commands.has_role("Oldton")
async def send_message(ctx, message: str):
    """Send a custom formatted message."""
    await ctx.send(message)

@tasks.loop(seconds=5)
async def fetch_and_post_latest_activity():
    current_time = datetime.now()
    last_checked_time = get_last_checked_time()

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
                    for channel_name in channels:
                        channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
                        if channel:
                            await channel.send(msg)
                
                # Update the last checked time to the timestamp of the last new achievement processed
                latest_activity_time = datetime.strptime(new_achievements[-1]['Date'], "%Y-%m-%d %H:%M:%S")
                save_last_checked_time(latest_activity_time.strftime("%Y-%m-%d %H:%M:%S"))
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

    allowed_channels = ['bot-testing', 'achievements']
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
