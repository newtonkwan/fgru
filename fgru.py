import discord
from discord.ext import commands, tasks
import json
import os
import re
import requests
from datetime import datetime

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise ValueError("No Discord token found. Please set the DISCORD_TOKEN environment variable.")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

group_id = 2112  # group ID

def save_last_posted_activity(activity_id):
    with open('last_posted_activity.json', 'w') as f:
        json.dump({'last_activity_id': activity_id}, f)

def get_last_posted_activity():
    try:
        with open('last_posted_activity.json', 'r') as f:
            data = json.load(f)
            return data['last_activity_id']
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def format_achievement_message(achievement):
    """Helper function to format an achievement message."""
    user = achievement['Username']
    skill = achievement['Skill']
    achievement_type = achievement['Type']
    xp_or_kc = "{:,}".format(int(achievement['Xp'])) 

    if achievement_type == "Pvm":
        if skill == "Clue_all": #custom exception for Colosseum Glory
            return f"{user} completed {xp_or_kc} Clues"
        elif skill == "Colosseum Glory": #custom exception for Colosseum Glory
            return f"{user} reached {xp_or_kc} Colosseum Glory"
        else:
            return f"{user} reached {xp_or_kc} KC at {skill}"
    elif achievement_type == "Skill":
        if skill in ['Ehp', 'Ehb']:  # These are usually treated as cumulative counters, not xp
            return f"{user} reached {xp_or_kc} {skill}"
        elif skill == "Overall":
            return f"{user} reached {xp_or_kc} XP {skill}"
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

            # messages = [format_achievement_message(achievement) for achievement in latest_achievements]
            # for msg in messages:
            #     await ctx.send(msg)

            # await ctx.send(msg)
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

@tasks.loop(minutes=1)
async def fetch_and_post_latest_activity():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Format current time as a string
    url = f"https://templeosrs.com/api/group_achievements.php?id={group_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'data' in data and data['data']:
            achievements = sorted(data['data'], key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
            latest_achievement = achievements[0]  # Get the latest achievement after sorting

            # Create a unique identifier for the latest achievement
            latest_activity_id = f"{latest_achievement['Username']}{latest_achievement['Date']}{latest_achievement['Skill']}"

            # Check if this is the same as the last posted activity
            if latest_activity_id != get_last_posted_activity():
                msg = format_achievement_message(latest_achievement)
                channels = ['bot-testing']
                for channel_name in channels:
                    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
                    if channel:
                        await channel.send(msg)
                # Save the ID of the latest posted activity
                save_last_posted_activity(latest_activity_id)
                print(f"{current_time} Posted new activity: {msg}")
            else:
                print(f"{current_time} No new activity to post.")
        else:
            print("No data available or group ID not found.")
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
