import discord
from discord.ext import commands, tasks
from discord.ui import Select, View
from flask import Flask
from threading import Thread
import random
import time
import datetime
import os
import aiohttp
import asyncio  # Added for 2-step verification timeout handling

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
LOG_CHANNEL_ID = 123456789012345678       
WARNINGS_CHANNEL_ID = 1521880436270301354 
LEVEL_LOG_CHANNEL_ID = 1521880096854769785
REMINDER_CHANNEL_ID = 123456789012345678  # Default, can be updated via ?messagesendadminpingu

USER_ROLE_ID = 1510547520273649704        
MEDIA_ROLE_ID = 1521875919864856714       

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
    {"cmd": "ls", "desc": "Used to list directory contents. It is just like taking a quick look at the items inside a room!"},
    {"cmd": "cd", "desc": "Allows you to navigate between directories. It essentially teleports you from one path to another!"},
    {"cmd": "pwd", "desc": "Prints the full path of the current working directory."},
    {"cmd": "sudo", "desc": "Runs a command with the elevated security privileges of the system administrator 'root'."},
    {"cmd": "htop", "desc": "A much sleeker, colorful, and highly interactive modern upgrade to the classic 'top' command!"}
]

SERVER_RULES = [
    {"title": "Hate Speech and Discrimination", "desc": "Racism, ethnic discrimination, and hate speech of any kind are strictly prohibited.", "penalty": "Permanent Ban"},
    {"title": "Unsolicited Advertising", "desc": "Sharing advertising or invite links in channels or via DMs without permission is prohibited.", "penalty": "Mute (Timeout)"},
    {"title": "Harassment and Discrimination", "desc": "Homophobia, sexism, and any discrimination against marginalized groups are strictly prohibited.", "penalty": "Permanent Ban"},
    {"title": "Disrupting Peace", "desc": "Harassing, provoking, or annoying members, or disrupting personal peace is prohibited.", "penalty": "Warning + Mute"},
    {"title": "Spreading False Information", "desc": "Spreading fake news or misinformation to manipulate members is prohibited.", "penalty": "Warning"},
    {"title": "Excessive Trolling", "desc": "Engaging in excessive trolling that derails channel purposes or ruins server peace is prohibited.", "penalty": "Warning + Mute"},
    {"title": "Toxic Language", "desc": "Excessive swearing, toxic language, and personal insults are strictly prohibited.", "penalty": "Mute"},
    {"title": "NSFW Content", "desc": "Posting NSFW, 18+ content, gore, or graphic violence is strictly prohibited.", "penalty": "Permanent Ban"},
    {"title": "Impersonation", "desc": "Impersonating another server member, staff member, or a bot is strictly prohibited.", "penalty": "Warning + Mute"},
    {"title": "Spam and Flooding", "desc": "Mass mentioning, spamming, and flooding channels with messages are prohibited.", "penalty": "Mute"}
]

LINUX_GIFS = [
    "https://media.giphy.com/media/LmNwrBhejkK9EFP504/giphy.gif",
    "https://media.giphy.com/media/i8XwYIrNqMEA8/giphy.gif",
    "https://media.giphy.com/media/VbKLOdvYXBEgw/giphy.gif",
    "https://media.tenor.com/7D-R9eYf6W8AAAAC/linux-penguin.gif",
    "https://media.tenor.com/V-nF03F5h20AAAAC/linux-arch.gif"
]

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
user_message_cache = {} 

# ==========================================
# 4. HELPER FUNCTIONS & ENGINE
# ==========================================
def add_xp(user_id, amount):
    current_time = time.time()
    if user_id not in xp_db:
        xp_db[user_id] = {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "last_msg": 0, "level": 1}
    
    if current_time - xp_db[user_id]["last_msg"] >= 60:
        xp_db[user_id]["total"] += amount
        xp_db[user_id]["daily"] += amount
        xp_db[user_id]["weekly"] += amount
        xp_db[user_id]["monthly"] += amount
        xp_db[user_id]["last_msg"] = current_time
        
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
            
        roles_to_remove = [r for r in interaction.user.roles if r.id in ALL_DISTRO_ROLES and r.id != selected_role_id]
        if roles_to_remove:
            await interaction.user.remove_roles(*roles_to_remove)
            
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ You have successfully claimed the `{role.name}` role!", ephemeral=True)

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
            
        roles_to_remove = [r for r in interaction.user.roles if r.id in ALL_GPU_ROLES and r.id != selected_role_id]
        if roles_to_remove:
            await interaction.user.remove_roles(*roles_to_remove)
            
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ You have successfully claimed the `{role.name}` driver role!", ephemeral=True)

class RolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        arch_opts = [
            discord.SelectOption(label="Arch Linux", value="1521868543799328808"),
            discord.SelectOption(label="Manjaro", value="1521870392472502344"),
            discord.SelectOption(label="EndeavourOS", value="1521870674669338654"),
            discord.SelectOption(label="Garuda Linux", value="1521871074994950295"),
            discord.SelectOption(label="Artix Linux", value="1521871078308184074")
        ]
        self.add_item(DistroSelect(placeholder="Arch / Arch-based", options=arch_opts, custom_id="arch_menu"))
        
        debian_opts = [
            discord.SelectOption(label="Debian", value="1521870173861056655"),
            discord.SelectOption(label="Kali Linux", value="1521871399403393044"),
            discord.SelectOption(label="MX Linux", value="1521871679368986655"),
            discord.SelectOption(label="Deepin", value="1521871896117776468")
        ]
        self.add_item(DistroSelect(placeholder="Debian / Debian-based", options=debian_opts, custom_id="debian_menu"))

        ubuntu_opts = [
            discord.SelectOption(label="Ubuntu", value="1521870110552227910"),
            discord.SelectOption(label="Linux Mint", value="1521868791942742026"),
            discord.SelectOption(label="Pop!_OS", value="1521871613958819860"),
            discord.SelectOption(label="Zorin OS", value="1521871816321404969"),
            discord.SelectOption(label="Elementary OS", value="1521872016901406720")
        ]
        self.add_item(DistroSelect(placeholder="Ubuntu / Ubuntu-based", options=ubuntu_opts, custom_id="ubuntu_menu"))

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
        self.add_item(GPUSelect())

# ==========================================
# 6. BG LOOP TASKS (SCHEDULER - 30 MINS)
# ==========================================
@tasks.loop(minutes=30)
async def half_hourly_reminder():
    await bot.wait_until_ready()
    global REMINDER_CHANNEL_ID
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if channel:
        rule = random.choice(SERVER_RULES)
        embed = discord.Embed(
            title="🐧 AdminPingu Automated Security Reminder",
            description=f"To protect system integrity, here is a core directive validation:\n\n"
                        f"🔹 **Rule:** {rule['title']}\n"
                        f"📝 **Details:** {rule['desc']}\n"
                        f"⚡ **Penalty:** `{rule['penalty']}`",
            color=discord.Color.red()
        )
        embed.set_footer(text="AdminPingu System Protection Protocol Active.")
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
    half_hourly_reminder.start()
    reset_daily_xp.start()
    bot.add_view(RolesView())

@bot.event
async def on_member_join(member):
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
                await warn_channel.send(f"🚨 {member.mention} has been permanently banned for exceeding the 3-warning limit!")
            warning_db[member.id] = 0
        except:
            pass

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    is_mod = message.author.guild_permissions.manage_messages
    if not is_mod:
        # SPAM FILTER
        if message.author.id not in user_message_cache:
            user_message_cache[message.author.id] = []
        
        user_message_cache[message.author.id].append(message.content.lower())
        
        if len(user_message_cache[message.author.id]) > 3:
            user_message_cache[message.author.id].pop(0)
            
        if len(user_message_cache[message.author.id]) == 3 and len(set(user_message_cache[message.author.id])) == 1:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, please stop spamming!", delete_after=5)
            await apply_warning(message.author, "Spam / Flooding the chat", message.guild)
            user_message_cache[message.author.id] = [] 
            return

        # PROFANITY FILTER
        msg_content = message.content.lower()
        if any(word in msg_content for word in PROFANITY_LIST):
            try:
                await message.delete()
                await message.channel.send(f"Hey {message.author.mention}, swearing is strictly prohibited!", delete_after=5)
                await apply_warning(message.author, f"Profanity filtering system trigger.", message.guild)
                return  
            except Exception as e:
                print(f"Profanity filter error: {e}")

    gained = random.randint(5, 10)
    leveled_up = add_xp(message.author.id, gained)
    if leveled_up:
        new_level = xp_db[message.author.id]['level']
        level_channel = bot.get_channel(LEVEL_LOG_CHANNEL_ID)
        
        if level_channel:
            await level_channel.send(f"🎉 Congratulations {message.author.mention}! You've reached **Level {new_level}**!")
            
        if new_level == 20:
            media_role = message.guild.get_role(MEDIA_ROLE_ID)
            if media_role:
                await message.author.add_roles(media_role)
                if level_channel:
                    await level_channel.send(f"📸 {message.author.mention} reached level 20 and unlocked **Media Permissions**!")

    await bot.process_commands(message)

