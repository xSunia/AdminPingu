import discord
from discord.ext import commands, tasks
from discord.ui import Select, View
from flask import Flask
from threading import Thread
import random
import time
import datetime
import os
import aiohttp  # Added for the weather command

# ==========================================
# 1. RENDER KEEP-ALIVE SYSTEM (FLASK SERVER)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "AdminPingu is operational and running smoothly!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 2. BOT INITIALIZATION & INTENTS
# ==========================================
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

# ==========================================
# 3. DATA STRUCTURES & CONFIGURATIONS
# ==========================================
LOG_CHANNEL_ID = 123456789012345678       # Standard Mod Log Channel ID
WARNINGS_CHANNEL_ID = 1521880436270301354 # Profanity & Spam Warnings Channel
LEVEL_LOG_CHANNEL_ID = 1521880096854769785# Level Up Messages Channel
REMINDER_CHANNEL_ID = 123456789012345678  # Hourly Rule Reminder Channel

USER_ROLE_ID = 1510547520273649704        # Auto-role on Join
MEDIA_ROLE_ID = 1521875919864856714       # Level 20 Media Role

# Exactly 75 English Profanities and Slang Terms for Filtering
PROFANITY_LIST = [
    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "cunt", "bastard", "motherfucker", 
    "wanker", "twat", "nigger", "faggot", "slut", "whore", "crap", "bollocks", "bugger", 
    "choad", "crikey", "rubbish", "shag", "wank", "tosser", "twit", "prick", "clunge", 
    "muff", "scumbag", "dickhead", "bellend", "knobhead", "bint", "minger", "munter", 
    "arse", "arsehole", "asswipe", "bloody", "bastards", "bitches", "fucking", "fucker", 
    "shitting", "shitter", "bullshit", "horseshit", "dipshit", "jackass", "dumbass", 
    "badass", "dumbshit", "goddamn", "hell", "piss", "pissed", "pisser", "snatch", 
    "twats", "pricks", "dicks", "cocksucker", "motherfucking", "douche", "douchebag", 
    "skank", "slutty", "wankers", "coone", "kike", "spic", "retard", "tard", "scum"
]

LINUX_COMMANDS = [
    {"cmd": "ls", "desc": "🐧 Used to list directory contents. It is just like taking a quick look at the items inside a room!"},
    {"cmd": "cd", "desc": "🐧 Allows you to navigate between directories. It essentially teleports you from one path to another!"},
    {"cmd": "pwd", "desc": "🐧 Prints the full path of the current working directory."},
    {"cmd": "sudo", "desc": "🐧 Runs a command with the elevated security privileges of the system administrator 'root'."},
    {"cmd": "htop", "desc": "🐧 A much sleeker, colorful, and highly interactive modern upgrade to the classic 'top' command!"}
]

SERVER_RULES = [
    "Racism, ethnic discrimination, and hate speech of any kind are strictly prohibited.",
    "Unsolicited advertising, sharing invite links in channels or via DMs without permission is prohibited.",
    "Excessive swearing, toxic language, and personal insults are strictly prohibited.",
    "Impersonating another server member, staff member, or bot is strictly prohibited.",
    "Mass mentioning, spamming, and flooding channels with messages are prohibited."
]

LINUX_GIFS = [
    "https://media.giphy.com/media/LmNwrBhejkK9EFP504/giphy.gif",
    "https://media.giphy.com/media/i8XwYIrNqMEA8/giphy.gif",
    "https://media.giphy.com/media/VbKLOdvYXBEgw/giphy.gif",
    "https://media.tenor.com/7D-R9eYf6W8AAAAC/linux-penguin.gif",
    "https://media.tenor.com/V-nF03F5h20AAAAC/linux-arch.gif"
]

# New Entertainment & Info Data
TANK_FACTS = [
    "The British Mark I was the first tank to enter combat during the Battle of the Flers-Courcelette in 1916.",
    "Major General Ernest Swinton is highly credited with the conceptualization of the first armored tracked vehicles.",
    "The German Tiger I featured an 88mm KwK 36 gun, initially designed as an anti-aircraft flak cannon.",
    "Sloped armor, famously utilized on the Soviet T-34, increases the effective thickness of the armor against incoming shells."
]

MMA_FACTS = [
    "Jon 'Bones' Jones became the youngest champion in UFC history at age 23.",
    "The traditional Octagon was created to avoid the structural disadvantages of a square boxing ring, preventing fighters from getting stuck in corners.",
    "Brazilian Jiu-Jitsu rose to global prominence after Royce Gracie won the first, second, and fourth UFC tournaments."
]

