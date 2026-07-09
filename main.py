import os
import json
import random
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

try:
    GUILD = int(os.getenv('Main_Guild'))
    CATEGORY = int(os.getenv('Server_Logs'))
except (TypeError, ValueError):
    GUILD = None
    CATEGORY = None

CONFIG_FILE = "letter_log_config.json"
BANNED_GUILD_FILE = "banned-user-guild.json"
BANNED_GLOBAL_FILE = "banned-globally.json"
OPTOUT_FILE = "optout-user-guild.json"

STATUSES = [
    "Sending Love Letters",
    "Secret Admirer",
    "Creampie",
    "Loving you",
    "がんばって",
    "Please Don't Stawp",
    "I love the way you taste.",
    "Failure to pleasure a woman is a crime!!",
    "You wanna taste me daddy!"
]

def load_optouts() -> dict:
    if os.path.exists(OPTOUT_FILE):
        with open(OPTOUT_FILE, "r") as f:
            return json.load(f)
    return {}

def save_optouts(data: dict) -> None:
    with open(OPTOUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def load_banned_guilds() -> dict:
    if os.path.exists(BANNED_GUILD_FILE):
        with open(BANNED_GUILD_FILE, "r") as f:
            return json.load(f)
    return {}

def save_banned_guilds(data: dict) -> None:
    with open(BANNED_GUILD_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_banned_globally() -> list:
    if os.path.exists(BANNED_GLOBAL_FILE):
        with open(BANNED_GLOBAL_FILE, "r") as f:
            return json.load(f)
    return []

def save_banned_globally(data: list) -> None:
    with open(BANNED_GLOBAL_FILE, "w") as f:
        json.dump(data, f, indent=2)

def build_log_embed(
    sender: discord.Member,
    recipient: discord.Member,
    content: str,
    anonymous: bool,
    channel_name: str,
) -> discord.Embed:
    embed = discord.Embed(
        title="📨 New Letter Sent",
        color=discord.Color.dark_grey(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(
        name="Sender",
        value=f"{sender.name}\nID: `{sender.id}`",
        inline=True,
    )
    embed.add_field(
        name="Recipient",
        value=f"{recipient.name}\nID: `{recipient.id}`",
        inline=True,
    )
    embed.add_field(
        name="Settings",
        value=f"Anonymous: **{'Yes' if anonymous else 'No'}**",
        inline=False,
    )
    embed.add_field(name="Message Content", value=content[:1024], inline=False)
    embed.set_footer(text=f"Sent in #{channel_name}")
    return embed

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)


class OpenLetterView(discord.ui.View):
    def __init__(self, recipient: discord.Member, content: str, sender: discord.Member, anonymous: bool):
        super().__init__(timeout=None)
        self.recipient = recipient
        self.content = content
        self.sender = sender
        self.anonymous = anonymous

    @discord.ui.button(label="Open Letter", style=discord.ButtonStyle.primary, custom_id="open_letter_btn")
    async def open_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.recipient.id:
            await interaction.response.send_message("This letter isn't for you!", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="You received a letter!",
            description=self.content,
            color=0x2b2d31
        )
        
        sender_name = "Anonymous" if self.anonymous else self.sender.display_name
        
        embed.set_footer(text=f"From: {sender_name}")
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        button.label = "Opened"
        button.disabled = True
        button.style = discord.ButtonStyle.secondary
        await interaction.message.edit(view=self)


class LetterModal(discord.ui.Modal, title='Send a Letter'):
    letter_content = discord.ui.TextInput(
        label='Letter Content',
        style=discord.TextStyle.paragraph,
        placeholder='Write the content of your letter here...',
        required=True,
        max_length=2000
    )

    def __init__(self, recipient: discord.Member, anonymous: bool):
        super().__init__()
        self.recipient = recipient
        self.anonymous = anonymous

    async def on_submit(self, interaction: discord.Interaction):
        view = OpenLetterView(
            recipient=self.recipient, 
            content=self.letter_content.value, 
            sender=interaction.user, 
            anonymous=self.anonymous
        )
        
        await interaction.channel.send(
            content=f"{self.recipient.mention}, you have received a new letter!",
            view=view
        )
        await interaction.response.send_message("Your letter has been dispatched!", ephemeral=True)

        log_embed = build_log_embed(
            sender=interaction.user,
            recipient=self.recipient,
            content=self.letter_content.value,
            anonymous=self.anonymous,
            channel_name=interaction.channel.name,
        )

        config = load_config()
        local_channel_id = config.get(str(interaction.guild.id))
        if local_channel_id:
            local_log_ch = interaction.guild.get_channel(local_channel_id)
            if local_log_ch:
                try:
                    await local_log_ch.send(embed=log_embed)
                except discord.Forbidden:
                    pass

        if GUILD:
            hub_guild = interaction.client.get_guild(GUILD)
            if hub_guild:
                clean_name = interaction.guild.name.lower().replace(" ", "-")
                clean_name = "".join(c for c in clean_name if c.isalnum() or c == "-")
                hub_log_ch = discord.utils.get(hub_guild.text_channels, name=clean_name)
                if hub_log_ch:
                    await hub_log_ch.send(embed=log_embed)


@tasks.loop(seconds=15)
async def change_status():
    await bot.wait_until_ready()
    new_status = random.choice(STATUSES)
    await bot.change_presence(activity=discord.Game(name=new_status))

@bot.event
async def on_ready():
    print(f'{bot.user.name} is online')

    if not change_status.is_running():
        change_status.start()
        print("Dynamic Status Loop Started.")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    if not GUILD or not CATEGORY:
        print("Cannot process Server Join")
        return
    
    hub_guild = bot.get_guild(GUILD)
    if not hub_guild:
        print(f"Error: Could not find Main Guild")
        return
    
    hub_category = discord.utils.get(hub_guild.categories, id=CATEGORY)
    
    clean_channel_name = guild.name.lower().replace(" ", "-")
    clean_channel_name = "".join(c for c in clean_channel_name if c.isalnum() or c == "-")

    try:
        new_channel = await hub_guild.create_text_channel(name=clean_channel_name, category=hub_category)
        
        embed = discord.Embed(title=f"Confezzion Joined a New Server!", color=discord.Color.blue())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Owner", value=guild.owner.name if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Total Members", value=str(guild.member_count), inline=True)
        embed.set_footer(text="Confezzion Logger")

        await new_channel.send(embed=embed)

    except discord.Forbidden:
        print("Error: Missing permissions in Main Guild!")
    except Exception as e:
        print(f"An error occurred: {e}")


@bot.tree.command(name="letter", description="Send a secret letter to someone in this server!")
@app_commands.describe(
    recipient="Select the user you want to send the letter to",
    anonymous="Do you want to send this anonymously?"
)
@app_commands.choices(anonymous=[
    app_commands.Choice(name="Yes (Hide my identity)", value=1),
    app_commands.Choice(name="No (Show my username)", value=0)
])
async def letter_cmd(interaction: discord.Interaction, recipient: discord.Member, anonymous: app_commands.Choice[int]):
    global_bans = load_banned_globally()
    if str(interaction.user.id) in global_bans:
        await interaction.response.send_message("You are globally banned from using this bot.", ephemeral=True)
        return
        
    guild_bans = load_banned_guilds()
    user_guild_bans = guild_bans.get(str(interaction.user.id), [])
    if interaction.guild and str(interaction.guild.id) in user_guild_bans:
        await interaction.response.send_message("You are banned from using this command in this server.", ephemeral=True)
        return

    optouts = load_optouts()
    guild_id_str = str(interaction.guild.id) if interaction.guild else ""
    
    if guild_id_str in optouts.get(str(interaction.user.id), []):
        await interaction.response.send_message("You have opted out of the letter system in this server. Use `/no-letter` to opt back in first.", ephemeral=True)
        return
        
    if guild_id_str in optouts.get(str(recipient.id), []):
        await interaction.response.send_message(f"Sorry, {recipient.display_name} has opted out of receiving letters in this server.", ephemeral=True)
        return

    if recipient.bot:
        await interaction.response.send_message("Bots can't read letters!", ephemeral=True)
        return
    
    if recipient.id == interaction.user.id:
        romcom_lines = [
            "Writing a love letter to yourself? I know self-love is important, but let's leave some romance for the rest of us!",
            "You can't send a secret letter to yourself! Unless... are you your own secret admirer?",
            "Sending a confession to yourself? That's peak main character energy, but I'm not delivering that!",
            "I know you're amazing, but trying to date yourself is a bit much, don't you think?",
            "Error 404: Too much self-love detected. Go flirt with someone else!",
            "Do you have a name, or should I just call you mine? Because you cannot send letters to yourself.",
            "All the good pickup lines are taken…but I’m hoping you’re not. Watching you writing letters to yourself but why not someone!",
            "I seem to have lost my cell number. Can I have yours? Asking for a friend cause you seem to be too lonely to write letters to yourself.",
            "Have we met? Because you look exactly the one who writes letters to yourself.",
            "Waiting for you is like waiting for rain in this drought. Useless and disappointing. Said by your girlfriend.",
            "Seems like you got No cake to put your cream inside, that's why you writing letters to yourself."
        ]
        await interaction.response.send_message(random.choice(romcom_lines), ephemeral=True)
        return
        
    is_anonymous = bool(anonymous.value)
    await interaction.response.send_modal(LetterModal(recipient=recipient, anonymous=is_anonymous))

@bot.tree.command(name="no-letter", description="Opt out or back into sending and receiving letters in this server.")
@app_commands.describe(opt_out="Choose 'Yes' to opt out or 'No' to opt back in")
@app_commands.choices(opt_out=[
    app_commands.Choice(name="Yes (Opt out of letters)", value=1),
    app_commands.Choice(name="No (Opt back into letters)", value=0)
])
async def no_letter_cmd(interaction: discord.Interaction, opt_out: app_commands.Choice[int]):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
        return

    optouts = load_optouts()
    user_id_str = str(interaction.user.id)
    guild_id_str = str(interaction.guild.id)
    user_optouts = optouts.get(user_id_str, [])

    if opt_out.value == 1:
        if guild_id_str in user_optouts:
            await interaction.response.send_message("You have already opted out of letters in this server.", ephemeral=True)
            return
        
        user_optouts.append(guild_id_str)
        optouts[user_id_str] = user_optouts
        save_optouts(optouts)
        await interaction.response.send_message("You have opted out. You can no longer send or receive letters in this server.", ephemeral=True)
    
    else:
        if guild_id_str not in user_optouts:
            await interaction.response.send_message("You are already opted in to receiving letters.", ephemeral=True)
            return
        
        user_optouts.remove(guild_id_str)
        if not user_optouts:
            del optouts[user_id_str]
        else:
            optouts[user_id_str] = user_optouts
            
        save_optouts(optouts)
        await interaction.response.send_message("Welcome back! You can now send and receive letters again in this server.", ephemeral=True)

@bot.tree.command(name="letter-log", description="Set a channel in this server to receive letter logs.")
@app_commands.describe(channel="The channel where letter activity will be logged")
@app_commands.default_permissions(manage_guild=True)
async def letter_log_cmd(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
        return

    bot_member = interaction.guild.me
    perms = channel.permissions_for(bot_member)
    if not perms.send_messages or not perms.embed_links:
        await interaction.response.send_message(
            f" I don't have **Send Messages** and **Embed Links** permissions in {channel.mention}. "
            "Please fix that first, then run this command again.",
            ephemeral=True,
        )
        return

    config = load_config()
    config[str(interaction.guild.id)] = channel.id
    save_config(config)

    await interaction.response.send_message(
        f"Letter logs for **{interaction.guild.name}** will now be sent to {channel.mention}.",
        ephemeral=True,
    )

@bot.tree.command(name="letter-log-remove", description="Stop sending letter logs to the configured channel.")
@app_commands.default_permissions(manage_guild=True)
async def letter_log_remove_cmd(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
        return

    config = load_config()
    guild_key = str(interaction.guild.id)

    if guild_key not in config:
        await interaction.response.send_message("No log channel is currently configured for this server.", ephemeral=True)
        return

    del config[guild_key]
    save_config(config)

    await interaction.response.send_message("Letter logging has been disabled for this server.", ephemeral=True)

@bot.tree.command(name="ban-user", description="Ban a user from using the bot in this server.")
@app_commands.describe(user="The user to ban")
@app_commands.default_permissions(manage_guild=True)
async def ban_user_cmd(interaction: discord.Interaction, user: discord.Member):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
        return

    global_bans = load_banned_globally()
    if str(user.id) in global_bans:
        await interaction.response.send_message(f"{user.mention} is already globally banned from the bot.", ephemeral=True)
        return

    guild_bans = load_banned_guilds()
    user_bans = guild_bans.get(str(user.id), [])
    guild_id_str = str(interaction.guild.id)

    if guild_id_str in user_bans:
        await interaction.response.send_message(f"{user.mention} is already banned in this server.", ephemeral=True)
        return

    user_bans.append(guild_id_str)
    guild_bans[str(user.id)] = user_bans
    save_banned_guilds(guild_bans)

    if len(user_bans) >= 3:
        global_bans.append(str(user.id))
        save_banned_globally(global_bans)
        await interaction.response.send_message(f"{user.mention} has been banned in 3 servers and is now **globally banned**.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{user.mention} has been banned from using the bot in this server.", ephemeral=True)

@bot.tree.command(name="unban-user", description="Unban a user from using the bot in this server.")
@app_commands.describe(user="The user to unban")
@app_commands.default_permissions(manage_guild=True)
async def unban_user_cmd(interaction: discord.Interaction, user: discord.Member):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
        return

    global_bans = load_banned_globally()
    if str(user.id) in global_bans:
        await interaction.response.send_message(f"Cannot unban {user.mention} because they are globally banned.", ephemeral=True)
        return

    guild_bans = load_banned_guilds()
    user_bans = guild_bans.get(str(user.id), [])
    guild_id_str = str(interaction.guild.id)

    if guild_id_str not in user_bans:
        await interaction.response.send_message(f"{user.mention} is not banned in this server.", ephemeral=True)
        return

    user_bans.remove(guild_id_str)
    if not user_bans:
        del guild_bans[str(user.id)]
    else:
        guild_bans[str(user.id)] = user_bans
        
    save_banned_guilds(guild_bans)
    await interaction.response.send_message(f"{user.mention} has been unbanned in this server.", ephemeral=True)


if __name__ == "__main__":
    bot.run(TOKEN)
