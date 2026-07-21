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

app = Flask('')

@app.route('/')
def home():
    return "AdminPingu is currently online and fully operational."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

LOG_CHANNEL_ID = 123456789012345678       
WARNINGS_CHANNEL_ID = 1521880436270301354 
LEVEL_LOG_CHANNEL_ID = 1521880096854769785
REMINDER_CHANNEL_ID = 123456789012345678  
EPIC_LEVEL_100_CHANNEL = 1510339895032418508 

USER_ROLE_ID = 1510547520273649704        
MEDIA_ROLE_ID = 1521875919864856714       

ACTIVE_EVENT_CHANNEL_ID = None

# BUG FIX / YENİ ÖZELLİK: Hatırlatma mesajı, chat'te uzun süredir kimse yazmıyorsa artık gönderilmiyor.
# Böylece gece kimse yokken kanal boş yere "kural üstüne kural" ile kirlenmiyor.
# Bu süreyi (saniye cinsinden) istediğin gibi değiştirebilirsin. Şu an 1 saat (3600 sn) olarak ayarlı.
REMINDER_INACTIVITY_THRESHOLD_SECONDS = 3600

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
    {"cmd": "htop", "desc": "A much sleeker, colorful, and interactive modern upgrade to the classic 'top' command!"},
    {"cmd": "mkdir", "desc": "Creates a brand new, empty directory at the specified path."},
    {"cmd": "rm", "desc": "Removes (deletes) files or directories. Use the -r flag for folders, and always double-check before running it!"},
    {"cmd": "cp", "desc": "Copies files or directories from one location to another, leaving the original intact."},
    {"cmd": "mv", "desc": "Moves or renames files and directories. If the destination is a new name, it acts as a rename."},
    {"cmd": "grep", "desc": "Searches through text using patterns, perfect for finding a specific line inside a huge log file."},
    {"cmd": "chmod", "desc": "Changes the read/write/execute permissions of a file or directory."},
    {"cmd": "chown", "desc": "Changes the owner (and optionally the group) of a file or directory."},
    {"cmd": "ps", "desc": "Displays information about currently running processes on the system."},
    {"cmd": "kill", "desc": "Sends a signal to a running process, most commonly used to terminate it."},
    {"cmd": "df", "desc": "Shows how much disk space is used and available on your mounted filesystems."},
    {"cmd": "du", "desc": "Estimates file and directory space usage, great for finding what's eating your storage."},
    {"cmd": "tar", "desc": "Archives multiple files into a single .tar file, often combined with compression like gzip."},
    {"cmd": "ssh", "desc": "Lets you securely log into and control a remote machine over an encrypted connection."},
    {"cmd": "curl", "desc": "Transfers data to or from a server, commonly used to test APIs or download files from the terminal."},
    {"cmd": "man", "desc": "Opens the manual page for a command, giving you the full documentation right in your terminal."},
    {"cmd": "top", "desc": "The classic real-time view of running processes and system resource usage."},
    {"cmd": "history", "desc": "Shows a list of the commands you've previously run in your terminal session."},
    {"cmd": "clear", "desc": "Wipes your terminal screen clean, giving you a fresh, empty prompt."},
    {"cmd": "systemctl", "desc": "Used to control and inspect systemd services, like starting, stopping, or checking a background daemon."},
    {"cmd": "journalctl", "desc": "Lets you view and filter logs collected by the systemd journal."}
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
    "https://media.tenor.com/7D-R9eYf6W8AAAAC/linux-penguin.gif",
    "https://media.tenor.com/V-nF03F5h20AAAAC/linux-arch.gif"
]

