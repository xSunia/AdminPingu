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
import asyncio
import certifi
import feedparser
import re # ADDED: Profanity protection Regex library
from easy_pil import Editor, Canvas, Font, load_image_async
from motor.motor_asyncio import AsyncIOMotorClient

# ==========================================
# 1. RENDER KEEP-ALIVE SYSTEM
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "AdminPingu is OPERATIONAL."

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
# 3. DATA STRUCTURES, ROLES & CONFIGURATIONS
# ==========================================
LOG_CHANNEL_ID = 123456789012345678       
WARNINGS_CHANNEL_ID = 1521880436270301354 
LEVEL_LOG_CHANNEL_ID = 1521880096854769785
REMINDER_CHANNEL_ID = 123456789012345678  
EPIC_LEVEL_100_CHANNEL = 1510339895032418508 

USER_ROLE_ID = 1510547520273649704        
MEDIA_ROLE_ID = 1521875919864856714       

# LEVEL ROLE MATRIX
LEVEL_ROLES = {
    5: 1521923955127226609,
    10: 1521924218479186102,
    15: 1521924385647366210,
    20: 1521924589230358708,
    25: 1521924699926302740,
    50: 1521924800682004530,
    100: 1521924931875635210
}

# Old list remains, but regex system is now the primary filter
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
    1521872683803873432, 1521872759691542588, 1521873026776301608, 1521873129868365964,
    1521909235594825941, 1521909235594825999
]
ALL_GPU_ROLES = [1521879270530486414, 1521879224951246928, 1521879315648614410]

# ==========================================
# NEW SYSTEM ADDED: GLOBAL REGEX OPTIMIZATION
# ==========================================
# OPTIMIZATION: Compiling regex globally once to prevent high CPU load on every message
HEAVY_SWEAR_REGEX = re.compile(r"(?i)\b(dih|n[i1ı!l\|]+[gq9ğ]{2,}[e3a@]*r*|n[i1ı!l\|]+[gq9ğ]{2,}[a@]+)\b")
STRICT_BANNED_WORDS = {"nigger", "nigga", "nıgga", "nıgger", "n1gga"}

def is_heavy_swear(text):
    text = text.lower()
    
    # Stage 1: Exact Word and Letter Play Catching
    if HEAVY_SWEAR_REGEX.search(text):
        return True
        
    # Stage 2: Bypass Protection with Spaces and Symbols
    stripped = re.sub(r'[^a-zıiğüşöç]', '', text)
    for word in STRICT_BANNED_WORDS:
        if word in stripped:
            return True
            
    return False

# ==========================================
# 4. MONGODB DATABASE SETUP & OPTIMIZED CACHING
# ==========================================
MONGO_URI = os.environ.get("MONGO_URI")

try:
    mongo_client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = mongo_client["AdminPinguDB"]
    xp_collection = db["users_xp"]
    config_collection = db["server_config"] # New collection for News and Join channels
except Exception as e:
    print(f"MongoDB Initialization Error: {e}")

warning_db = {}
user_message_cache = {} 
# OPTIMIZATION: In-Memory Cache to prevent DB overload.
xp_cooldown_cache = {} 

# ==========================================
# 5. HELPER FUNCTIONS & ENGINE
# ==========================================
async def add_xp(user_id, amount):
    """Adds XP to user securely via MongoDB with high-load RAM caching."""
    try:
        current_time = time.time()
        
        # SUPER OPTIMIZATION: Check RAM first before hitting DB to prevent spam (1 min cooldown)
        if current_time - xp_cooldown_cache.get(user_id, 0) < 60:
            return False, None
            
        xp_cooldown_cache[user_id] = current_time # Update RAM Cache

        user_data = await xp_collection.find_one({"_id": user_id})
        if not user_data:
            user_data = {"_id": user_id, "total": 0, "daily": 0, "weekly": 0, "monthly": 0, "last_msg": 0, "level": 1}
        
        new_total = user_data["total"] + amount
        new_daily = user_data.get("daily", 0) + amount
        new_weekly = user_data.get("weekly", 0) + amount
        new_monthly = user_data.get("monthly", 0) + amount
        new_level = user_data["level"]
        
        leveled_up = False
        next_level_xp = new_level * 50
        
        if new_total >= next_level_xp:
            new_level += 1
            leveled_up = True
            
        await xp_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "total": new_total,
                "daily": new_daily,
                "weekly": new_weekly,
                "monthly": new_monthly,
                "last_msg": current_time,
                "level": new_level
            }},
            upsert=True
        )
        return leveled_up, new_level

    except Exception as e:
        print(f"Database access error (add_xp): {e}")
        return False, None

