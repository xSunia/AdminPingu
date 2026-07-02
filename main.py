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
import re 
from unidecode import unidecode
from easy_pil import Editor, Canvas, Font, load_image_async
from motor.motor_asyncio import AsyncIOMotorClient

# ==========================================
# 1. RENDER KEEP-ALIVE SYSTEM
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "AdminPingu is currently online and fully operational."

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

# YENI: Etkinlik kanalının ID'sini geçici olarak tutacağımız değişken
ACTIVE_EVENT_CHANNEL_ID = None

LEVEL_ROLES = {
    5: 1521923955127226609,
    10: 1521924218479186102,
    15: 1521924385647366210,
    20: 1521924589230358708,
    25: 1521924699926302740,
    50: 1521924800682004530,
    100: 1521924931875635210
}

LINUX_COMMANDS = [
    {"cmd": "ls", "desc": "Used to list directory contents. It's like taking a quick look at everything inside a folder!"},
    {"cmd": "cd", "desc": "Allows you to navigate between directories. It essentially teleports you from one path to another."},
    {"cmd": "pwd", "desc": "Prints the full path of your current working directory."},
    {"cmd": "sudo", "desc": "Runs a command with the elevated security privileges of the system administrator ('root')."},
    {"cmd": "htop", "desc": "A much sleeker, colorful, and interactive modern upgrade to the classic 'top' command!"}
]

SERVER_RULES = [
    {"title": "Hate Speech and Discrimination", "desc": "Racism, ethnic discrimination, and hate speech of any kind are strictly prohibited.", "penalty": "Permanent Ban"},
    {"title": "Unsolicited Advertising", "desc": "Sharing advertising or invite links in channels or via DMs without permission is not allowed.", "penalty": "Timeout"},
    {"title": "Harassment", "desc": "Homophobia, sexism, and any discrimination against marginalized groups are strictly prohibited.", "penalty": "Permanent Ban"},
    {"title": "Disrupting the Peace", "desc": "Harassing, provoking, or intentionally annoying other members is forbidden.", "penalty": "Warning + Timeout"},
    {"title": "False Information", "desc": "Spreading fake news or misinformation to manipulate members is not allowed.", "penalty": "Warning"},
    {"title": "Excessive Trolling", "desc": "Engaging in excessive trolling that derails conversations or ruins the server vibe is prohibited.", "penalty": "Warning + Timeout"},
    {"title": "Toxic Language", "desc": "Excessive swearing, toxic language, and personal insults are strictly prohibited.", "penalty": "Timeout"},
    {"title": "NSFW Content", "desc": "Posting NSFW, 18+ content, gore, or graphic violence is strictly prohibited.", "penalty": "Permanent Ban"},
    {"title": "Impersonation", "desc": "Impersonating another server member, staff, or a bot is not allowed.", "penalty": "Warning + Timeout"},
    {"title": "Spam and Flooding", "desc": "Mass mentioning, spamming, or flooding channels with repeated messages is prohibited.", "penalty": "Timeout"}
]

LINUX_GIFS = [
    "https://media.giphy.com/media/LmNwrBhejkK9EFP504/giphy.gif",
    "https://media.giphy.com/media/i8XwYIrNqMEA8/giphy.gif",
    "https://media.giphy.com/media/VbKLOdvYXBEgw/giphy.gif",
    "https://media.tenor.com/7D-R9eYf6W8AAAAC/linux-penguin.gif",
    "https://media.tenor.com/V-nF03F5h20AAAAC/linux-arch.gif"
]

TANK_FACTS = [
    "The British Mark I was the very first tank to enter combat during the Battle of the Flers-Courcelette back in 1916.",
    "Major General Ernest Swinton is largely credited with the initial concept of armored tracked vehicles.",
    "The German Tiger I featured an 88mm KwK 36 gun, which was actually designed as an anti-aircraft flak cannon first.",
    "Sloped armor, famously used on the Soviet T-34, artificially increases the thickness of the armor against incoming shells."
]

MMA_FACTS = [
    "Jon 'Bones' Jones became the youngest champion in UFC history at the age of 23.",
    "The traditional Octagon was created to avoid the disadvantages of a square boxing ring, preventing fighters from getting trapped in corners.",
    "Brazilian Jiu-Jitsu rose to global fame after Royce Gracie dominated the first, second, and fourth UFC tournaments."
]

TECH_JOKES = [
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I'd tell you a joke about UDP, but you probably wouldn't get it."
]

PYTHON_TIPS = [
    "Use list comprehensions to write cleaner and faster code: `[x**2 for x in range(10)]`",
    "Did you know? You can swap two variables easily without a temporary variable: `a, b = b, a`",
    "Use `enumerate()` if you need both the index and the value while looping through an iterable."
]