TANK_FACTS = [
    "The British Mark I was the very first tank to enter combat during the Battle of the Flers-Courcelette back in 1916.",
    "Major General Ernest Swinton is largely credited with the initial concept of armored tracked vehicles.",
    "The German Tiger I featured an 88mm KwK 36 gun, which was actually designed as an anti-aircraft flak cannon first.",
    "Sloped armor, famously used on the Soviet T-34, artificially increases the thickness of the armor against incoming shells.",
    "The Panzerkampfwagen VI Tiger weighed nearly 57 tons, making it one of the heaviest production tanks fielded during WWII.",
    "The M1 Abrams runs on a gas turbine engine, similar in principle to a helicopter's engine, instead of a traditional diesel.",
    "The Soviet IS-2 heavy tank was named after Joseph Stalin, with 'IS' standing for 'Iosif Stalin'.",
    "During WWI, early armored vehicles were code-named 'tanks' by the British to disguise them as water-carrying containers during transport.",
    "The French Renault FT, introduced in 1917, pioneered the now-standard tank layout with a fully rotating turret on top of the hull.",
    "Modern main battle tanks like the Leopard 2 use layered composite armor to defeat both kinetic penetrators and shaped-charge warheads."
]

MMA_FACTS = [
    "Jon 'Bones' Jones became the youngest champion in UFC history at the age of 23.",
    "The traditional Octagon was created to avoid the disadvantages of a square boxing ring, preventing fighters from getting trapped in corners.",
    "Brazilian Jiu-Jitsu rose to global fame after Royce Gracie dominated the first, second, and fourth UFC tournaments.",
    "Anderson Silva held the UFC Middleweight Championship for a record-setting 2,457 consecutive days.",
    "The UFC was founded in 1993 and originally had almost no weight classes, time limits, or many of today's safety rules.",
    "Georges St-Pierre is one of the few fighters in UFC history to hold championship belts in two different weight classes.",
    "Muay Thai is often nicknamed 'The Art of Eight Limbs' because fighters strike with fists, elbows, knees, and shins.",
    "Khabib Nurmagomedov retired from professional MMA with a perfect, undefeated record of 29 wins and 0 losses.",
    "Many Brazilian Jiu-Jitsu submissions and Judo throws share historical roots, both having evolved out of traditional Japanese jujutsu."
]

TECH_JOKES = [
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I'd tell you a joke about UDP, but you probably wouldn't get it.",
    "Why do Java developers wear glasses? Because they don't see sharp.",
    "A SQL query walks into a bar, walks up to two tables, and asks: 'Can I join you?'",
    "Why was the computer cold? It left its Windows open.",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
    "I would tell you a joke about recursion, but I'd have to tell you a joke about recursion first.",
    "Why do programmers always mix up Halloween and Christmas? Because Oct 31 equals Dec 25.",
    "There's no place like 127.0.0.1.",
    "Why did the developer go broke? Because he used up all of his cache."
]

PYTHON_TIPS = [
    "Use list comprehensions to write cleaner and faster code: `[x**2 for x in range(10)]`",
    "Did you know? You can swap two variables easily without a temporary variable: `a, b = b, a`",
    "Use `enumerate()` if you need both the index and the value while looping through an iterable.",
    "Use f-strings for cleaner formatting: `f'Result: {value}'` is faster and easier to read than `.format()`.",
    "The `zip()` function lets you loop over multiple lists in parallel: `for a, b in zip(list1, list2):`",
    "Use `collections.Counter` to quickly count how many times each item appears in a list.",
    "Dictionary comprehensions work just like list comprehensions: `{k: v for k, v in items}`",
    "Use `with open(...) as f:` when working with files so they get closed automatically, even if an error occurs.",
    "The walrus operator `:=` lets you assign and use a value in the same expression (Python 3.8+).",
    "Use `*args` and `**kwargs` in your function definitions to accept a flexible number of arguments.",
    "Prefer `pathlib.Path` over manual string concatenation when working with file paths."
]

ALL_DISTRO_ROLES = [
    1521868543799328808, 1521870392472502344, 1521870674669338654, 1521871074994950295, 1521871078308184074,
    1521870173861056655, 1521871399403393044, 1521871679368986655, 1521871896117776468,
    1521870110552227910, 1521868791942742026, 1521871613958819860, 1521871816321404969, 1521872016901406720,
    1521870225228955798, 1521872173688422420, 1521872360393670819, 1521872534117679206, 1521872635968098344,
    1521872683803873432, 1521872759691542588, 1521873026776301608, 1521873129868365964,
    1521909235594825941, 1521909235594825999,
    1522137195102867526, 1522137253856415784, 1522143963904081920,
    1521909451739893982, 1521909341802725427, 1522212167393214514, 1522212092663300248,
    1522211951709519872, 1522211033073324234, 1522211796532854826, 1522211599744499834,
    1521909403496742973
]
ALL_GPU_ROLES = [1521879270530486414, 1521879224951246928, 1521879315648614410]