# ==========================================
# 6. INTERACTIVE DROPDOWN ROLES (GUI VIEW)
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
        
        # 1. Arch Based
        arch_opts = [
            discord.SelectOption(label="Arch Linux", value="1521868543799328808"),
            discord.SelectOption(label="Manjaro", value="1521870392472502344"),
            discord.SelectOption(label="EndeavourOS", value="1521870674669338654"),
            discord.SelectOption(label="Garuda Linux", value="1521871074994950295"),
            discord.SelectOption(label="Artix Linux", value="1521871078308184074")
        ]
        self.add_item(DistroSelect(placeholder="Arch / Arch-based", options=arch_opts, custom_id="arch_menu"))
        
        # 2. Debian & Ubuntu Based
        deb_ubu_opts = [
            discord.SelectOption(label="Debian", value="1521870173861056655"),
            discord.SelectOption(label="Ubuntu", value="1521870110552227910"),
            discord.SelectOption(label="Linux Mint", value="1521868791942742026"),
            discord.SelectOption(label="Kali Linux", value="1521871399403393044"),
            discord.SelectOption(label="Pop!_OS", value="1521871613958819860"),
            discord.SelectOption(label="Zorin OS", value="1521871816321404969"),
            discord.SelectOption(label="MX Linux", value="1521871679368986655"),
            discord.SelectOption(label="Deepin", value="1521871896117776468"),
            discord.SelectOption(label="Elementary OS", value="1521872016901406720")
        ]
        self.add_item(DistroSelect(placeholder="Debian & Ubuntu-based", options=deb_ubu_opts, custom_id="deb_ubu_menu"))

        # 3. Windows & FreeBSD
        win_bsd_opts = [
            discord.SelectOption(label="Windows 11", value="1521909235594825941", emoji="🪟"),
            discord.SelectOption(label="FreeBSD", value="1521909235594825999", emoji="😈")
        ]
        self.add_item(DistroSelect(placeholder="Windows & FreeBSD", options=win_bsd_opts, custom_id="win_bsd_menu"))

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
# 7. BG LOOP TASKS (SCHEDULER)
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
    try:
        await xp_collection.update_many({}, {"$set": {"daily": 0}})
    except Exception as e:
        print(f"Failed to reset daily XP: {e}")

@tasks.loop(hours=24)
async def daily_tech_news():
    """Fetches daily tech news and broadcasts to registered channels."""
    await bot.wait_until_ready()
    try:
        feed = feedparser.parse("https://www.omgubuntu.co.uk/feed")
        if not feed.entries:
            return
            
        entry = feed.entries[0]
        embed = discord.Embed(
            title=f"📰 {entry.title}", 
            url=entry.link, 
            description=entry.summary[:500] + "...", 
            color=discord.Color.teal()
        )
        embed.set_footer(text="Daily Linux & Tech Intelligence Network")
        
        # Try to find image
        if "media_content" in entry:
            embed.set_image(url=entry.media_content[0]["url"])

        configs = await config_collection.find({"news_channel": {"$exists": True}}).to_list(length=100)
        for conf in configs:
            guild = bot.get_guild(int(conf["_id"]))
            if guild:
                news_channel = guild.get_channel(int(conf["news_channel"]))
                if news_channel:
                    await news_channel.send("🚨 **System Scan Complete. Daily Tech Report Uploaded!** 🚨", embed=embed)
    except Exception as e:
        print(f"Tech news stream error: {e}")