ALL_DISTRO_ROLES = [
    1521868543799328808, 1521870392472502344, 1521870674669338654, 1521871074994950295, 1521871078308184074,
    1521870173861056655, 1521871399403393044, 1521871679368986655, 1521871896117776468,
    1521870110552227910, 1521868791942742026, 1521871613958819860, 1521871816321404969, 1521872016901406720,
    1521870225228955798, 1521872173688422420, 1521872360393670819, 1521872534117679206, 1521872635968098344,
    1521872683803873432, 1521872759691542588, 1521873026776301608, 1521873129868365964,
    1521909235594825941, 1521909235594825999,
    1522137195102867526, 1522137253856415784, 1522143963904081920 
]
ALL_GPU_ROLES = [1521879270530486414, 1521879224951246928, 1521879315648614410]

# ==========================================
# 4. SMART PROFANITY & BYPASS FILTER ALGORITHM
# ==========================================
STRICT_BANNED_WORDS = {
    "nigger", "nigga", "porn", "porno", "sex", "pussy", "fuck", 
    "bitch", "cunt", "dick", "asshole", "slut", "whore", 
    "faggot", "childporn", "rape", "pusy", "fck", "btch", "cp"
}

SQUISHED_SEVERE_WORDS = ["fuck", "nigger", "nigga", "porn", "pussy", "bitch", "faggot", "whore"]

LEET_DICT = {'@': 'a', '4': 'a', '1': 'i', '!': 'i', '0': 'o', '3': 'e', '$': 's', '5': 's', '7': 't', '+': 't', 'v': 'u'}

def clean_text_for_filter(text):
    text = text.lower()
    for k, v in LEET_DICT.items():
        text = text.replace(k, v)
    text = unidecode(text)
    return text

def is_heavy_swear(text):
    cleaned_text = clean_text_for_filter(text)
    
    words = re.findall(r'[a-z]+', cleaned_text)
    for word in words:
        dedup_word = re.sub(r'(.)\1+', r'\1', word)
        if word in STRICT_BANNED_WORDS or dedup_word in STRICT_BANNED_WORDS:
            return True
            
    squished_text = re.sub(r'[^a-z]', '', cleaned_text)
    squished_dedup = re.sub(r'(.)\1+', r'\1', squished_text)
    
    for severe_word in SQUISHED_SEVERE_WORDS:
        if severe_word in squished_text or severe_word in squished_dedup:
            return True

    return False

# ==========================================
# 5. MONGODB DATABASE SETUP & CACHING
# ==========================================
MONGO_URI = os.environ.get("MONGO_URI")

try:
    mongo_client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = mongo_client["AdminPinguDB"]
    xp_collection = db["users_xp"]
    config_collection = db["server_config"]
except Exception as e:
    print(f"MongoDB Initialization Error: {e}")

warning_db = {}
user_message_cache = {} 
xp_message_counter = {} # New specific cache to count every 3 messages
LAST_NEWS_URL = "" 

# ==========================================
# 6. HELPER FUNCTIONS & ENGINE
# ==========================================

def get_xp_requirement(level):
    
    return int(100 * (level ** 1.15))

async def add_xp(user_id, amount):
    try:
        current_time = time.time()
        
        user_data = await xp_collection.find_one({"_id": user_id})
        if not user_data:
            user_data = {"_id": user_id, "total": 0, "daily": 0, "weekly": 0, "monthly": 0, "last_msg": 0, "level": 1}
        
        new_total = user_data["total"] + amount
        new_daily = user_data.get("daily", 0) + amount
        new_weekly = user_data.get("weekly", 0) + amount
        new_monthly = user_data.get("monthly", 0) + amount
        new_level = user_data["level"]
        
        leveled_up = False
        next_level_xp = get_xp_requirement(new_level)
        
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
# 7. INTERACTIVE DROPDOWN ROLES (GUI VIEW)
# ==========================================
class DistroSelect(Select):
    def __init__(self, placeholder, options, custom_id):
        # min_values=0 allows users to deselect/clear their roles from the dropdown completely
        super().__init__(placeholder=placeholder, min_values=0, max_values=2, options=options, custom_id=custom_id)
        # Store only the IDs belonging to this specific menu block
        self.menu_role_ids = [int(opt.value) for opt in options]

    async def callback(self, interaction: discord.Interaction):
        selected_role_ids = [int(v) for v in self.values]
        
        # Cross-menu validation to perfectly support dual-boot setups!
        other_os_roles = [r for r in interaction.user.roles if r.id in ALL_DISTRO_ROLES and r.id not in self.menu_role_ids]
        
        if len(other_os_roles) + len(selected_role_ids) > 2:
            return await interaction.response.send_message(
                "❌ **Dual-Boot Limit Reached:** You can only have a maximum of 2 OS roles across all menus! Please deselect an OS from another menu first.", 
                ephemeral=True
            )
            
        roles_to_add = []
        for role_id in selected_role_ids:
            role = interaction.guild.get_role(role_id)
            if role:
                roles_to_add.append(role)
                
        # Scoped removal: Only remove unselected roles that belong to THIS specific dropdown menu.
        roles_to_remove = [r for r in interaction.user.roles if r.id in self.menu_role_ids and r.id not in selected_role_ids]
        
        if roles_to_remove:
            await interaction.user.remove_roles(*roles_to_remove)
            
        if roles_to_add:
            await interaction.user.add_roles(*roles_to_add)
            
        if not roles_to_add and not roles_to_remove:
             return await interaction.response.send_message("✅ No changes were made.", ephemeral=True)
             
        role_names = " & ".join([r.name for r in roles_to_add]) if roles_to_add else "Cleared"
        await interaction.response.send_message(f"✅ Menu Updated! Current selection for this category: `{role_names}`", ephemeral=True)

class GPUSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="NVIDIA Graphics", value="1521879270530486414", emoji="🟩"),
            discord.SelectOption(label="AMD Graphics", value="1521879224951246928", emoji="🟥"),
            discord.SelectOption(label="Intel Graphics", value="1521879315648614410", emoji="🟦")
        ]
        super().__init__(placeholder="Select Your Graphics Driver", min_values=0, max_values=1, options=options, custom_id="gpu_select")

    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            roles_to_remove = [r for r in interaction.user.roles if r.id in ALL_GPU_ROLES]
            if roles_to_remove:
                await interaction.user.remove_roles(*roles_to_remove)
            return await interaction.response.send_message("✅ Graphics Driver selection cleared.", ephemeral=True)
            
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
            discord.SelectOption(label="Artix Linux", value="1521871078308184074"),
            discord.SelectOption(label="Black Arch", value="1522137195102867526"),
            discord.SelectOption(label="CachyOS", value="1522143963904081920")
        ]
        self.add_item(DistroSelect(placeholder="Arch / Arch-based", options=arch_opts, custom_id="arch_menu"))
        
        deb_ubu_opts = [
            discord.SelectOption(label="Debian", value="1521870173861056655"),
            discord.SelectOption(label="Ubuntu", value="1521870110552227910"),
            discord.SelectOption(label="Linux Mint", value="1521868791942742026"),
            discord.SelectOption(label="Kali Linux", value="1521871399403393044"),
            discord.SelectOption(label="Pop!_OS", value="1521871613958819860"),
            discord.SelectOption(label="Zorin OS", value="1521871816321404969"),
            discord.SelectOption(label="MX Linux", value="1521871679368986655"),
            discord.SelectOption(label="Deepin", value="1521871896117776468"),
            discord.SelectOption(label="Elementary OS", value="1521872016901406720"),
            discord.SelectOption(label="Parrot OS", value="1522137253856415784")
        ]
        self.add_item(DistroSelect(placeholder="Debian & Ubuntu-based", options=deb_ubu_opts, custom_id="deb_ubu_menu"))

        win_bsd_opts = [
            discord.SelectOption(label="Windows 11", value="1521909235594825941"),
            discord.SelectOption(label="FreeBSD", value="1521909235594825999"),
            discord.SelectOption(label="Windows 10", value="1521909403496742973")
        ]
        self.add_item(DistroSelect(placeholder="Windows & FreeBSD", options=win_bsd_opts, custom_id="win_bsd_menu"))

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
# 8. BG LOOP TASKS (SCHEDULER)
# ==========================================
@tasks.loop(minutes=30)
async def half_hourly_reminder():
    await bot.wait_until_ready()
    global REMINDER_CHANNEL_ID
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if channel:
        rule = random.choice(SERVER_RULES)
        embed = discord.Embed(
            title="🐧 Automated Security Reminder",
            description=f"Just a quick reminder to keep our community safe and enjoyable:\n\n"
                        f"🔹 **Rule:** {rule['title']}\n"
                        f"📝 **Details:** {rule['desc']}\n"
                        f"⚡ **Penalty:** `{rule['penalty']}`",
            color=discord.Color.red()
        )
        embed.set_footer(text="AdminPingu System Protection Protocol")
        await channel.send(embed=embed)

@tasks.loop(hours=24)
async def reset_daily_xp():
    try:
        await xp_collection.update_many({}, {"$set": {"daily": 0}})
    except Exception as e:
        print(f"Failed to reset daily XP: {e}")

@tasks.loop(hours=1)
async def daily_tech_news():
    await bot.wait_until_ready()
    global LAST_NEWS_URL
    try:
        feed = feedparser.parse("https://www.omgubuntu.co.uk/feed")
        if not feed.entries:
            return
            
        entry = feed.entries[0]
        
        if entry.link == LAST_NEWS_URL:
            return
            
        LAST_NEWS_URL = entry.link
        
        embed = discord.Embed(
            title=f"📰 {entry.title}", 
            url=entry.link, 
            description=entry.summary[:500] + "...", 
            color=discord.Color.teal()
        )
        embed.set_footer(text="Linux & Tech Intelligence Network")
        
        if "media_content" in entry:
            embed.set_image(url=entry.media_content[0]["url"])

        configs = await config_collection.find({"news_channel": {"$exists": True}}).to_list(length=100)
        for conf in configs:
            guild = bot.get_guild(int(conf["_id"]))
            if guild:
                news_channel = guild.get_channel(int(conf["news_channel"]))
                if news_channel:
                    await news_channel.send("🚨 **Fresh Tech News Uploaded!** 🚨", embed=embed)
    except Exception as e:
        print(f"Tech news stream error: {e}")