STRICT_BANNED_WORDS = {
    "nigger", "nigga", "porn", "porno", "sex", "pussy", "fuck", 
    "bitch", "cunt", "dick", "asshole", "slut", "whore", 
    "faggot", "childporn", "rape", "pusy", "fck", "btch", "cp"
}

SQUISHED_SEVERE_WORDS = ["fuck", "nigger", "nigga", "porn", "pussy", "bitch", "faggot", "whore"]

# NOT: 'v': 'u' eşleşmesi kaldırıldı; normal kelimelerdeki 'v' harflerini gereksiz yere
# bozarak yanlış pozitif (masum kelimenin yasaklı sayılması) riskini artırıyordu.
LEET_DICT = {'@': 'a', '4': 'a', '1': 'i', '!': 'i', '0': 'o', '3': 'e', '$': 's', '5': 's', '7': 't', '+': 't'}

# "f.u.c.k" veya "f_u_c_k" gibi noktalama ile bölünmüş yazımları birleştirmek için kaldırılan karakterler.
# Gerçek boşluklara DOKUNULMUYOR, böylece farklı kelimeler birbirine karışmıyor.
OBFUSCATION_CHARS_TABLE = str.maketrans('', '', ".,*_~'\"-|")

def normalize_for_filter(text):
    text = text.lower()
    for k, v in LEET_DICT.items():
        text = text.replace(k, v)
    text = unidecode(text)
    text = text.translate(OBFUSCATION_CHARS_TABLE)
    return text

def collapse_repeats(word):
    # Sadece 3 veya daha fazla art arda gelen AYNI harfi tek harfe indirir (örn: "fuuuuck" -> "fuck").
    # Eski kod 2 tekrarı bile indiriyordu (örn: "book" -> "bok"), bu da normal, çift harfli
    # kelimelerin yanlışlıkla farklı bir kelimeye dönüşme riskini artırıyordu. Artık daha güvenli.
    return re.sub(r'(.)\1{2,}', r'\1', word)

def clean_text_for_filter(text):
    # Geriye dönük uyumluluk için tutuluyor; artık normalize_for_filter'a yönlendiriyor.
    return normalize_for_filter(text)

def strip_html_tags(raw_html):
    """RSS özetlerinin içindeki HTML etiketlerini temizler, embed içinde çirkin görünmesini engeller."""
    if not raw_html:
        return ""
    clean = re.sub('<[^<]+?>', '', raw_html)
    clean = (clean.replace('&nbsp;', ' ')
                  .replace('&amp;', '&')
                  .replace('&#8217;', "'")
                  .replace('&#8216;', "'")
                  .replace('&quot;', '"')
                  .replace('&#8220;', '"')
                  .replace('&#8221;', '"'))
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def is_heavy_swear(text):
    """
    AKILLI KÜFÜR FİLTRESİ:
    Eski sistem tüm mesajı boşluksuz tek bir bloğa çeviriyordu; bu yüzden "cucumber" gibi tamamen
    masum bir kelime, mesajdaki komşu kelimelerle birleşince yanlışlıkla yasaklı kelime gibi
    algılanabiliyordu. Yeni sistem her kelimeyi TEK TEK ve kelime sınırlarına saygı duyarak
    kontrol eder; böylece farklı kelimeler birbirine karışıp yanlış alarm üretemez.
    Yine de şunları yakalamaya devam eder:
      1) Leetspeak yazımlar (n1gg3r, sh!t gibi)
      2) Harf uzatma bypass'ı (fuuuuck gibi)
      3) Noktalama ile bölünmüş yazımlar (f.u.c.k, f_u_c_k gibi)
      4) Harf harf boşluklu yazımlar (f u c k gibi)
    """
    normalized = normalize_for_filter(text)
    raw_tokens = normalized.split()
    clean_tokens = [re.sub(r'[^a-z]', '', t) for t in raw_tokens]
    clean_tokens = [t for t in clean_tokens if t]

    for token in clean_tokens:
        if token in STRICT_BANNED_WORDS:
            return True
        collapsed = collapse_repeats(token)
        if collapsed in STRICT_BANNED_WORDS:
            return True

    # Harf harf boşluklu bypass denemelerini yakalamak için: ardışık tek harfli
    # token'ları geçici olarak birleştirip kontrol ediyoruz (örn: "f u c k" -> "fuck").
    buffer = ""
    for token in clean_tokens:
        if len(token) == 1:
            buffer += token
            continue
        if len(buffer) >= 3:
            collapsed_buffer = collapse_repeats(buffer)
            for severe_word in SQUISHED_SEVERE_WORDS:
                if severe_word in buffer or severe_word in collapsed_buffer:
                    return True
        buffer = ""
    if len(buffer) >= 3:
        collapsed_buffer = collapse_repeats(buffer)
        for severe_word in SQUISHED_SEVERE_WORDS:
            if severe_word in buffer or severe_word in collapsed_buffer:
                return True

    return False