# ==========================================
# 8. BOT LIFE-CYCLE & AUTOMATION EVENTS
# ==========================================
@bot.event
async def on_ready():
    print(f'==========================================')
    print(f'🤖 Bot Is Online: {bot.user.name}')
    print(f'🚀 Engine Status: READY AND OPERATIONAL')
    print(f'==========================================')
    await bot.change_presence(activity=discord.Game(name="Managing Linux Servers | ?help"))
    half_hourly_reminder.start()
    reset_daily_xp.start()
    daily_tech_news.start()
    bot.add_view(RolesView())

@bot.event
async def on_member_join(member):
    # AUTO ROLE
    role = member.guild.get_role(USER_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"Auto-role assignment error: {e}")

    # NEW SYSTEM ADDED: LINUX TERMINAL TEXT WELCOME
    terminal_channel = bot.get_channel(1510339895032418508)
    if terminal_channel:
        linux_msg = (
            f"```yaml\n"
            f"sys.log: [NEW_CONNECTION_ESTABLISHED]\n"
            f"user_id: {member.id}\n"
            f"status: authorized_entry\n"
            f"```\n"
            f"🔌 **Terminal Access Granted!** Welcome to the system, {member.mention}.\n\n"
            f"📂 **Review the Required Directories Before Starting:**\n"
            f"> 📜 Read the rules: <#1510343681985613905>\n"
            f"> 🏷️ Claim your roles: <#1521868274240065597>\n\n"
            f"*System optimization complete. You may now write in the main terminal.*"
        )
        await terminal_channel.send(linux_msg)

    # ORIGINAL: EASY-PIL VISUAL WELCOME SCREEN
    try:
        guild_config = await config_collection.find_one({"_id": str(member.guild.id)})
        if guild_config and "join_channel" in guild_config:
            join_channel = member.guild.get_channel(int(guild_config["join_channel"]))
            
            if join_channel:
                background = Editor(Canvas((800, 250), color="#1e1e2e"))
                
                # Terminal UI Design
                background.rectangle((0, 0), width=800, height=40, color="#11111b")
                background.text((20, 10), "root@adminpingu:~# ./accept_connection.sh", font=Font.poppins(size=18), color="#a6e3a1")
                
                # Avatar
                avatar_image = await load_image_async(str(member.display_avatar.url))
                profile = Editor(avatar_image).resize((150, 150)).circle_image()
                background.paste(profile, (325, 60))
                
                # Text
                background.text((400, 220), f"NEW ENTITY DETECTED: {member.name.upper()}", font=Font.poppins(variant="bold", size=24), color="#cba6f7", align="center")
                
                file = discord.File(fp=background.image_bytes, filename="welcome.png")
                await join_channel.send(f"🐧 A new client has connected to the server infrastructure: {member.mention}! Secure communication protocol initiated.", file=file)
    except Exception as e:
        print(f"Join Image Render Error: {e}")