# ==========================================
# 8. COMMAND MATRIX (COMPLETELY IN ENGLISH)
# ==========================================

# --- CONFIG COMMAND ---
@bot.command()
@commands.has_permissions(administrator=True)
async def messagesendadminpingu(ctx, channel: discord.TextChannel = None):
    """Sets the channel for half-hourly rule reminders."""
    global REMINDER_CHANNEL_ID
    target_channel = channel or ctx.channel
    REMINDER_CHANNEL_ID = target_channel.id
    await ctx.send(f"✅ **Success:** AdminPingu automated rules will now be broadcasted to {target_channel.mention} every 30 minutes.")

# --- ADMINISTRATIVE ROOT OPERATIONS ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx):
    """Clears all messages in the channel with a strict 2-step verification."""
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'y'

    await ctx.send("⚠️ **WARNING: CORE SYSTEM PURGE INITIATED** ⚠️\nYou are about to delete **ALL** messages in this channel.\nType `y` within 30 seconds to proceed.")
    
    try:
        await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("❌ **Timeout:** Channel wipe sequence aborted due to inactivity.")

    await ctx.send("🚨 **FINAL SECURITY CHECK:** 🚨\nThis action is **IRREVERSIBLE**. Type `y` one last time to authorize full data deletion.")
    
    try:
        await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("❌ **Timeout:** Channel wipe sequence aborted due to inactivity.")

    await ctx.send("🔄 **Authorization Accepted:** Executing complete channel purge protocol...", delete_after=3)
    
    try:
        deleted = await ctx.channel.purge(limit=None)
        msg = await ctx.send(f"✅ **System Wipe Complete:** Successfully deleted `{len(deleted)}` messages from the database.")
        await asyncio.sleep(5)
        await msg.delete()
    except Exception as e:
        await ctx.send(f"❌ **System Error during purge:** {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def roles(ctx):
    """Prints the Dropdown Role Selection panel."""
    role_embed = discord.Embed(
        title="Choose Your Primary Distro & Graphics Driver", 
        description="Use the menus below to select your configurations. Max 1 role per category.", 
        color=discord.Color.dark_theme()
    )
    await ctx.send(embed=role_embed, view=RolesView())

@bot.command()
@commands.has_permissions(manage_channels=True)
async def sudolock(ctx):
    """Locks down the current text channel."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(
        title="🔒 Administrative Channel Lockdown Initiated",
        description=f"This channel has been successfully locked by root permissions ({ctx.author.mention}).",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def sudounlock(ctx):
    """Unlocks the current text channel."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    embed = discord.Embed(
        title="🔓 Administrative Channel Lockdown Revoked",
        description=f"This channel has been completely unlocked by root permissions ({ctx.author.mention}).",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, hours: int = 1, *, reason="No reason specified"):
    """Silences a user with a customized timeout duration."""
    duration = datetime.timedelta(hours=hours)
    try:
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="🤫 User Muted Successfully", color=discord.Color.orange())
        embed.add_field(name="Target Entity", value=member.mention, inline=True)
        embed.add_field(name="Duration", value=f"`{hours} Hours`", inline=True)
        embed.add_field(name="Reason", value=f"`{reason}`", inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ **System Failure:** Unable to apply structural timeout. Reason: {e}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    """Lifts an active timeout structural restriction from a user."""
    try:
        await member.timeout(None)
        await ctx.send(f"✅ **Success:** Mute restriction lifted from user {member.mention}.")
    except Exception as e:
        await ctx.send(f"❌ **System Failure:** Could not remove restriction. Reason: {e}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warning(ctx, member: discord.Member, *, reason="Manual Override Warning"):
    """Adds a system manual warning mark."""
    await apply_warning(member, reason, ctx.guild)
    await ctx.send(f"✅ Warning tracking successfully loaded for {member.mention}.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No structural reason specified"):
    """Bans a target member from the infrastructure server."""
    await member.ban(reason=reason)
    await ctx.send(f"🔨 **Banned Entity:** `{member.name}` has been banned. Reason: `{reason}`")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    """Revokes an existing global user infrastructure ban."""
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ **Success:** Infrastructure access ban lifted for user: `{user.name}` ({user_id}).")
    except discord.NotFound:
        await ctx.send("❌ **Error:** Target ban index registry not found.")
    except Exception as e:
        await ctx.send(f"❌ **Error:** Operation aborted. Details: {e}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ipban(ctx, member: discord.Member):
    """Simulated structural network IP level ban execution sequence."""
    mock_ip = f"{random.randint(12, 192)}.{random.randint(10, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    embed = discord.Embed(title="⚡ Automated Deep Network IP-Ban Simulation Sequence", color=discord.Color.purple())
    embed.add_field(name="Target Virtual Machine", value=member.mention, inline=True)
    embed.add_field(name="Intercepted Gateway Route", value=f"`{mock_ip}`", inline=True)
    embed.add_field(name="Firewall Status", value="`Dropping all active sessions packet streams...`", inline=False)
    await ctx.send(embed=embed)

# --- SYSTEM EXPERIENCE ANALYTICS ---
@bot.command()
async def stats(ctx, member: discord.Member = None):
    """Displays highly detailed user level card analytics with an automated progress bar."""
    member = member or ctx.author
    if member.id not in xp_db:
        xp_db[member.id] = {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "level": 1, "last_msg": 0}
        
    data = xp_db[member.id]
    next_xp = data["level"] * 50
    current_xp = data["total"]
    
    # Progress bar calculation
    percentage = min(current_xp / next_xp, 1.0)
    bar_length = 10
    filled_blocks = int(percentage * bar_length)
    empty_blocks = bar_length - filled_blocks
    progress_bar = "█" * filled_blocks + "░" * empty_blocks

    embed = discord.Embed(title=f"📊 {member.name}'s Core Matrix Analytics", color=discord.Color.purple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="System Rank Access", value=f"`Level {data['level']}`", inline=True)
    embed.add_field(name="Experience Stream Index", value=f"`{current_xp} / {next_xp} XP`", inline=True)
    embed.add_field(name="Matrix Calibration Progress", value=f"`[{progress_bar}] {int(percentage * 100)}%`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def leaderstats(ctx):
    """Lists the top 15 highest-ranked matrix members."""
    if not xp_db:
        return await ctx.send("❌ **Error:** Structural database empty. No records tracked yet.")
        
    sorted_users = sorted(xp_db.items(), key=lambda x: x[1]['total'], reverse=True)[:15]
    leaderboard_str = ""
    
    for index, (user_id, stats_data) in enumerate(sorted_users, start=1):
        user_obj = ctx.guild.get_member(user_id)
        name = user_obj.name if user_obj else f"Unknown User ({user_id})"
        leaderboard_str += f"`#{index:02}` **{name}** - Level {stats_data['level']} ({stats_data['total']} XP)\n"
        
    embed = discord.Embed(title="🏆 Server Communication Matrix - Top 15 Leaderboard", description=leaderboard_str, color=discord.Color.gold())
    await ctx.send(embed=embed)

# --- LINUX TERMINAL FUN CORE ---
@bot.command()
async def randomlinux(ctx):
    """Teaches a random core system terminal command architecture instruction."""
    selected = random.choice(LINUX_COMMANDS)
    embed = discord.Embed(
        title=f"🐧 Linux System Engine Terminal Documentation",
        description=f"📁 **Command Instruction:** `{selected['cmd']}`\n\n💡 **Operation Metric:** {selected['desc']}",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def whoami(ctx):
    """Runs a simulated authentication core signature scan sequence validation."""
    roles_list = [r.name for r in ctx.author.roles if r.name != "@everyone"]
    roles_str = ", ".join(roles_list) if roles_list else "No assigned functional roles."
    
    embed = discord.Embed(title="💻 Root Authentication Verification System: whoami", color=discord.Color.dark_grey())
    embed.add_field(name="Current Secure Shell Identity", value=f"`{ctx.author.name}#{ctx.author.discriminator}`", inline=True)
    embed.add_field(name="Host Unique Sequence UID ID", value=f"`{ctx.author.id}`", inline=True)
    embed.add_field(name="Infrastructural Nodes Permissions Base", value=f"`Admin: {ctx.author.guild_permissions.administrator}`", inline=True)
    embed.add_field(name="Active Network Security Cleared Groups", value=f"```text\n{roles_str}```", inline=False)
    await ctx.send(embed=embed)

# --- THE WEATHER ENDPOINT OPTIMIZATION MIGRATION ---
@bot.command()
async def weather(ctx, *, city: str = ""):
    """Fetches text-based weather analytics. Correctly rejects blank executions."""
    if not city.strip():
        await ctx.send("❌ **Error:** No city selected! Please specify a location (e.g., `?weather London`).")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://wttr.in/{city}?format=3') as resp:
            if resp.status == 200:
                text = await resp.text()
                await ctx.send(f"🌤️ **Weather Report:** `{text.strip()}`")
            else:
                await ctx.send("❌ **System Fault:** Could not fetch standard weather telemetry array metrics right now.")

# --- COMPREHENSIVE FUN & UTILITY CORE UTILITIES ---
@bot.command()
async def tankfact(ctx):
    """Sends historical tank fact metrics."""
    fact = random.choice(TANK_FACTS)
    embed = discord.Embed(title="🪖 Historical Heavy Armored Core Fact", description=fact, color=discord.Color.dark_gray())
    await ctx.send(embed=embed)

@bot.command()
async def mmafact(ctx):
    """Sends combat sports technical trivia metrics."""
    fact = random.choice(MMA_FACTS)
    embed = discord.Embed(title="🥊 Combat Athletics & MMA Protocol Fact", description=fact, color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command()
async def pythontip(ctx):
    """Provides professional modern python compiler syntax tips."""
    tip = random.choice(PYTHON_TIPS)
    embed = discord.Embed(title="🐍 Core Python Programming Guideline Directive", description=tip, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command()
async def tea(ctx, member: discord.Member = None):
    """Serves high quality virtual cup of unsweetened Sri Lankan tea."""
    member = member or ctx.author
    await ctx.send(f"☕ {member.mention}, here is a freshly brewed cup of strong, unsweetened Sri Lankan tea for you. Enjoy the warmth!")

@bot.command()
async def ping(ctx):
    """Validates frame array link socket execution latencies."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Global Gateway Socket Network Latency is `{latency}ms`.")

@bot.command()
async def serverinfo(ctx):
    """Displays standard host node metrics array specs details."""
    guild = ctx.guild
    embed = discord.Embed(title=f"🏰 {guild.name} Node Registry Details", color=discord.Color.blue())
    embed.add_field(name="Infrastructure Hash Unique ID", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="Registered Active User Entities", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="Initialization Timestamp Date", value=f"`{guild.created_at.strftime('%Y-%m-%d')}`", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """Fetches high resolution display user graphics asset frame."""
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Display Node Target User Asset Reference: {member.name}", color=discord.Color.dark_magenta())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def coinflip(ctx):
    """Random coin outcome selection algorithm generator execution."""
    choices = ["Heads", "Tails"]
    await ctx.send(f"🪙 Execution sequence complete. Outcome: **{random.choice(choices)}**")

@bot.command()
async def diceroll(ctx, sides: int = 6):
    """Calculates numerical randomness distributions matrix bound arrays limits."""
    if sides < 2:
        return await ctx.send("❌ **Error Matrix Fault:** Minimum dimensional matrix requires at least 2 coordinate facets!")
    await ctx.send(f"🎲 Vector calculated on a `{sides}`-sided polyhedral module matrix. Result: **{random.randint(1, sides)}**")

@bot.command(name="8ball")
async def magic_ball(ctx, *, question: str):
    """Evaluates question parameters query strings to random probability matrix outputs."""
    responses = [
        "It is certain.", "Without a doubt.", "Yes, definitely.", 
        "Ask again later.", "Cannot predict now.", 
        "Don't count on it.", "My sources say no.", "Very doubtful."
    ]
    await ctx.send(f"🎱 **Evaluated Metric Query:** {question}\n**Matrix System Probability Response Output:** {random.choice(responses)}")

@bot.command()
async def joke(ctx):
    """Returns random tech development string jokes."""
    await ctx.send(f"😂 {random.choice(TECH_JOKES)}")

@bot.command()
async def gif(ctx):
    """Displays random penguin graphics data asset frames."""
    embed = discord.Embed(title="🐧 Selected System Environment Asset Render Graphic", color=discord.Color.green())
    embed.set_image(url=random.choice(LINUX_GIFS))
    await ctx.send(embed=embed)

# --- UNIFIED GLOBAL OVERVIEW HELP MANIFEST ---
@bot.command()
async def help(ctx):
    """Displays an extensive, beautifully categorized overview of all commands."""
    embed = discord.Embed(
        title="🐧 AdminPingu Total Master System Infrastructure Manual Overview", 
        description="Comprehensive list of modules and kernel execution sequences. All processes are fully active.",
        color=discord.Color.dark_green()
    )
    
    embed.add_field(
        name="🛡️ Administrative Root Operations", 
        value="`?roles` - Deployment configuration dashboard\n"
              "`?sudolock` - Lockdown local texting channels\n"
              "`?sudounlock` - Open locked down channel lanes\n"
              "`?mute <user> [h]` - Silence entity via structural timeout\n"
              "`?unmute <user>` - Lift channel silences restrictions\n"
              "`?clear` - Execute 2-step verification massive channel purge\n"
              "`?warning <user> [reason]` - Apply warning registry indices\n"
              "`?ban <user> [reason]` - Purge malicious entities permanently\n"
              "`?unban <id>` - Restore infrastructure privileges access rights\n"
              "`?ipban <user>` - Emulate a network infrastructure firewall routing ban", 
        inline=False
    )
    
    embed.add_field(
        name="📊 Analytics & Setup Configuration Metrics", 
        value="`?stats [user]` - Visual representation metric ranking database profiles\n"
              "`?leaderstats` - Output communication ranking list leaderboards\n"
              "`?serverinfo` - Display underlying active local machine frame details\n"
              "`?messagesendadminpingu` - Configure specific reminder target channels", 
        inline=False
    )
    
    embed.add_field(
        name="🐧 Linux Terminal Fun Core & Tech Library Modules", 
        value="`?randomlinux` - Pull random manual operating instructions logs\n"
              "`?whoami` - Fetch secure shell structural identity matrix credentials\n"
              "`?pythontip` - Generate code optimization standard recommendations\n"
              "`?joke` - Retrieve random text programming joke lines\n"
              "`?gif` - Output random animated system graphic visual assets", 
        inline=False
    )
    
    embed.add_field(
        name="🌍 Info, Culture & Entertainment Nodes", 
        value="`?weather <city>` - Output real-time location forecasting telemetry\n"
              "`?tankfact` - Read heavy ground vehicular historically loaded logs\n"
              "`?mmafact` - Render athletic combat tournament history files\n"
              "`?tea` - Brew high quality virtual cup samples allocations", 
        inline=False
    )
    
    embed.add_field(
        name="🎲 Fun, Randomization Games & Utilities Array", 
        value="`?coinflip` - Run binary heads or tails randomization streams\n"
              "`?diceroll [sides]` - Return dynamic value from target multi-sided geometry dice\n"
              "`?8ball <question>` - Ask systemic future prediction evaluations questions\n"
              "`?ping` - Check socket communication performance latency frames\n"
              "`?avatar [user]` - Isolate high resolution user graphics imagery profiles", 
        inline=False
    )
    
    embed.set_footer(text="Parameters in [brackets] are optional, <angle brackets> are structurally required variables.")
    await ctx.send(embed=embed)

# ==========================================
# 9. GLOBAL EXCEPTION HANDLER
# ==========================================
@bot.listen()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **Access Denied:** You lack the necessary root system permissions required to execute this command structure!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Syntax Error:** Missing mandatory argument values! Consult structural guides via `?help` command sequences.")
    else:
        print(f"Unhandled system error: {error}")

# BOOTUP SEQUENCE
keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
