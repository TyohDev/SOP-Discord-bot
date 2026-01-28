import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio

# 1. Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
#MY_GUILD = discord.Object(id=) # Replace with your Server ID
REQUIRED_ROLE = "" # Replace with your Role Name or ID

@bot.event
async def on_ready():
    # Syncs the command to your specific server
    # bot.tree.copy_global_to(guild=MY_GUILD)
    # await bot.tree.sync(guild=MY_GUILD)

    # This registers the commands to Discord's central system 
    # so they appear in EVERY server the bot joins.
    try:
        synced = await bot.tree.sync() 
        print(f"Synced {len(synced)} command(s) globally.")
    except Exception as e:
        print(f"Error syncing: {e}")

    print(f"Logged in as {bot.user} | Multi-input Batch Bot is ready")

# 2. The Updated Command
@bot.tree.command(name="smashorpass", description="Post a sequence of Pokémon polls")
@app_commands.describe(
    start_id="The PokéDex number to start with (e.g. 1 for Bulbasaur)", 
    repeats="How many polls to create (e.g. 5)"
)
@app_commands.checks.has_role(REQUIRED_ROLE)
async def batch_poll(interaction: discord.Interaction, start_id: int, repeats: int):
    # Safety cap: Don't allow more than 20 at once to prevent spam kicks
    if repeats > 50:
        return await interaction.response.send_message("❌ Please keep repeats under 50.", ephemeral=True)

    #await interaction.response.send_message(f"🚀 Starting batch of {repeats} polls from ID {start_id}...", ephemeral=True)
    await interaction.response.defer(ephemeral=True, thinking=True)

    for i in range(repeats):
        current_id = start_id + i
        
        # Format the ID to be 3 digits (e.g., 1 becomes 001) 
        # Most Pokémon URL assets require this 3-digit format
        formatted_id = str(current_id).zfill(3)
        current_url = f"https://www.pokemon.com/static-assets/content-assets/cms2/img/pokedex/full/{formatted_id}.png"
        
        # Send the Image
        embed = discord.Embed(title=f"Pokédex #{formatted_id}", color=0xFF0000)
        embed.set_image(url=current_url)
        await interaction.channel.send(embed=embed)

        # Create the Native Poll
        my_poll = discord.Poll(
            question=f"Smash or Pass?",
            duration=datetime.timedelta(hours=24)
        )
        my_poll.add_answer(text="Smash", emoji="✅")
        my_poll.add_answer(text="Pass", emoji="❌")

        await interaction.channel.send(poll=my_poll)

        # Wait 1.5 seconds between each set
        await asyncio.sleep(1.5)

    #await interaction.followup.send("✅ Batch processing finished!", ephemeral=True)
    await interaction.delete_original_response()


# 3. Error Handling
@batch_poll.error
async def batch_poll_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message(f"❌ You need the **{REQUIRED_ROLE}** role.", ephemeral=True)
    else:
        print(f"Error: {error}")

@bot.tree.command(name="clear", description="Delete a specific number of recent messages")
@app_commands.describe(amount="The number of messages to delete")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    # 1. We must defer because deleting many messages can take more than 3 seconds
    await interaction.response.defer(ephemeral=True)

    # 2. Perform the purge
    # We use +0 here because the slash command itself doesn't count as a message in the channel
    deleted = await interaction.channel.purge(limit=amount)

    # 3. Send a private confirmation
    await interaction.followup.send(f"🗑️ Successfully deleted {len(deleted)} messages.", ephemeral=True)

# Note: You'll need this error handler so people without permissions don't crash the bot
@clear.error
async def clear_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ You need 'Manage Messages' permissions to use this!", ephemeral=True)

@bot.tree.command(name="clear_results", description="Specifically deletes the 'Poll closed' announcement messages")
@app_commands.describe(search_limit="How many messages back should I scan? (e.g., 100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_results(interaction: discord.Interaction, search_limit: int = 100):
    await interaction.response.defer(ephemeral=True, thinking=True)

    def is_poll_announcement(message):
        # 1. Catch the official poll result message type
        if message.type == discord.MessageType.poll_result:
            return True
        
        # 2. Catch messages that look like the ones in your screenshot
        # They usually have no 'author' in the traditional sense or are system messages
        content = message.content.lower()
        if "has closed" in content and "poll" in content:
            return True
            
        return False

    # Perform the purge
    deleted = await interaction.channel.purge(limit=search_limit, check=is_poll_announcement)

    await interaction.followup.send(f"🗑️ Cleaned up {len(deleted)} result announcements!", ephemeral=True)

bot.run('') #Put bot Token inside the quotations 