MONGO_URI = os.environ.get("MONGO_URI")

try:
    mongo_client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = mongo_client["AdminPinguDB"]
    xp_collection = db["users_xp"]
    config_collection = db["server_config"]
    warnings_collection = db["user_warnings"]  # YENİ: Uyarılar artık kalıcı olarak Mongo'da tutuluyor
except Exception as e:
    print(f"MongoDB Initialization Error: {e}")

warning_db = {}  # Mongo'ya ulaşılamazsa devreye giren yedek (fallback) hafıza
user_message_cache = {} 
xp_message_counter = {} 
LAST_NEWS_URL = "" 
last_activity_time = time.time()  # YENİ: Reminder görevinin sohbet aktivitesini takip etmesi için

def get_xp_requirement(level):
    """
    Belirtilen seviyeye ulaşmak için gereken TOPLAM (kümülatif) XP miktarını döndürür.
    Örnek: Level 1 -> 0 XP, Level 2 -> 100 XP, Level 3 -> 200 XP, Level 4 -> 400 XP,
    Level 5 -> 600 XP, Level 6 -> 900 XP, Level 7 -> 1200 XP ...
    Büyüme SÜREKLİ ikiye katlanmaz; her 2 seviyede bir kademeli olarak artar. Böylece hem
    başlangıçta akıcı bir ilerleme olur, hem de ileri seviyelerde XP ihtiyacı çılgınca
    patlamaz (ne çok kolay, ne çok zor).
    """
    n = level - 1
    if n <= 0:
        return 0
    k = n // 2
    if n % 2 == 0:
        total_units = k * (k + 1)
    else:
        total_units = (k + 1) ** 2
    return total_units * 100

async def save_event_state(channel_id, ends_at_timestamp):
    try:
        await config_collection.update_one(
            {"_id": "global_event_state"},
            {"$set": {"active_channel_id": channel_id, "ends_at": ends_at_timestamp}},
            upsert=True
        )
    except Exception as e:
        print(f"Event state save error: {e}")

async def clear_event_state():
    try:
        await config_collection.update_one(
            {"_id": "global_event_state"},
            {"$set": {"active_channel_id": None, "ends_at": None}},
            upsert=True
        )
    except Exception as e:
        print(f"Event state clear error: {e}")

async def load_event_state():
    try:
        return await config_collection.find_one({"_id": "global_event_state"})
    except Exception as e:
        print(f"Event state load error: {e}")
        return None