TECH_JOKES = [
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I'd tell you a joke about UDP, but you probably wouldn't get it."
]

PYTHON_TIPS = [
    "Use list comprehensions to write cleaner and faster code: `[x**2 for x in range(10)]`",
    "Did you know? You can swap two variables easily without a temp variable: `a, b = b, a`",
    "Use `enumerate()` if you need both the index and the value while looping through an iterable."
]

# Role Categories
ALL_DISTRO_ROLES = [
    1521868543799328808, 1521870392472502344, 1521870674669338654, 1521871074994950295, 1521871078308184074,
    1521870173861056655, 1521871399403393044, 1521871679368986655, 1521871896117776468,
    1521870110552227910, 1521868791942742026, 1521871613958819860, 1521871816321404969, 1521872016901406720,
    1521870225228955798, 1521872173688422420, 1521872360393670819, 1521872534117679206, 1521872635968098344,
    1521872683803873432, 1521872759691542588, 1521873026776301608, 1521873129868365964
]
ALL_GPU_ROLES = [1521879270530486414, 1521879224951246928, 1521879315648614410]

# In-Memory Databases
xp_db = {}
warning_db = {}
user_message_cache = {} # For Spam Protection

# ==========================================
# 4. HELPER FUNCTIONS & ENGINE
# ==========================================
def add_xp(user_id, amount):
    current_time = time.time()
    if user_id not in xp_db:
        xp_db[user_id] = {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "last_msg": 0, "level": 1}
    
    # 60-Second Cooldown
    if current_time - xp_db[user_id]["last_msg"] >= 60:
        xp_db[user_id]["total"] += amount
        xp_db[user_id]["daily"] += amount
        xp_db[user_id]["weekly"] += amount
        xp_db[user_id]["monthly"] += amount
        xp_db[user_id]["last_msg"] = current_time
        
        # Level Up Algorithm (Harder Curve: 50 XP per level requirement, low gain makes it take hours)
        current_xp = xp_db[user_id]["total"]
        next_level_xp = xp_db[user_id]["level"] * 50
        if current_xp >= next_level_xp:
            xp_db[user_id]["level"] += 1
            return True
    return False

# ==========================================
# 5. INTERACTIVE DROPDOWN ROLES (GUI VIEW)
# ==========================================
class DistroSelect(Select):
    def __init__(self, placeholder, options, custom_id):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = int(self.values[0])
        role = interaction.guild.get_role(selected_role_id)
        
        if not role:
            return await interaction.response.send_message("❌ Role not found on the server!", ephemeral=True)
            
        # Check and remove existing distro roles
        roles_to_remove = [r for r in interaction.user.roles if r.id in ALL_DISTRO_ROLES and r.id != selected_role_id]
        if roles_to_remove:
            await interaction.user.remove_roles(*roles_to_remove)
            
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ You have successfully claimed the `{role.name}` role! (Previous distro role removed)", ephemeral=True)

class GPUSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="NVIDIA Graphics", value="1521879270530486414", emoji="🟩"),
            discord.SelectOption(label="AMD Graphics", value="1521879224951246928", emoji="🟥"),
            discord.SelectOption(label="Intel Graphics", value="1521879315648614410", emoji="🟦")
        ]
        super().__init__(placeholder="Select Your Graphics Driver", min_values=1, max_values=1, options=options, custom_id="gpu_select")

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = int(self.values[0])
        role = interaction.guild.get_role(selected_role_id)
        
        if not role:
            return await interaction.response.send_message("❌ Role not found on the server!", ephemeral=True)
            
        # Check and remove existing GPU roles
        roles_to_remove = [r for r in interaction.user.roles if r.id in ALL_GPU_ROLES and r.id != selected_role_id]
        if roles_to_remove:
            await interaction.user.remove_roles(*roles_to_remove)
            
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ You have successfully claimed the `{role.name}` driver role! (Previous GPU role removed)", ephemeral=True)

class RolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # 1. Arch / Arch-based
        arch_opts = [
            discord.SelectOption(label="Arch Linux", value="1521868543799328808"),
            discord.SelectOption(label="Manjaro", value="1521870392472502344"),
            discord.SelectOption(label="EndeavourOS", value="1521870674669338654"),
            discord.SelectOption(label="Garuda Linux", value="1521871074994950295"),
            discord.SelectOption(label="Artix Linux", value="1521871078308184074")
        ]
        self.add_item(DistroSelect(placeholder="Arch / Arch-based", options=arch_opts, custom_id="arch_menu"))
        
        # 2. Debian / Debian-based
        debian_opts = [
            discord.SelectOption(label="Debian", value="1521870173861056655"),
            discord.SelectOption(label="Kali Linux", value="1521871399403393044"),
            discord.SelectOption(label="MX Linux", value="1521871679368986655"),
            discord.SelectOption(label="Deepin", value="1521871896117776468")
        ]
        self.add_item(DistroSelect(placeholder="Debian / Debian-based", options=debian_opts, custom_id="debian_menu"))

        # 3. Ubuntu / Ubuntu-based
        ubuntu_opts = [
            discord.SelectOption(label="Ubuntu", value="1521870110552227910"),
            discord.SelectOption(label="Linux Mint", value="1521868791942742026"),
            discord.SelectOption(label="Pop!_OS", value="1521871613958819860"),
            discord.SelectOption(label="Zorin OS", value="1521871816321404969"),
            discord.SelectOption(label="Elementary OS", value="1521872016901406720")
        ]
        self.add_item(DistroSelect(placeholder="Ubuntu / Ubuntu-based", options=ubuntu_opts, custom_id="ubuntu_menu"))

        # 4. Independent
        indep_opts = [
            discord.SelectOption(label="Gentoo", value="1521870225228955798"),
            discord.SelectOption(label="Nobara", value="1521872173688422420"),
            discord.SelectOption(label="Fedora", value="1521872360393670819"),
            discord.SelectOption(label="Red Star OS", value="1521872534117679206"),
            discord.SelectOption(label="Void Linux", value="1521872635968098344"),
            discord.SelectOption(label="NixOS", value="1521872683803873432"),
            discord.SelectOption(label="Alpine Linux", value="1521872759691542588"),
            discord.SelectOption(label="openSUSE", value="1521873026776301608"),
            discord.SelectOption(label="Slackware", value="1521873129868365964")
        ]
        self.add_item(DistroSelect(placeholder="Independent", options=indep_opts, custom_id="indep_menu"))

        # 5. Graphics Driver
        self.add_item(GPUSelect())

# ==========================================
# 6. BG LOOP TASKS (SCHEDULER)
# ==========================================
@tasks.loop(minutes=60)
async def hourly_reminder():
    await bot.wait_until_ready()
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if channel:
        chosen_rule = random.choice(SERVER_RULES)
        embed = discord.Embed(
            title="🐧 AdminPingu Hourly Rule Reminder",
            description=f"It is my absolute duty to maintain order and remind you of our server rules!\n\n**Always Remember:** {chosen_rule}",
            color=discord.Color.dark_teal()
        )
        await channel.send(embed=embed)

@tasks.loop(hours=24)
async def reset_daily_xp():
    for user_id in xp_db:
        xp_db[user_id]["daily"] = 0

# ==========================================
# 7. BOT LIFE-CYCLE & AUTOMATION EVENTS
# ==========================================
@bot.event
async def on_ready():
    print(f'==========================================')
    print(f'🤖 Bot Is Online: {bot.user.name}')
    print(f'🚀 Engine Status: SYNTAX OK & PRODUCTION READY')
    print(f'==========================================')
    await bot.change_presence(activity=discord.Game(name="Managing Linux Servers | ?help"))
    hourly_reminder.start()
    reset_daily_xp.start()
    bot.add_view(RolesView()) # Make view persistent

@bot.event
async def on_member_join(member):
    # Auto-role assigned on join
    role = member.guild.get_role(USER_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"Auto-role assignment error: {e}")