# YENI: Her Pazar UTC 12:00'da tetiklenecek Event Loop'u
@tasks.loop(time=datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc))
async def sunday_xp_event():
    await bot.wait_until_ready()
    global ACTIVE_EVENT_CHANNEL_ID
    
    # Bugün Pazar değilse (Python'da Pazartesi=0, Pazar=6'dır) işlemi iptal et
    now = datetime.datetime.now(datetime.timezone.utc)
    if now.weekday() != 6: 
        return
        
    category = bot.get_channel(1510339895032418506)
    if not category:
        return
        
    guild = category.guild
    
    try:
        # Kanalı 10 saniye slowmode ile oluşturuyoruz
        event_channel = await guild.create_text_channel(
            name="🔥-triple-xp-chaos",
            category=category,
            topic="3X XP EVENT CHANNEL! 10s cooldown. Spam filter disabled. Deletes in 3 hours.",
            slowmode_delay=10
        )
        
        ACTIVE_EVENT_CHANNEL_ID = event_channel.id
        
        # Etkinlik kanalına Efsanevi Giriş Mesajı
        await event_channel.send(
            "🚨 **THE RIFT HAS OPENED! TRIPLE XP IS NOW ACTIVE!** 🚨\n\n"
            "Welcome to the Chaos Zone. For the next **3 HOURS**, every message you send here grants **3X XP**! "
            "The standard bot spam filter has been lifted, but you must survive the 10-second cooldown.\n\n"
            "Grind your hearts out. The countdown to destruction has begun! ⏳"
        )
        
        # Ana kanala duyuru geç
        announcement_channel = bot.get_channel(1522172546714308648)
        if announcement_channel:
            await announcement_channel.send(f"⚡ **THE SUNDAY EVENT HAS BEGUN!** A dimensional rift just opened at {event_channel.mention}. Get in there for **3X XP**! The channel will self-destruct in exactly 3 hours.")
            
        # Tam 3 Saat (10800 saniye) bekle
        await asyncio.sleep(3 * 60 * 60)
        
        # Süre dolunca kanalı yok et
        if event_channel:
            await event_channel.delete()
            
        ACTIVE_EVENT_CHANNEL_ID = None
        
        if announcement_channel:
            await announcement_channel.send("🛑 **THE SUNDAY 3X XP EVENT HAS CONCLUDED!** The rift has collapsed and the channel has been erased. See you all next week!")
            
    except Exception as e:
        print(f"Sunday Event Error: {e}")
        ACTIVE_EVENT_CHANNEL_ID = None