@bot.event
async def on_member_remove(member):
    # ORIGINAL: EASY-PIL VISUAL GOODBYE SCREEN
    try:
        guild_config = await config_collection.find_one({"_id": str(member.guild.id)})
        if guild_config and "join_channel" in guild_config:
            join_channel = member.guild.get_channel(int(guild_config["join_channel"]))
            
            if join_channel:
                background = Editor(Canvas((800, 250), color="#1e1e2e"))
                
                # Terminal UI Design
                background.rectangle((0, 0), width=800, height=40, color="#11111b")
                background.text((20, 10), "root@adminpingu:~# sudo kill -9 client_process", font=Font.poppins(size=18), color="#f38ba8")
                
                # Avatar
                avatar_image = await load_image_async(str(member.display_avatar.url))
                profile = Editor(avatar_image).resize((150, 150)).circle_image()
                background.paste(profile, (325, 60))
                
                # Text
                background.text((400, 220), f"CONNECTION TERMINATED: {member.name.upper()}", font=Font.poppins(variant="bold", size=24), color="#f38ba8", align="center")
                
                file = discord.File(fp=background.image_bytes, filename="goodbye.png")
                await join_channel.send(f"⚠️ A client has disconnected: **{member.name}**. Data stream halted.", file=file)
    except Exception as e:
        print(f"Remove Image Render Error: {e}")

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
        embed.add_field(name="Total Warnings", value=f"**{total_warns}/5**", inline=False)
        await warn_channel.send(embed=embed)
        
    if total_warns >= 5:
        try:
            await member.ban(reason="Automated Ban - Exceeded 5 Active Warnings Limit.")
            if warn_channel:
                await warn_channel.send(f"🚨 {member.mention} has been permanently banned for exceeding the 5-warning limit!")
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

        # NEW SYSTEM ADDED: HEAVY PROFANITY CONTROL (Bypass Protected with Regex)
        if is_heavy_swear(message.content):
            try:
                await message.delete()
                warning_channel = bot.get_channel(1521880436270301354)
                if warning_channel:
                    await warning_channel.send(f"🚨 Warning! {message.author.mention} has used a strictly prohibited word.")
                # Save to warning system (Bans on the 5th offense)
                await apply_warning(message.author, "Severe prohibited word usage (Bypass Protection Triggered)", message.guild)
                return  
            except Exception as e:
                print(f"Heavy Profanity filter error: {e}")

    # OPTIMIZATION AND XP GAIN: Slower rate (4-8 points)
    try:
        gained = random.randint(4, 8) 
        leveled_up, new_level = await add_xp(message.author.id, gained)
        
        if leveled_up and new_level:
            level_channel = bot.get_channel(LEVEL_LOG_CHANNEL_ID)
            epic_channel = bot.get_channel(EPIC_LEVEL_100_CHANNEL)
            
            # NEW SYSTEM ADDED: DYNAMIC MESSAGE ON EVERY LEVEL UP
            level_log_channel = bot.get_channel(1521880096854769785)
            if level_log_channel:
                await level_log_channel.send(f"🆙 Progress Report: {message.author.mention} has gained experience and reached **Level {new_level}**! 🎉")
            
            # ASSIGN NECESSARY ROLE
            if new_level in LEVEL_ROLES:
                target_role = message.guild.get_role(LEVEL_ROLES[new_level])
                if target_role:
                    await message.author.add_roles(target_role)

            # SPECIAL LEVEL MESSAGES (ORIGINAL - NONE DELETED)
            if new_level == 5:
                await level_channel.send(f"🎉 Congratulations {message.author.mention}, you're now **LEVEL 5**!\n🔓 **Unlocked:** Media Permission")
                media_role = message.guild.get_role(MEDIA_ROLE_ID)
                if media_role: await message.author.add_roles(media_role)

            elif new_level == 10:
                await level_channel.send(f"🎉 Congratulations {message.author.mention}, you're now **LEVEL 10**! System structural upgrade complete.")

            elif new_level == 15:
                await level_channel.send(f"🎉 Congratulations {message.author.mention}, you're now **LEVEL 15**! Core matrix synchronization optimized.")

            elif new_level == 20:
                await level_channel.send(f"🎉 Congratulations {message.author.mention}, you're now **LEVEL 20**! Advanced clearance granted.")

            elif new_level == 25:
                embed = discord.Embed(title="🎖️ ATTENTION: OUTSTANDING SERVICE ACKNOWLEDGED", description=f"Dear {message.author.mention},\n\nYour continuous activity and dedication to this server haven't gone unnoticed. We are honored to confirm your advancement to **Level 25**. The system has registered you as a distinguished unit.", color=discord.Color.dark_green())
                await level_channel.send(embed=embed)

            elif new_level == 50:
                embed = discord.Embed(title="🔥 ALERT: CRITICAL THRESHOLD BREACHED 🔥", description=f"**IDENTITY VERIFIED:** {message.author.mention}\n\nMassive milestone! You're officially one of the core pillars of this community. By reaching **Level 50**, you've secured high-ranking status. We salute you!", color=discord.Color.gold())
                embed.set_image(url="https://media.giphy.com/media/xUOxfgwY8Tvj1DY5y0/giphy.gif")
                await level_channel.send(embed=embed)

            elif new_level == 100:
                msg_content = f"### 👑 FIREWALLS BREACHED: A LEGEND HAS ARRIVED! 👑\n\nAttention all server nodes! {message.author.mention} just achieved the impossible and hit **LEVEL 100**!\n\nThe effort and time you've put into this community is genuinely legendary. You are officially a **Master User**. Huge congratulations on this massive milestone!"
                await level_channel.send(msg_content)
                if epic_channel:
                    await epic_channel.send(msg_content)
                    
    except Exception as e:
        print(f"XP System Skipped (Cache Protection/Error): {e}")

    await bot.process_commands(message)

