import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import pandas as pd
from ollama import Client

# Load .env file
load_dotenv()

# Get the token
TOKEN = os.getenv("DISCORD_TOKEN")

# Create bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Simple command
@bot.command()
async def ping(ctx):
    await ctx.send("I am here!")

@bot.command()
async def event(ctx, date: str):

    allowed_roles = {"Intern", "Admin", "Officer"}
    user_roles = {r.name for r in ctx.author.roles}

    if not allowed_roles & user_roles:  # intersection check
        await ctx.send("Sorry You don't have permission to use this command.")
        return
    
    df = pd.read_csv('ucdenver_events.csv')
    matching_rows = df.loc[df['Date'] == int(date)]

    if matching_rows.empty:
        await ctx.send(f"No events found for {date[:2]}/{date[2:]}.")
        return

    await ctx.send(f"# Events Happening On {date[:2]}/{date[2:]}")

    for _, each_event in matching_rows.iterrows():
        event_text = (

            f"\n\n **Title:** {each_event['Title']}\n\n"
            f"**Link:** <{each_event['Link']}>\n\n"  # prevents auto-embed
            f"**Time:** {each_event['Start']} - {each_event['End']}\n\n"
            f"**Location:** {each_event['Location']}\n\n"
            # f"**Event Detail:** {each_event['Summary']}\n\n"
            f"~~--------------------~~\n\n"

        )

        # send each event separately, suppressing embeds
        await ctx.send(event_text, suppress_embeds=True)

@bot.command()
async def q(ctx, question: str):

    allowed_roles = {"Intern", "Admin", "Officer"}
    user_roles = {r.name for r in ctx.author.roles}

    if not allowed_roles & user_roles:  # intersection check
        await ctx.send("Sorry You don't have permission to use this command.")
        return

    client = Client(
    host='http://localhost:11434',
    )
    response = client.chat(model='gpt-oss', messages=[
    {
        'role': 'user',
        'content': question,
    },
    ])
    await ctx.send(response.message.content)

# Run bot
bot.run(TOKEN)