async def apply_warning(member, reason, guild):
    if member.id not in warning_db:
        warning_db[member.id] = 0
    warning_db[member.id] += 1
    total_warns = warning_db[member.id]
    
    warn_channel = bot.get_channel(WARNINGS_CHANNEL_ID)
    if warn_channel:
        embed = discord.Embed(title="⚠️ System Warning Issued", color=discord.Color.orange())
        embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warnings", value=f"**{total_warns}/3**", inline=False)
        await warn_channel.send(embed=embed)
        
    if total_warns >= 3:
        try:
            await member.ban(reason="Automated Ban - Exceeded 3 Active Warnings Limit.")
            if warn_channel:
                await warn_channel.send(f"🚨 {member.mention} has been banned from the server for exceeding the 3-warning limit!")
            warning_db[member.id] = 0
        except:
            pass

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    # A. SPAM FILTER (Exempts Mods and Admins)
    is_mod = message.author.guild_permissions.manage_messages
    if not is_mod:
        if message.author.id not in user_message_cache:
            user_message_cache[message.author.id] = []
        
        user_message_cache[message.author.id].append(message.content.lower())
        
        if len(user_message_cache[message.author.id]) > 3:
            user_message_cache[message.author.id].pop(0)
            
        if len(user_message_cache[message.author.id]) == 3 and len(set(user_message_cache[message.author.id])) == 1:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, please stop spamming!", delete_after=5)
            await apply_warning(message.author, "Spam / Flooding the chat", message.guild)
            user_message_cache[message.author.id] = [] # Clear cache
            return

    # B. PROFANITY FILTER
    msg_content = message.content.lower()
    if any(word in msg_content for word in PROFANITY_LIST):
        try:
            await message.delete()
            await message.channel.send(f"Hey {message.author.mention}, swearing is strictly prohibited on this server!", delete_after=5)
            await apply_warning(message.author, f"Profanity used: ||{message.content}||", message.guild)
            return  # Cancel XP gain
        except Exception as e:
            print(f"Profanity filter error: {e}")

    # C. XP ENGINE TRIGGER (Very Slow XP Gain: 5 to 10 XP)
    gained = random.randint(5, 10)
    leveled_up = add_xp(message.author.id, gained)
    if leveled_up:
        new_level = xp_db[message.author.id]['level']
        level_channel = bot.get_channel(LEVEL_LOG_CHANNEL_ID)
        
        if level_channel:
            await level_channel.send(f"🎉 Congratulations {message.author.mention}! You've reached **Level {new_level}** by chatting!")
            
        # Media Permission Check
        if new_level == 20:
            media_role = message.guild.get_role(MEDIA_ROLE_ID)
            if media_role:
                await message.author.add_roles(media_role)
                if level_channel:
                    await level_channel.send(f"📸 {message.author.mention} has reached level 20 and earned the **Media Permission** role!")

    await bot.process_commands(message)

# ==========================================
# 8. COMMAND MATRIX
# ==========================================
@bot.command()
@commands.has_permissions(administrator=True)
async def roles(ctx):
    """Prints the Dropdown Role Selection panel."""
    role_embed = discord.Embed(
        title="Choose Your Primary Distro & Graphics Driver", 
        description="Use the menus below to select your primary Linux distribution and GPU driver. You can only have 1 role per category.", 
        color=discord.Color.dark_theme()
    )
    await ctx.send(embed=role_embed, view=RolesView())