# ==========================================
# 9. BOT LIFE-CYCLE & AUTOMATION EVENTS
# ==========================================
@bot.event
async def on_ready():
    print('==========================================')
    print(f'🤖 Bot Is Online: {bot.user.name}')
    print('🚀 Engine Status: READY AND OPERATIONAL')
    print('==========================================')
    await bot.change_presence(activity=discord.Game(name="Managing the Server | ?help"))
    half_hourly_reminder.start()
    reset_daily_xp.start()
    daily_tech_news.start()
    sunday_xp_event.start() # YENI: Event Task'ı başlatıldı
    bot.add_view(RolesView())

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(USER_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except Exception:
            pass

    terminal_channel = bot.get_channel(1510339895032418508)
    if terminal_channel:
        linux_msg = (
            f"```yaml\n"
            f"sys.log: [NEW_CONNECTION_ESTABLISHED]\n"
            f"user: {member.name}\n"
            f"status: authorized\n"
            f"```\n"
            f"🔌 **Access Granted!** Welcome to the server, {member.mention}.\n\n"
            f"📂 **Please review the directories before starting:**\n"
            f"> 📜 Rules: <#1510343681985613905>\n"
            f"> 🏷️ Roles: <#1521868274240065597>\n"
        )
        await terminal_channel.send(linux_msg)

    try:
        guild_config = await config_collection.find_one({"_id": str(member.guild.id)})
        if guild_config and "join_channel" in guild_config:
            join_channel = member.guild.get_channel(int(guild_config["join_channel"]))
            
            if join_channel:
                background = Editor(Canvas((800, 250), color="#1e1e2e"))
                
                background.rectangle((0, 0), width=800, height=40, color="#11111b")
                background.text((20, 10), "root@adminpingu:~# ./accept_connection.sh", font=Font.poppins(size=18), color="#a6e3a1")
                
                avatar_image = await load_image_async(str(member.display_avatar.url))
                profile = Editor(avatar_image).resize((150, 150)).circle_image()
                background.paste(profile, (325, 60))
                
                background.text((400, 220), f"NEW USER: {member.name.upper()}", font=Font.poppins(variant="bold", size=24), color="#cba6f7", align="center")
                
                file = discord.File(fp=background.image_bytes, filename="welcome.png")
                await join_channel.send(f"🐧 A new user has connected: {member.mention}! Welcome aboard.", file=file)
    except Exception as e:
        print(f"Join Image Render Error: {e}")

@bot.event
async def on_member_remove(member):
    try:
        guild_config = await config_collection.find_one({"_id": str(member.guild.id)})
        if guild_config and "join_channel" in guild_config:
            join_channel = member.guild.get_channel(int(guild_config["join_channel"]))
            
            if join_channel:
                background = Editor(Canvas((800, 250), color="#1e1e2e"))
                
                background.rectangle((0, 0), width=800, height=40, color="#11111b")
                background.text((20, 10), "root@adminpingu:~# sudo kill -9 client_process", font=Font.poppins(size=18), color="#f38ba8")
                
                avatar_image = await load_image_async(str(member.display_avatar.url))
                profile = Editor(avatar_image).resize((150, 150)).circle_image()
                background.paste(profile, (325, 60))
                
                background.text((400, 220), f"DISCONNECTED: {member.name.upper()}", font=Font.poppins(variant="bold", size=24), color="#f38ba8", align="center")
                
                file = discord.File(fp=background.image_bytes, filename="goodbye.png")
                await join_channel.send(f"⚠️ **{member.name}** has left the server.", file=file)
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
        embed.add_field(name="Warnings", value=f"**{total_warns}/5**", inline=False)
        await warn_channel.send(embed=embed)
        
    if total_warns >= 5:
        admins = [m for m in guild.members if m.guild_permissions.administrator and not m.bot]
        for admin in admins:
            try:
                await admin.send(f"🚨 **Administrator Alert:** The user {member.mention} (`{member.name}`) has reached the **5/5 warning limit** in {guild.name}. They have officially run out of luck! Please review their logs and take manual action.")
            except Exception:
                pass
                
        if warn_channel:
            await warn_channel.send(f"🚨 {member.mention} has hit the 5-warning limit! Server administrators have been notified via DM.")
            
        warning_db[member.id] = 0

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    is_mod = message.author.guild_permissions.manage_messages
    if not is_mod:
        # SPAM FILTER - YENI: Etkinlik kanalındaysak Spam filtresini atla!
        if message.channel.id != ACTIVE_EVENT_CHANNEL_ID:
            if message.author.id not in user_message_cache:
                user_message_cache[message.author.id] = []
            
            user_message_cache[message.author.id].append(message.content.lower())
            
            if len(user_message_cache[message.author.id]) > 3:
                user_message_cache[message.author.id].pop(0)
                
            if len(user_message_cache[message.author.id]) == 3 and len(set(user_message_cache[message.author.id])) == 1:
                await message.delete()
                await message.channel.send(f"⚠️ Hey {message.author.mention}, please slow down and stop spamming!", delete_after=5)
                await apply_warning(message.author, "Spamming the chat", message.guild)
                user_message_cache[message.author.id] = [] 
                return

        # PROFANITY CONTROL
        if is_heavy_swear(message.content):
            try:
                await message.delete()
                warning_channel = bot.get_channel(WARNINGS_CHANNEL_ID)
                if warning_channel:
                    await warning_channel.send(f"🚨 Heads up! {message.author.mention} triggered the NSFW/Profanity filter.")
                await apply_warning(message.author, "Used prohibited NSFW/Profanity terms", message.guild)
                return  
            except Exception as e:
                print(f"Profanity filter error: {e}")

    # OPTIMIZED HARDCORE XP SYSTEM (2-6 XP every 3 messages)
    try:
        author_id = message.author.id
        if author_id not in xp_message_counter:
            xp_message_counter[author_id] = 0
            
        xp_message_counter[author_id] += 1
        
        if xp_message_counter[author_id] >= 3:
            xp_message_counter[author_id] = 0 # Reset counter after triggering
            gained = random.randint(5, 30) 
            
            # YENI: Eğer etkinlik kanalındaysa XP'yi 3 ile çarp
            if message.channel.id == ACTIVE_EVENT_CHANNEL_ID:
                gained *= 3
                
            leveled_up, new_level = await add_xp(author_id, gained)
            
            if leveled_up and new_level:
                level_channel = bot.get_channel(LEVEL_LOG_CHANNEL_ID)
                epic_channel = bot.get_channel(EPIC_LEVEL_100_CHANNEL)
                
                if level_channel:
                    await level_channel.send(f"🆙 Awesome! {message.author.mention} just reached **Level {new_level}**! 🎉")
                
                if new_level in LEVEL_ROLES:
                    target_role = message.guild.get_role(LEVEL_ROLES[new_level])
                    if target_role:
                        await message.author.add_roles(target_role)

                if new_level == 5:
                    if level_channel: await level_channel.send(f"🎉 Congrats {message.author.mention}, you're now **LEVEL 5**! Keep chatting to unlock more perks.")
                elif new_level == 10:
                    if level_channel: await level_channel.send(f"🎉 Amazing {message.author.mention}, you're now **LEVEL 10**! You've officially unlocked Media Permissions. 📸")
                    media_role = message.guild.get_role(MEDIA_ROLE_ID)
                    if media_role: await message.author.add_roles(media_role)
                elif new_level == 25:
                    embed = discord.Embed(title="🎖️ Outstanding Activity Noticed", description=f"{message.author.mention}, your dedication is real! Welcome to **Level 25**. Keep it up!", color=discord.Color.dark_green())
                    if level_channel: await level_channel.send(embed=embed)
                elif new_level == 50:
                    embed = discord.Embed(title="🔥 Level 50 Milestone Reached! 🔥", description=f"Massive congrats to {message.author.mention}! Reaching Level 50 is no joke. We salute your grind!", color=discord.Color.gold())
                    embed.set_image(url="https://media.giphy.com/media/xUOxfgwY8Tvj1DY5y0/giphy.gif")
                    if level_channel: await level_channel.send(embed=embed)
                elif new_level == 100:
                    msg_content = f"👑 **A LEGEND HAS ARRIVED!** 👑\n\nAttention everyone! {message.author.mention} just achieved the impossible and hit **LEVEL 100**! Massive congratulations!"
                    if level_channel: await level_channel.send(msg_content)
                    if epic_channel:
                        await epic_channel.send(msg_content)
                        
    except Exception as e:
        print(f"XP Processing Error: {e}")

    await bot.process_commands(message)

# ==========================================
# 10. COMMAND MATRIX
# ==========================================

# YENI: Bilgilendirme Komutu
@bot.command()
@commands.has_permissions(administrator=True)
async def starteventonsunday(ctx):
    if ctx.channel.id != 1522172546714308648:
        return await ctx.send("❌ This command can only be used in the designated announcement channel.")
        
    epic_msg = (
        "🔥 **A DIMENSIONAL RIFT IS OPENING! THE 3X XP EVENT!** 🔥\n\n"
        "Forget everything you know! This isn't just another Sunday. A dimensional gateway will automatically open, "
        "spawning a legendary **3-HOUR TRIPLE XP CHAT ZONE**!\n\n"
        "⚡ **EVENT MECHANICS:**\n"
        "• A chaotic chat channel will automatically forge itself in the designated category.\n"
        "• **TRIPLE (3X) XP** is permanently active while you are inside.\n"
        "• The system spam filters are **DISABLED** in this zone, but beware: a **10-second slowmode** will limit your strikes.\n"
        "• Exactly 3 hours later, the channel will implode and be deleted forever.\n\n"
        "🌍 **GLOBAL INITIATION TIMES (EVERY SUNDAY):**\n"
        "```yaml\n"
        "🌐 UTC (Core Server Time): 12:00 PM\n"
        "🇹🇷 Turkey (TRT):           15:00 (3:00 PM)\n"
        "🇪🇺 Europe (CET / CEST):    13:00 / 14:00\n"
        "🇺🇸 America (EST / EDT):    07:00 AM / 08:00 AM\n"
        "🇷🇺 Russia (MSK):           15:00 (3:00 PM)\n"
        "```\n"
        "Prepare your keyboards. The ultimate grind awaits. Will you conquer the leaderboard?"
    )
    await ctx.send(epic_msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def setnewschannel(ctx, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    await config_collection.update_one(
        {"_id": str(ctx.guild.id)}, 
        {"$set": {"news_channel": str(target_channel.id)}}, 
        upsert=True
    )
    await target_channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(title="✅ News Channel Set", description=f"{target_channel.mention} is now the official Tech News broadcast channel.", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setjoinchannel(ctx, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    await config_collection.update_one(
        {"_id": str(ctx.guild.id)}, 
        {"$set": {"join_channel": str(target_channel.id)}}, 
        upsert=True
    )
    await ctx.send(f"✅ Users will now be greeted with visual terminal banners in {target_channel.mention}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def messagesendadminpingu(ctx, channel: discord.TextChannel = None):
    global REMINDER_CHANNEL_ID
    target_channel = channel or ctx.channel
    REMINDER_CHANNEL_ID = target_channel.id
    await ctx.send(f"✅ The automated rules reminder will now be sent to {target_channel.mention}.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'y'

    await ctx.send("⚠️ **WARNING:** You are about to wipe all messages in this channel.\nType `y` within 30 seconds to proceed.")
    try:
        await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("❌ **Aborted:** Channel wipe canceled due to inactivity.")

    await ctx.send("🚨 **Final confirmation:** This is irreversible. Type `y` one last time.", delete_after=10)
    try:
        await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("❌ **Aborted:** Channel wipe canceled.")

    try:
        deleted = await ctx.channel.purge(limit=None)
        msg = await ctx.send(f"✅ **Success:** Purged `{len(deleted)}` messages.")
        await asyncio.sleep(5)
        await msg.delete()
    except Exception as e:
        await ctx.send(f"❌ Error during purge: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def roles(ctx):
    role_embed = discord.Embed(
        title="Choose Your OS & Hardware", 
        description="Select your preferred distributions and graphics drivers from the menus below.\n*(Note: You can select up to 2 OS roles across all menus for Dual-Boot configurations!)*", 
        color=discord.Color.dark_theme()
    )
    await ctx.send(embed=role_embed, view=RolesView())

@bot.command()
@commands.has_permissions(manage_channels=True)
async def sudolock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(
        title="🔒 Channel Locked",
        description=f"This channel has been locked down by {ctx.author.mention}.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def sudounlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    embed = discord.Embed(
        title="🔓 Channel Unlocked",
        description=f"The lockdown has been lifted by {ctx.author.mention}.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, hours: int = 1, *, reason="No reason specified"):
    duration = datetime.timedelta(hours=hours)
    try:
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="🤫 User Muted", color=discord.Color.orange())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Duration", value=f"`{hours} Hours`", inline=True)
        embed.add_field(name="Reason", value=f"`{reason}`", inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to mute user: {e}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"✅ Mute lifted for {member.mention}.")
    except Exception as e:
        await ctx.send(f"❌ Failed to unmute user: {e}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warning(ctx, member: discord.Member, *, reason="Manual Warning"):
    await apply_warning(member, reason, ctx.guild)
    await ctx.send(f"✅ Warning applied to {member.mention}.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.name} has been banned. Reason: `{reason}`")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ Ban lifted for user: `{user.name}`.")
    except Exception as e:
        await ctx.send(f"❌ Failed to unban: {e}")

@bot.command()
async def stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    try:
        user_data = await xp_collection.find_one({"_id": member.id})
    except Exception:
        user_data = None

    if not user_data:
        user_data = {"total": 0, "level": 1}
        
    current_xp = user_data["total"]
    current_level = user_data["level"]
    
    # Accurate XP Progress Calculation based on the new exponential difficulty curve
    prev_level_xp = get_xp_requirement(current_level - 1) if current_level > 1 else 0
    next_level_xp = get_xp_requirement(current_level)
    
    xp_into_level = current_xp - prev_level_xp
    xp_needed_for_level = next_level_xp - prev_level_xp 
    
    percentage = min(max(xp_into_level / xp_needed_for_level, 0.0), 1.0)
    bar_length = 10
    filled_blocks = int(percentage * bar_length)
    empty_blocks = bar_length - filled_blocks
    progress_bar = "█" * filled_blocks + "░" * empty_blocks

    embed = discord.Embed(title=f"📊 {member.name}'s Profile", color=discord.Color.purple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Current Level", value=f"`Level {current_level}`", inline=True)
    embed.add_field(name="Total XP", value=f"`{current_xp} XP`", inline=True)
    embed.add_field(name="Next Level At", value=f"`{next_level_xp} XP`", inline=True)
    embed.add_field(name="Progress", value=f"`[{progress_bar}] {int(percentage * 100)}%`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def leaderstats(ctx):
    try:
        cursor = xp_collection.find({}).sort("total", -1).limit(15)
        sorted_users = await cursor.to_list(length=15)
        
        if not sorted_users:
            return await ctx.send("❌ The database is empty.")
            
        leaderboard_str = ""
        for index, user_data in enumerate(sorted_users, start=1):
            user_id = user_data["_id"]
            user_obj = ctx.guild.get_member(user_id)
            name = user_obj.name if user_obj else f"Unknown ({user_id})"
            leaderboard_str += f"`#{index:02}` **{name}** - Level {user_data['level']} ({user_data['total']} XP)\n"
            
        embed = discord.Embed(title="🏆 Server Leaderboard - Top 15", description=leaderboard_str, color=discord.Color.gold())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error fetching leaderboard: {e}")

@bot.command()
async def randomlinux(ctx):
    selected = random.choice(LINUX_COMMANDS)
    embed = discord.Embed(
        title=f"🐧 Linux Command Tip",
        description=f"📁 **Command:** `{selected['cmd']}`\n\n💡 **What it does:** {selected['desc']}",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def whoami(ctx):
    roles_list = [r.name for r in ctx.author.roles if r.name != "@everyone"]
    roles_str = ", ".join(roles_list) if roles_list else "No assigned roles."
    
    embed = discord.Embed(title="💻 Identity Verification: whoami", color=discord.Color.dark_grey())
    embed.add_field(name="User ID", value=f"`{ctx.author.id}`", inline=True)
    embed.add_field(name="Administrator Status", value=f"`{ctx.author.guild_permissions.administrator}`", inline=True)
    embed.add_field(name="Active Roles", value=f"```text\n{roles_str}```", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def weather(ctx, *, city: str = ""):
    if not city.strip():
        await ctx.send("❌ Please provide a city name! (e.g., `?weather London`).")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://wttr.in/{city}?format=3') as resp:
            if resp.status == 200:
                text = await resp.text()
                await ctx.send(f"🌤️ **Weather:** `{text.strip()}`")
            else:
                await ctx.send("❌ Could not fetch the weather data right now.")

@bot.command()
async def tankfact(ctx):
    fact = random.choice(TANK_FACTS)
    embed = discord.Embed(title="🪖 Random Tank Fact", description=fact, color=discord.Color.dark_gray())
    await ctx.send(embed=embed)

@bot.command()
async def mmafact(ctx):
    fact = random.choice(MMA_FACTS)
    embed = discord.Embed(title="🥊 Random MMA Fact", description=fact, color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command()
async def pythontip(ctx):
    tip = random.choice(PYTHON_TIPS)
    embed = discord.Embed(title="🐍 Python Tip", description=tip, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command()
async def tea(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"☕ Hey {member.mention}, here is a freshly brewed cup of hot tea for you. Enjoy!")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency is `{latency}ms`.")

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"🏰 {guild.name} Server Info", color=discord.Color.blue())
    embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="Total Members", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="Created On", value=f"`{guild.created_at.strftime('%Y-%m-%d')}`", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ {member.name}'s Avatar", color=discord.Color.dark_magenta())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def coinflip(ctx):
    choices = ["Heads", "Tails"]
    await ctx.send(f"🪙 The coin landed on: **{random.choice(choices)}**")

@bot.command()
async def diceroll(ctx, sides: int = 6):
    if sides < 2:
        return await ctx.send("❌ A dice must have at least 2 sides!")
    await ctx.send(f"🎲 You rolled a `{sides}`-sided dice and got: **{random.randint(1, sides)}**")

@bot.command(name="8ball")
async def magic_ball(ctx, *, question: str):
    responses = [
        "It is certain.", "Without a doubt.", "Yes, definitely.", 
        "Ask again later.", "Cannot predict right now.", 
        "Don't count on it.", "My sources say no.", "Very doubtful."
    ]
    await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {random.choice(responses)}")

@bot.command()
async def joke(ctx):
    await ctx.send(f"😂 {random.choice(TECH_JOKES)}")

@bot.command()
async def gif(ctx):
    embed = discord.Embed(title="🐧 Random Linux Graphic", color=discord.Color.green())
    embed.set_image(url=random.choice(LINUX_GIFS))
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🐧 AdminPingu Command List", 
        description="Here is everything you can do with the bot:",
        color=discord.Color.dark_green()
    )
    
    embed.add_field(
        name="🛡️ Moderation Commands", 
        value="`?roles` - Opens the role selection menu\n"
              "`?sudolock` / `?sudounlock` - Locks/Unlocks a text channel\n"
              "`?mute <user> [h]` / `?unmute <user>` - Manages timeouts\n"
              "`?clear` - Mass deletes messages in a channel\n"
              "`?warning <user> [reason]` - Gives a user a warning\n"
              "`?ban <user> [reason]` / `?unban <id>` - Manages bans\n"
              "`?setnewschannel` - Sets the channel for tech news\n"
              "`?setjoinchannel` - Sets the channel for welcome banners", 
        inline=False
    )
    
    embed.add_field(
        name="📊 Stats & Utilities", 
        value="`?stats [user]` - View a user's level and XP\n"
              "`?leaderstats` - See the top 15 users in the server\n"
              "`?serverinfo` - Display information about this server\n"
              "`?messagesendadminpingu` - Configure the rules reminder channel", 
        inline=False
    )
    
    embed.add_field(
        name="🎮 Fun & Random", 
        value="`?weather <city>` - Get the current weather\n"
              "`?randomlinux` / `?whoami` / `?pythontip` - Tech stuff\n"
              "`?tankfact` / `?mmafact` - Interesting facts\n"
              "`?tea` - Brew some tea for someone\n"
              "`?coinflip` / `?diceroll` / `?8ball` / `?joke` - Minigames", 
        inline=False
    )
    
    embed.set_footer(text="Arguments in [brackets] are optional, <angle brackets> are required.")
    await ctx.send(embed=embed)

# ==========================================
# 11. GLOBAL EXCEPTION HANDLER
# ==========================================
@bot.listen()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **Access Denied:** You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Syntax Error:** You are missing some arguments! Check `?help` for usage.")
    else:
        pass 

# BOOTUP SEQUENCE
keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
