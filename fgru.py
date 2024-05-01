import discord
from discord.ext import commands
import os
import re

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise ValueError("No Discord token found. Please set the DISCORD_TOKEN environment variable.")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Command Prefix: {bot.command_prefix}')
    print("Commands loaded:")
    for command in bot.commands:
        print(command.name)

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