@bot.command()
async def stats(ctx, member: discord.Member = None):
    """Displays user level card."""
    member = member or ctx.author
    if member.id not in xp_db:
        xp_db[member.id] = {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "level": 1, "last_msg": 0}
        
    data = xp_db[member.id]
    next_xp = data["level"] * 50
    
    embed = discord.Embed(title=f"📊 {member.name}'s Server Statistics", color=discord.Color.purple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Current Level", value=f"`Level {data['level']}`", inline=True)
    embed.add_field(name="Total XP", value=f"`{data['total']} / {next_xp} XP`", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def warning(ctx, member: discord.Member, *, reason="Manual Warning"):
    """Adds a manual warning to a user."""
    await apply_warning(member, reason, ctx.guild)
    await ctx.send(f"✅ A warning has been issued to {member.mention}. Details have been sent to the warnings channel.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Bans a member from the server."""
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.name} has been successfully banned. Reason: {reason if reason else 'Not specified'}")

# --- 12 NEW FUN & INFO COMMANDS ---

@bot.command()
async def weather(ctx, *, city: str = "Izmir"):
    """Fetches text-based weather for a given city."""
    async with aiohttp.ClientSession() as session:
        # Using wttr.in with format=3 (location, weather icon, temperature)
        async with session.get(f'https://wttr.in/{city}?format=3') as resp:
            if resp.status == 200:
                text = await resp.text()
                await ctx.send(f"🌤️ **Weather Report:** `{text.strip()}`")
            else:
                await ctx.send("❌ Could not fetch weather data right now. Try again later.")

@bot.command()
async def tankfact(ctx):
    """Sends a random WW1/WW2 tank fact."""
    fact = random.choice(TANK_FACTS)
    embed = discord.Embed(title="🪖 Historical Tank Fact", description=fact, color=discord.Color.dark_gray())
    await ctx.send(embed=embed)

@bot.command()
async def mmafact(ctx):
    """Sends a random MMA/UFC fact."""
    fact = random.choice(MMA_FACTS)
    embed = discord.Embed(title="🥊 MMA & Combat Sports Fact", description=fact, color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command()
async def pythontip(ctx):
    """Sends a random Python programming tip."""
    tip = random.choice(PYTHON_TIPS)
    embed = discord.Embed(title="🐍 Daily Python Tip", description=tip, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command()
async def tea(ctx, member: discord.Member = None):
    """Serves a nice virtual cup of Sri Lankan tea."""
    member = member or ctx.author
    await ctx.send(f"☕ {member.mention}, here is a freshly brewed cup of strong, unsweetened Sri Lankan tea for you. Enjoy!")

@bot.command()
async def ping(ctx):
    """Shows the bot's latency."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency is `{latency}ms`.")

@bot.command()
async def serverinfo(ctx):
    """Displays information about the server."""
    guild = ctx.guild
    embed = discord.Embed(title=f"🏰 {guild.name} Server Info", color=discord.Color.blue())
    embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="Member Count", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="Created On", value=f"`{guild.created_at.strftime('%Y-%m-%d')}`", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """Displays a user's avatar."""
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ {member.name}'s Avatar", color=discord.Color.dark_magenta())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def coinflip(ctx):
    """Flips a coin."""
    choices = ["Heads", "Tails"]
    result = random.choice(choices)
    await ctx.send(f"🪙 You flipped a coin and got: **{result}**")

@bot.command()
async def diceroll(ctx, sides: int = 6):
    """Rolls a dice with the given number of sides."""
    if sides < 2:
        return await ctx.send("❌ A dice needs at least 2 sides!")
    result = random.randint(1, sides)
    await ctx.send(f"🎲 You rolled a `{sides}`-sided dice and got: **{result}**")

@bot.command(name="8ball")
async def magic_ball(ctx, *, question: str):
    """Answers a yes/no question."""
    responses = [
        "It is certain.", "Without a doubt.", "Yes, definitely.", 
        "Ask again later.", "Cannot predict now.", 
        "Don't count on it.", "My sources say no.", "Very doubtful."
    ]
    await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {random.choice(responses)}")

@bot.command()
async def joke(ctx):
    """Sends a random programming/tech joke."""
    joke_text = random.choice(TECH_JOKES)
    await ctx.send(f"😂 {joke_text}")

@bot.command()
async def randomlinux(ctx):
    """Random terminal command."""
    selected = random.choice(LINUX_COMMANDS)
    embed = discord.Embed(
        title=f"🐧 Linux Terminal Library",
        description=f"**Command:** `{selected['cmd']}`\n\n**Description:** {selected['desc']}",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def gif(ctx):
    """Sends a random Linux meme or gif."""
    gif_url = random.choice(LINUX_GIFS)
    embed = discord.Embed(title="🐧 Random Linux Meme/Gif", color=discord.Color.green())
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    """Displays all available commands."""
    embed = discord.Embed(title="🐧 AdminPingu Commands Overview", color=discord.Color.dark_green())
    
    embed.add_field(name="🛡️ Moderation", value="`?warning <user>`\n`?ban <user>`", inline=True)
    embed.add_field(name="📊 Analytics & Setup", value="`?stats [user]`\n`?roles` (Admin)\n`?serverinfo`", inline=True)
    embed.add_field(name="🐧 Linux & Tech", value="`?randomlinux`\n`?gif`\n`?pythontip`\n`?joke`", inline=True)
    embed.add_field(name="🎲 Fun & Games", value="`?coinflip`\n`?diceroll [sides]`\n`?8ball <question>`", inline=True)
    embed.add_field(name="🌍 Info & Culture", value="`?weather [city]`\n`?tankfact`\n`?mmafact`\n`?tea`", inline=True)
    embed.add_field(name="🛠️ Utility", value="`?ping`\n`?avatar [user]`\n`?help`", inline=True)
    
    embed.set_footer(text="Parameters in [brackets] are optional, <angle brackets> are required.")
    await ctx.send(embed=embed)

# ==========================================
# 9. GLOBAL EXCEPTION HANDLER
# ==========================================
@bot.listen()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **ERROR: You lack the necessary privileges!**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **ERROR: Missing argument parameters! Try typing `?help`**")
    else:
        print(f"Unhandled system error: {error}")

# BOOTUP SEQUENCE
keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