async def resume_event_countdown(channel, remaining_seconds, announcement_channel_id):
    """Bot yeniden başlatıldığında devam eden bir 3x XP etkinliğinin geri kalan süresini tamamlar."""
    global ACTIVE_EVENT_CHANNEL_ID
    try:
        await asyncio.sleep(remaining_seconds)
        try:
            await channel.delete()
        except Exception:
            pass
        ACTIVE_EVENT_CHANNEL_ID = None
        await clear_event_state()
        announcement_channel = bot.get_channel(announcement_channel_id)
        if announcement_channel:
            await announcement_channel.send("🛑 **THE SUNDAY 3X XP EVENT HAS CONCLUDED!** The rift has collapsed and the channel has been erased. See you all next week!")
    except Exception as e:
        print(f"Event resume error: {e}")

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
        old_level = user_data.get("level", 1)
        new_level = old_level
        # BUG FIX: 'if' yerine 'while' kullanıyoruz. Böylece tek bir mesajda (örneğin 3x XP
        # etkinliğinde) birden fazla seviye birden atlanırsa, hiçbir seviye atlaması kaçırılmaz.
        while new_total >= get_xp_requirement(new_level + 1):
            new_level += 1
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
        levels_gained = list(range(old_level + 1, new_level + 1)) if new_level > old_level else []
        return levels_gained
    except Exception as e:
        print(f"Database access error (add_xp): {e}")
        return []

class DistroSelect(Select):
    def __init__(self, placeholder, options, custom_id):
        super().__init__(placeholder=placeholder, min_values=0, max_values=2, options=options, custom_id=custom_id)
        self.menu_role_ids = [int(opt.value) for opt in options]

    async def callback(self, interaction: discord.Interaction):
        selected_role_ids = [int(v) for v in self.values]
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
            discord.SelectOption(label="Windows 10", value="1521909403496742973"),
            discord.SelectOption(label="Windows 8", value="1521909451739893982"),
            discord.SelectOption(label="Windows 7", value="1521909341802725427"),
            discord.SelectOption(label="Windows Vista", value="1522212167393214514"),
            discord.SelectOption(label="Windows XP", value="1522212092663300248"),
            discord.SelectOption(label="FreeBSD", value="1521909235594825999"),
            discord.SelectOption(label="GhostBSD", value="1522211951709519872"),
            discord.SelectOption(label="OpenBSD", value="1522211033073324234"),
            discord.SelectOption(label="DragonFly BSD", value="1522211796532854826"),
            discord.SelectOption(label="NetBSD", value="1522211599744499834")
        ]
        self.add_item(DistroSelect(placeholder="Windows & BSD Family", options=win_bsd_opts, custom_id="win_bsd_menu"))
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

@tasks.loop(minutes=30)
async def half_hourly_reminder():
    await bot.wait_until_ready()
    global REMINDER_CHANNEL_ID, last_activity_time
    # BUG FIX / YENİ: Sohbette uzun süredir kimse mesaj atmadıysa hatırlatmayı gönderme.
    if time.time() - last_activity_time > REMINDER_INACTIVITY_THRESHOLD_SECONDS:
        return
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
        # BUG FIX: RSS özetindeki HTML etiketleri artık temizleniyor, embed daha temiz görünüyor.
        clean_summary = strip_html_tags(entry.summary) if hasattr(entry, "summary") else ""
        embed = discord.Embed(
            title=f"📰 {entry.title}", 
            url=entry.link, 
            description=clean_summary[:500] + ("..." if len(clean_summary) > 500 else ""), 
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

@tasks.loop(time=datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc))
async def sunday_xp_event():
    await bot.wait_until_ready()
    global ACTIVE_EVENT_CHANNEL_ID
    now = datetime.datetime.now(datetime.timezone.utc)
    if now.weekday() != 6: 
        return
    category = bot.get_channel(1510339895032418506)
    if not category:
        return
    guild = category.guild
    try:
        event_channel = await guild.create_text_channel(
            name="🔥-triple-xp-chaos",
            category=category,
            topic="3X XP EVENT CHANNEL! 10s cooldown. Spam filter disabled. Deletes in 3 hours.",
            slowmode_delay=10
        )
        ACTIVE_EVENT_CHANNEL_ID = event_channel.id
        event_duration_seconds = 3 * 60 * 60
        # YENİ: Etkinlik durumu Mongo'ya kaydediliyor; bot yeniden başlarsa etkinlik kaybolmuyor.
        await save_event_state(event_channel.id, time.time() + event_duration_seconds)
        await event_channel.send(
            "🚨 **THE RIFT HAS OPENED! TRIPLE XP IS NOW ACTIVE!** 🚨\n\n"
            "Welcome to the Chaos Zone. For the next **3 HOURS**, every message you send here grants **3X XP**! "
            "The standard bot spam filter has been lifted, but you must survive the 10-second cooldown.\n\n"
            "Grind your hearts out. The countdown to destruction has begun! ⏳"
        )
        announcement_channel = bot.get_channel(1522172546714308648)
        if announcement_channel:
            await announcement_channel.send(f"⚡ **THE SUNDAY EVENT HAS BEGUN!** A dimensional rift just opened at {event_channel.mention}. Get in there for **3X XP**! The channel will self-destruct in exactly 3 hours.")
        await asyncio.sleep(event_duration_seconds)
        if event_channel:
            await event_channel.delete()
        ACTIVE_EVENT_CHANNEL_ID = None
        await clear_event_state()
        if announcement_channel:
            await announcement_channel.send("🛑 **THE SUNDAY 3X XP EVENT HAS CONCLUDED!** The rift has collapsed and the channel has been erased. See you all next week!")
    except Exception as e:
        print(f"Sunday Event Error: {e}")
        ACTIVE_EVENT_CHANNEL_ID = None
        await clear_event_state()