# ==========================================
# 9. COMMAND MATRIX
# ==========================================

# --- CONFIG COMMANDS ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setnewschannel(ctx, channel: discord.TextChannel = None):
    """Sets a channel for automated daily tech/linux news and locks it."""
    target_channel = channel or ctx.channel
    
    # Save to DB
    await config_collection.update_one(
        {"_id": str(ctx.guild.id)}, 
        {"$set": {"news_channel": str(target_channel.id)}}, 
        upsert=True
    )
    
    # Lock to unauthorized users
    await target_channel.set_permissions(ctx.guild.default_role, send_messages=False)
    
    embed = discord.Embed(title="✅ News Network Configured", description=f"{target_channel.mention} has been successfully configured for the Global Tech News broadcast.\n\n🔒 *Security Protocol:* Channel locked to standard users for writing.", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setjoinchannel(ctx, channel: discord.TextChannel = None):
    """Sets the channel for visual welcome/goodbye terminal banners."""
    target_channel = channel or ctx.channel
    
    # Save to DB
    await config_collection.update_one(
        {"_id": str(ctx.guild.id)}, 
        {"$set": {"join_channel": str(target_channel.id)}}, 
        upsert=True
    )
    
    await ctx.send(f"✅ **Unit Configured:** Incoming and outgoing clients will now be greeted with a visual terminal interface in {target_channel.mention}.")

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
        title="Choose Your Primary Platform & Graphics Driver", 
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
    """Displays highly detailed user level card analytics using MongoDB."""
    member = member or ctx.author
    
    try:
        user_data = await xp_collection.find_one({"_id": member.id})
    except Exception:
        user_data = None

    if not user_data:
        user_data = {"total": 0, "level": 1}
        
    next_xp = user_data["level"] * 50
    current_xp = user_data["total"]
    
    percentage = min(current_xp / next_xp, 1.0)
    bar_length = 10
    filled_blocks = int(percentage * bar_length)
    empty_blocks = bar_length - filled_blocks
    progress_bar = "█" * filled_blocks + "░" * empty_blocks

    embed = discord.Embed(title=f"📊 {member.name}'s Core Matrix Analytics", color=discord.Color.purple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="System Rank Access", value=f"`Level {user_data['level']}`", inline=True)
    embed.add_field(name="Experience Stream Index", value=f"`{current_xp} / {next_xp} XP`", inline=True)
    embed.add_field(name="Matrix Calibration Progress", value=f"`[{progress_bar}] {int(percentage * 100)}%`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def leaderstats(ctx):
    """Lists the top 15 highest-ranked matrix members directly from MongoDB."""
    try:
        cursor = xp_collection.find({}).sort("total", -1).limit(15)
        sorted_users = await cursor.to_list(length=15)
        
        if not sorted_users:
            return await ctx.send("❌ **Error:** Structural database empty. No records tracked yet.")
            
        leaderboard_str = ""
        for index, user_data in enumerate(sorted_users, start=1):
            user_id = user_data["_id"]
            user_obj = ctx.guild.get_member(user_id)
            name = user_obj.name if user_obj else f"Unknown User ({user_id})"
            leaderboard_str += f"`#{index:02}` **{name}** - Level {user_data['level']} ({user_data['total']} XP)\n"
            
        embed = discord.Embed(title="🏆 Server Communication Matrix - Top 15 Leaderboard", description=leaderboard_str, color=discord.Color.gold())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ **Database Error:** Could not fetch records. Details: {e}")

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
              "`?ipban <user>` - Emulate a network infrastructure firewall routing ban\n"
              "`?setnewschannel` - Sets up and locks the automated Linux News channel\n"
              "`?setjoinchannel` - Sets the channel for visual welcome/goodbye banners", 
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
# 10. GLOBAL EXCEPTION HANDLER
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