@bot.event
async def on_ready():
    print('==========================================')
    print(f'🤖 Bot Is Online: {bot.user.name}')
    print('🚀 Engine Status: READY AND OPERATIONAL')
    print('==========================================')
    global last_activity_time, ACTIVE_EVENT_CHANNEL_ID
    last_activity_time = time.time()
    # BUG FIX: MongoDB bağlantısı artık başlangıçta test ediliyor, hata sessizce yutulmuyor.
    try:
        await mongo_client.admin.command('ping')
        print('✅ MongoDB Connection: Successfully established and verified.')
    except Exception as e:
        print('❌ MongoDB Connection Error: Database is NOT reachable! XP, warnings and configs will fail to save.')
        print(f'   Details: {e}')
    await bot.change_presence(activity=discord.Game(name="Managing the Server | ?help"))
    half_hourly_reminder.start()
    reset_daily_xp.start()
    daily_tech_news.start()
    sunday_xp_event.start() 
    bot.add_view(RolesView())
    # YENİ: Bot yeniden başladıysa devam eden bir 3x XP etkinliği var mı diye kontrol ediyoruz.
    try:
        state = await load_event_state()
        if state and state.get("active_channel_id"):
            remaining = state.get("ends_at", 0) - time.time()
            channel = bot.get_channel(int(state["active_channel_id"]))
            if remaining > 0 and channel:
                ACTIVE_EVENT_CHANNEL_ID = channel.id
                asyncio.create_task(resume_event_countdown(channel, remaining, 1522172546714308648))
                print(f"🔥 Restored active 3X XP event, {int(remaining)}s remaining.")
            else:
                if channel:
                    try:
                        await channel.delete()
                    except Exception:
                        pass
                await clear_event_state()
    except Exception as e:
        print(f"Event state restore error: {e}")

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
    total_warns = None
    try:
        await warnings_collection.update_one(
            {"_id": member.id},
            {
                "$inc": {"count": 1},
                "$push": {"history": {"reason": reason, "timestamp": time.time()}}
            },
            upsert=True
        )
        warning_doc = await warnings_collection.find_one({"_id": member.id})
        total_warns = warning_doc.get("count", 1) if warning_doc else 1
    except Exception as e:
        print(f"Warning DB error (falling back to memory): {e}")
    if total_warns is None:
        # BUG FIX: Veritabanına ulaşılamazsa uyarı sistemi tamamen çökmesin diye hafızada devam ediyoruz.
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
        try:
            await warnings_collection.update_one({"_id": member.id}, {"$set": {"count": 0}}, upsert=True)
        except Exception as e:
            print(f"Warning reset DB error: {e}")
        warning_db[member.id] = 0

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    global last_activity_time
    last_activity_time = time.time()  # YENİ: Her insan mesajında aktivite zamanı güncelleniyor
    is_mod = message.author.guild_permissions.manage_messages
    if not is_mod:
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
    try:
        author_id = message.author.id
        if author_id not in xp_message_counter:
            xp_message_counter[author_id] = 0
        xp_message_counter[author_id] += 1
        if xp_message_counter[author_id] >= 3:
            xp_message_counter[author_id] = 0 
            gained = random.randint(5, 30) 
            if message.channel.id == ACTIVE_EVENT_CHANNEL_ID:
                gained *= 3
            # BUG FIX: Tek bir XP kazanımında birden fazla seviye atlanabilir (özellikle 3x etkinlikte),
            # bu yüzden atlanan TÜM seviyeler işleniyor, sadece sonuncusu değil.
            levels_gained = await add_xp(author_id, gained)
            for new_level in levels_gained:
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
    await ctx.send(f"✅ The automated rules reminder will now be sent to {target_channel.mention} (only when the chat has been active recently).")

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
@commands.has_permissions(kick_members=True)
async def warnings(ctx, member: discord.Member):
    """YENİ KOMUT: Bir kullanıcının Mongo'da kayıtlı uyarı geçmişini gösterir."""
    try:
        doc = await warnings_collection.find_one({"_id": member.id})
    except Exception as e:
        return await ctx.send(f"❌ Database error: {e}")
    count = doc.get("count", 0) if doc else warning_db.get(member.id, 0)
    embed = discord.Embed(title=f"📋 Warning History: {member.name}", color=discord.Color.orange())
    embed.add_field(name="Current Warnings", value=f"`{count}/5`", inline=False)
    if doc and doc.get("history"):
        recent = doc["history"][-5:]
        history_str = "\n".join(
            [f"• `{datetime.datetime.fromtimestamp(h['timestamp']).strftime('%Y-%m-%d %H:%M')}` - {h['reason']}" for h in recent]
        )
        embed.add_field(name="Recent History (Last 5)", value=history_str, inline=False)
    else:
        embed.add_field(name="Recent History", value="No warnings recorded.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def clearwarnings(ctx, member: discord.Member):
    """YENİ KOMUT: Bir kullanıcının tüm uyarılarını sıfırlar (hem Mongo hem de yedek hafıza)."""
    try:
        await warnings_collection.update_one({"_id": member.id}, {"$set": {"count": 0, "history": []}}, upsert=True)
        warning_db[member.id] = 0
        await ctx.send(f"✅ All warnings cleared for {member.mention}.")
    except Exception as e:
        await ctx.send(f"❌ Database error: {e}")

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
    prev_level_xp = get_xp_requirement(current_level)
    next_level_xp = get_xp_requirement(current_level + 1)
    xp_into_level = current_xp - prev_level_xp
    xp_needed_for_level = next_level_xp - prev_level_xp 
    percentage = min(max(xp_into_level / xp_needed_for_level, 0.0), 1.0) if xp_needed_for_level > 0 else 1.0
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
              "`?warnings <user>` - Shows a user's warning history\n"
              "`?clearwarnings <user>` - Resets a user's warnings to 0\n"
              "`?ban <user> [reason]` / `?unban <id>` - Manages bans\n"
              "`?setnewschannel` - Sets the channel for tech news\n"
              "`?setjoinchannel` - Sets the channel for welcome banners\n"
              "`?messagesendadminpingu` - Sets the channel for the automated rules reminder", 
            inline=False
    )
    embed.add_field(
        name="📊 Stats & Utilities", 
        value="`?stats [user]` - View a user's level and XP\n"
              "`?leaderstats` - See the top 15 users in the server\n"
              "`?serverinfo` - Display information about this server", 
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

@bot.listen()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **Access Denied:** You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Syntax Error:** You are missing some arguments! Check `?help` for usage.")
    else:
        pass 

keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
