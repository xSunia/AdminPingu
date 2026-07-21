import discord
from discord.ext import commands, tasks
from discord.ui import Select, View, Modal, TextInput
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
import ast
import traceback
import io
import sys
import difflib
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
intents.voice_states = True

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

BOT_START_TIME = time.time()

LOG_CHANNEL_ID = 123456789012345678       
WARNINGS_CHANNEL_ID = 1521880436270301354 
LEVEL_LOG_CHANNEL_ID = 1521880096854769785
REMINDER_CHANNEL_ID = 123456789012345678  
EPIC_LEVEL_100_CHANNEL = 1510339895032418508 

USER_ROLE_ID = 1510547520273649704        
MEDIA_ROLE_ID = 1521875919864856714       

ACTIVE_EVENT_CHANNEL_ID = None
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

LEET_DICT = {'@': 'a', '4': 'a', '1': 'i', '!': 'i', '0': 'o', '3': 'e', '$': 's', '5': 's', '7': 't', '+': 't'}

OBFUSCATION_CHARS_TABLE = str.maketrans('', '', ".,*_~'\"-|")

def normalize_for_filter(text):
    text = text.lower()
    for k, v in LEET_DICT.items():
        text = text.replace(k, v)
    text = unidecode(text)
    text = text.translate(OBFUSCATION_CHARS_TABLE)
    return text

def collapse_repeats(word):
    return re.sub(r'(.)\1{2,}', r'\1', word)

def clean_text_for_filter(text):
    return normalize_for_filter(text)

def strip_html_tags(raw_html):
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
    warnings_collection = db["user_warnings"]
    customizations_collection = db["customizations"]
except Exception as e:
    print(f"MongoDB Initialization Error: {e}")

warning_db = {}
user_message_cache = {} 
xp_message_counter = {} 
voice_sessions = {}
LAST_NEWS_URL = "" 
last_activity_time = time.time()

def _xp_delta_for_level(level):
    base = 51.824 * (level ** 1.166)
    if level >= 90:
        t = (level - 89) / 10.0
        hard_multiplier = 1.0 + 1.6 * (t ** 1.6)
    else:
        hard_multiplier = 1.0
    return max(50, round(base * hard_multiplier))

_MAX_PRECOMPUTED_LEVEL = 200
_XP_REQUIREMENT_TABLE = [0]
for _lvl in range(1, _MAX_PRECOMPUTED_LEVEL + 1):
    _XP_REQUIREMENT_TABLE.append(_XP_REQUIREMENT_TABLE[-1] + _xp_delta_for_level(_lvl))

def get_xp_requirement(level):
    if level <= 0:
        return 0
    if level < len(_XP_REQUIREMENT_TABLE):
        return _XP_REQUIREMENT_TABLE[level]
    total = _XP_REQUIREMENT_TABLE[-1]
    for lvl in range(_MAX_PRECOMPUTED_LEVEL + 1, level + 1):
        total += _xp_delta_for_level(lvl)
    return total

def get_level_from_total_xp(total_xp):
    level = 1
    while total_xp >= get_xp_requirement(level + 1):
        level += 1
    return level

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
        new_total = user_data.get("total", 0) + amount
        new_daily = user_data.get("daily", 0) + amount
        new_weekly = user_data.get("weekly", 0) + amount
        new_monthly = user_data.get("monthly", 0) + amount
        old_level = user_data.get("level", 1)
        new_level = get_level_from_total_xp(new_total)
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

class FontSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Arial", value="arial"),
            discord.SelectOption(label="Impact", value="impact"),
            discord.SelectOption(label="Terminus", value="terminus"),
            discord.SelectOption(label="Courier", value="courier"),
            discord.SelectOption(label="Comic Sans", value="comic"),
            discord.SelectOption(label="Verdana", value="verdana"),
            discord.SelectOption(label="Georgia", value="georgia"),
            discord.SelectOption(label="Tahoma", value="tahoma"),
            discord.SelectOption(label="Trebuchet", value="trebuchet"),
            discord.SelectOption(label="Lucida", value="lucida"),
            discord.SelectOption(label="Garamond", value="garamond"),
            discord.SelectOption(label="Palatino", value="palatino"),
            discord.SelectOption(label="Bookman", value="bookman"),
            discord.SelectOption(label="Helvetica", value="helvetica"),
            discord.SelectOption(label="Calibri", value="calibri")
        ]
        super().__init__(placeholder="Select a Custom Font", min_values=1, max_values=1, options=options, custom_id="font_select")

    async def callback(self, interaction: discord.Interaction):
        await customizations_collection.update_one({"_id": interaction.user.id}, {"$set": {"font": self.values[0]}}, upsert=True)
        await interaction.response.send_message(f"✅ Your font preference has been saved to: `{self.values[0]}`", ephemeral=True)

class TemplateSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Neon Hacker", value="neon"),
            discord.SelectOption(label="Retro Synth", value="retro"),
            discord.SelectOption(label="Dark Matter", value="dark"),
            discord.SelectOption(label="Cyberpunk", value="cyber"),
            discord.SelectOption(label="Minimalist Light", value="light")
        ]
        super().__init__(placeholder="Select a Preset Color Template", min_values=1, max_values=1, options=options, custom_id="template_select")

    async def callback(self, interaction: discord.Interaction):
        await customizations_collection.update_one({"_id": interaction.user.id}, {"$set": {"template": self.values[0]}}, upsert=True)
        await interaction.response.send_message(f"✅ Your template schema has been set to: `{self.values[0]}`", ephemeral=True)

class RGBColorModal(Modal, title="Custom 16 Million RGB Colors"):
    text_color = TextInput(
        label="Text Hex Color (e.g., #FFFFFF)",
        placeholder="#FFFFFF",
        required=False,
        max_length=7
    )
    bar_color = TextInput(
        label="XP Progress Bar Hex Color (e.g., #00FFCC)",
        placeholder="#00FFCC",
        required=False,
        max_length=7
    )
    accent_color = TextInput(
        label="Card Border / Accent Hex Color (e.g., #FF0055)",
        placeholder="#FF0055",
        required=False,
        max_length=7
    )

    async def on_submit(self, interaction: discord.Interaction):
        update_dict = {}
        if self.text_color.value:
            update_dict["custom_text_color"] = self.text_color.value.strip()
        if self.bar_color.value:
            update_dict["custom_bar_color"] = self.bar_color.value.strip()
        if self.accent_color.value:
            update_dict["custom_accent_color"] = self.accent_color.value.strip()

        if update_dict:
            await customizations_collection.update_one({"_id": interaction.user.id}, {"$set": update_dict}, upsert=True)
            await interaction.response.send_message("✅ Your custom 16M RGB colors have been applied!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ No valid hex color values were provided.", ephemeral=True)

class CustomizeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FontSelect())
        self.add_item(TemplateSelect())

    @discord.ui.button(label="🎨 Custom 16M RGB Colors", style=discord.ButtonStyle.primary, custom_id="custom_rgb_btn")
    async def rgb_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RGBColorModal())

    @discord.ui.button(label="✅ Save & Finish", style=discord.ButtonStyle.success, custom_id="finish_custom_btn")
    async def finish_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="✅ Customization menu closed! Use `?stats` or `/stats` to preview your card.", view=None)

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
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permissions to use this command.", ephemeral=True)
    else:
        print(f"Unhandled command error in {ctx.command}: {error}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    print(f"Unhandled App Command Error: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message("❌ An unexpected system error occurred.", ephemeral=True)

@bot.event
async def on_ready():
    print('==========================================')
    print(f'🤖 Bot Is Online: {bot.user.name}')
    print('🚀 Engine Status: READY AND OPERATIONAL')
    print('==========================================')
    global last_activity_time, ACTIVE_EVENT_CHANNEL_ID
    last_activity_time = time.time()
    try:
        await mongo_client.admin.command('ping')
        print('✅ MongoDB Connection: Successfully established and verified.')
        try:
            xp_count = await xp_collection.count_documents({})
            warn_count = await warnings_collection.count_documents({})
            config_count = await config_collection.count_documents({})
            print(f'   📊 users_xp: {xp_count} | user_warnings: {warn_count} | server_config: {config_count}')
        except Exception as ce:
            print(f'   ⚠️ Could not count collections: {ce}')
    except Exception as e:
        print('❌ MongoDB Connection Error: Database is NOT reachable!')
        print(f'   Details: {e}')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Slash Commands: {len(synced)} command(s) synced globally.')
    except Exception as e:
        print(f'❌ Slash Command Sync Error: {e}')
    await bot.change_presence(activity=discord.Game(name="Managing the Server | ?help or /help"))
    half_hourly_reminder.start()
    reset_daily_xp.start()
    daily_tech_news.start()
    sunday_xp_event.start() 
    bot.add_view(RolesView())
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
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    if before.channel is None and after.channel is not None:
        voice_sessions[member.id] = time.time()
    elif before.channel is not None and after.channel is None:
        if member.id in voice_sessions:
            join_time = voice_sessions.pop(member.id)
            duration = time.time() - join_time
            minutes = int(duration // 60)
            if minutes > 0:
                xp_gained = minutes * 2
                if duration >= 7200:
                    xp_gained += 5000
                await add_xp(member.id, xp_gained)

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
        print(f"Warning DB error: {e}")
    if total_warns is None:
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
                await admin.send(f"🚨 **Administrator Alert:** The user {member.mention} (`{member.name}`) has reached the **5/5 warning limit** in {guild.name}.")
            except Exception:
                pass
        if warn_channel:
            await warn_channel.send(f"🚨 {member.mention} has hit the 5-warning limit! Server administrators have been notified via DM.")
        try:
            await warnings_collection.update_one({"_id": member.id}, {"$set": {"count": 0}}, upsert=True)
        except Exception as e:
            print(f"Warning reset DB error: {e}")
        warning_db[member.id] = 0

def check_code_safety(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "Security Error: Imports are disabled in the sandbox."
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['open', 'eval', 'exec', '__import__', 'globals', 'locals', 'compile', 'input']:
                    return False, f"Security Error: The function `{node.func.id}` is blocked in the sandbox."
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ['system', 'popen', 'spawn', 'run']:
                    return False, f"Security Error: The attribute `{node.func.attr}` is blocked."
    return True, ""

def execute_sandbox_sync(code):
    safe, msg = check_code_safety(code)
    if not safe:
        return msg

    output_buffer = io.StringIO()

    def custom_print(*args, sep=' ', end='\n', file=None):
        if file is None:
            output_buffer.write(sep.join(map(str, args)) + end)
        else:
            file.write(sep.join(map(str, args)) + end)

    safe_builtins = {
        'print': custom_print, 'range': range, 'len': len, 'int': int, 'float': float,
        'str': str, 'bool': bool, 'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
        'sum': sum, 'min': min, 'max': max, 'abs': abs, 'round': round, 'type': type,
        'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError,
        'IndexError': IndexError, 'KeyError': KeyError, 'ZeroDivisionError': ZeroDivisionError,
        'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter, 'all': all, 'any': any,
        'sorted': sorted, 'reversed': reversed, 'isinstance': isinstance, 'issubclass': issubclass,
        'chr': chr, 'ord': ord, 'hex': hex, 'oct': oct, 'bin': bin
    }
    safe_env = {'__builtins__': safe_builtins}
    
    try:
        exec(code, safe_env, safe_env)
    except Exception as e:
        output_buffer.write("".join(traceback.format_exception_only(type(e), e)).strip() + "\n")
        
    return output_buffer.getvalue()

async def execute_sandbox(code):
    loop = asyncio.get_running_loop()
    try:
        future = loop.run_in_executor(None, execute_sandbox_sync, code)
        output = await asyncio.wait_for(future, timeout=3.0)
        return output
    except asyncio.TimeoutError:
        return "Timeout Error: Code execution took too long."
    except Exception as e:
        return f"Execution Error: {e}"

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
        
    if message.channel.category_id == 1510339895032418506 and message.channel.name.startswith("terminal-"):
        is_mod = message.author.guild_permissions.manage_messages
        is_owner = str(message.author.id) in (message.channel.topic or "")
        
        if is_owner or is_mod:
            code = message.content.strip()
            
            if code.lower() in ['exit()', 'close()', 'exit', 'close', '?close']:
                await message.channel.delete(reason="User closed terminal.")
                return

            if code.startswith("```python"): code = code[9:]
            elif code.startswith("```py"): code = code[5:]
            elif code.startswith("```"): code = code[3:]
            if code.endswith("```"): code = code[:-3]
            code = code.strip()

            if not code: return

            await message.add_reaction("⏳")
            output = await execute_sandbox(code)
            
            if len(output) > 1900:
                output = output[:1900] + "\n... [Output Truncated]"
            if not output.strip():
                output = "Code executed successfully (no output)."

            await message.channel.send(f"```python\n{output}\n```")
            try:
                await message.remove_reaction("⏳", bot.user)
            except Exception:
                pass
            return 
    
    global last_activity_time
    last_activity_time = time.time()
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

    handled_by_shortcut = await try_smart_command_match(message)
    if handled_by_shortcut:
        return
    await bot.process_commands(message)

async def try_smart_command_match(message):
    prefix = "?"
    if message.author.bot or not message.content.startswith(prefix):
        return False
    body = message.content[len(prefix):].strip()
    if not body:
        return False
    parts = body.split(maxsplit=1)
    typed_cmd = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if bot.get_command(typed_cmd) is not None:
        return False

    if len(typed_cmd) < 2:
        return False

    all_cmds = []
    cmd_map = {}
    for cmd in bot.commands:
        all_cmds.append(cmd.name)
        cmd_map[cmd.name] = cmd.name
        for alias in cmd.aliases:
            all_cmds.append(alias)
            cmd_map[alias] = cmd.name

    matches = difflib.get_close_matches(typed_cmd, all_cmds, n=1, cutoff=0.4)
    if matches:
        best_match = cmd_map[matches[0]]
        message.content = f"{prefix}{best_match} {rest}".strip()
        await bot.process_commands(message)
        return True

    return False

@bot.hybrid_command(name="terminal", aliases=["term"], description="Opens a private Python sandbox terminal.")
async def terminal(ctx):
    category = bot.get_channel(1510339895032418506)
    if not category:
        return await ctx.send("❌ Error: The required category for terminals was not found.", ephemeral=True)
        
    existing_channel = discord.utils.get(category.text_channels, name=f"terminal-{ctx.author.name.lower()}")
    if existing_channel:
        return await ctx.send(f"❌ You already have an active terminal: {existing_channel.mention}", ephemeral=True)

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }
    
    for role in ctx.guild.roles:
        if role.permissions.manage_messages:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
    term_channel = await ctx.guild.create_text_channel(
        name=f"terminal-{ctx.author.name}",
        category=category,
        overwrites=overwrites,
        topic=f"{ctx.author.id}"
    )
    
    embed = discord.Embed(
        title="🐍 Python Sandbox Terminal",
        description=f"Welcome {ctx.author.mention}! This channel is your isolated Python environment.\n\n"
                    f"🔒 **Security Rules:**\n"
                    f"• Imports, file I/O, and dangerous functions are strictly **BLOCKED**.\n"
                    f"• Infinite loops will automatically time out after 3 seconds.\n"
                    f"• You cannot interact with or harm the Discord bot or the server.\n\n"
                    f"💡 **How to use:**\n"
                    f"Just type your Python code directly into the chat and send it!\n\n"
                    f"🛑 **To Exit:**\n"
                    f"Type `close()` or `exit()` to delete this channel.",
        color=discord.Color.green()
    )
    await term_channel.send(embed=embed)
    await ctx.send(f"✅ Terminal successfully initialized: {term_channel.mention}", ephemeral=True)

@bot.hybrid_command(name="starteventonsunday", aliases=["startevent"], description="Manually starts the 3x XP event (admin).")
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

@bot.hybrid_command(name="setnewschannel", aliases=["snc"], description="Sets the channel for tech news broadcasting (admin).")
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

@bot.hybrid_command(name="setjoinchannel", aliases=["sjc"], description="Sets the channel for welcome banners (admin).")
@commands.has_permissions(administrator=True)
async def setjoinchannel(ctx, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    await config_collection.update_one(
        {"_id": str(ctx.guild.id)}, 
        {"$set": {"join_channel": str(target_channel.id)}}, 
        upsert=True
    )
    await ctx.send(f"✅ Users will now be greeted with visual terminal banners in {target_channel.mention}.")

@bot.hybrid_command(name="messagesendadminpingu", aliases=["setreminder", "sr"], description="Sets the channel for automatic rule reminders (admin).")
@commands.has_permissions(administrator=True)
async def messagesendadminpingu(ctx, channel: discord.TextChannel = None):
    global REMINDER_CHANNEL_ID
    target_channel = channel or ctx.channel
    REMINDER_CHANNEL_ID = target_channel.id
    await ctx.send(f"✅ The automated rules reminder will now be sent to {target_channel.mention}.")

@bot.hybrid_command(name="clear", aliases=["purge", "c"], description="Deletes all messages in this channel with confirmation (mod).")
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

@bot.hybrid_command(name="roles", aliases=["osroles", "distro"], description="Opens the OS/GPU role selection menu (admin).")
@commands.has_permissions(administrator=True)
async def roles(ctx):
    role_embed = discord.Embed(
        title="Choose Your OS & Hardware", 
        description="Select your preferred distributions and graphics drivers from the menus below.\n*(Note: You can select up to 2 OS roles across all menus for Dual-Boot configurations!)*", 
        color=discord.Color.dark_theme()
    )
    await ctx.send(embed=role_embed, view=RolesView())

@bot.hybrid_command(name="sudolock", aliases=["lock"], description="Locks this channel (mod).")
@commands.has_permissions(manage_channels=True)
async def sudolock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(
        title="🔒 Channel Locked",
        description=f"This channel has been locked down by {ctx.author.mention}.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="sudounlock", aliases=["unlock"], description="Unlocks this channel (mod).")
@commands.has_permissions(manage_channels=True)
async def sudounlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    embed = discord.Embed(
        title="🔓 Channel Unlocked",
        description=f"The lockdown has been lifted by {ctx.author.mention}.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="mute", aliases=["m", "timeout"], description="Mutes a user (mod).")
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

@bot.hybrid_command(name="unmute", aliases=["um"], description="Unmutes a user (mod).")
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"✅ Mute lifted for {member.mention}.")
    except Exception as e:
        await ctx.send(f"❌ Failed to unmute user: {e}")

@bot.hybrid_command(name="warning", aliases=["warn"], description="Issues a warning to a user (mod).")
@commands.has_permissions(kick_members=True)
async def warning(ctx, member: discord.Member, *, reason="Manual Warning"):
    await apply_warning(member, reason, ctx.guild)
    await ctx.send(f"✅ Warning applied to {member.mention}.")

@bot.hybrid_command(name="warnings", aliases=["warns", "w"], description="Shows a user's warning history (mod).")
@commands.has_permissions(kick_members=True)
async def warnings(ctx, member: discord.Member):
    if ctx.interaction:
        await ctx.defer()
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

@bot.hybrid_command(name="clearwarnings", aliases=["cw", "clwarns"], description="Clears all warnings for a user (admin).")
@commands.has_permissions(administrator=True)
async def clearwarnings(ctx, member: discord.Member):
    try:
        await warnings_collection.update_one({"_id": member.id}, {"$set": {"count": 0, "history": []}}, upsert=True)
        warning_db[member.id] = 0
        await ctx.send(f"✅ All warnings cleared for {member.mention}.")
    except Exception as e:
        await ctx.send(f"❌ Database error: {e}")

@bot.hybrid_command(name="fixlevels", aliases=["recalclevels", "syncxp"], description="Recalculates everyone's level based on total XP.")
@commands.has_permissions(administrator=True)
async def fixlevels(ctx):
    if ctx.interaction:
        await ctx.defer()
    try:
        all_users = await xp_collection.find({}).to_list(length=None)
    except Exception as e:
        return await ctx.send(f"❌ Database error: {e}")
    changed = 0
    for user_doc in all_users:
        total = user_doc.get("total", 0)
        old_level = user_doc.get("level", 1)
        correct_level = get_level_from_total_xp(total)
        if correct_level != old_level:
            changed += 1
            await xp_collection.update_one({"_id": user_doc["_id"]}, {"$set": {"level": correct_level}})
    embed = discord.Embed(
        title="🔧 Level Recalculation Complete",
        description=f"Scanned `{len(all_users)}` users against the new XP curve.\n`{changed}` user(s) had their level corrected.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="dbstatus", aliases=["dbcheck", "mongostatus"], description="Shows MongoDB connection and collection stats.")
@commands.has_permissions(administrator=True)
async def dbstatus(ctx):
    embed = discord.Embed(title="🗄️ Database Diagnostics", color=discord.Color.blue())
    try:
        await mongo_client.admin.command('ping')
        embed.add_field(name="Connection", value="✅ Reachable", inline=False)
    except Exception as e:
        embed.add_field(name="Connection", value=f"❌ Unreachable: `{e}`", inline=False)
        embed.color = discord.Color.red()
        return await ctx.send(embed=embed)
    try:
        xp_count = await xp_collection.count_documents({})
        warn_count = await warnings_collection.count_documents({})
        config_count = await config_collection.count_documents({})
        embed.add_field(name="users_xp", value=f"`{xp_count}` documents", inline=True)
        embed.add_field(name="user_warnings", value=f"`{warn_count}` documents", inline=True)
        embed.add_field(name="server_config", value=f"`{config_count}` documents", inline=True)
    except Exception as e:
        embed.add_field(name="Collection Error", value=f"`{e}`", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="ban", aliases=["b"], description="Bans a user from the server.")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.name} has been banned. Reason: `{reason}`")

@bot.hybrid_command(name="unban", aliases=["ub"], description="Unbans a user (mod).")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ Ban lifted for user: `{user.name}`.")
    except Exception as e:
        await ctx.send(f"❌ Failed to unban: {e}")

@bot.hybrid_command(name="customize", description="Customize your stats card background image, fonts, and 16M RGB colors.")
async def customize(ctx, background_image: discord.Attachment = None):
    if ctx.interaction:
        await ctx.defer(ephemeral=True)

    if background_image:
        if background_image.content_type in ["image/png", "image/jpeg", "image/webp", "image/jpg"]:
            await customizations_collection.update_one(
                {"_id": ctx.author.id}, 
                {"$set": {"bg_image": background_image.url}}, 
                upsert=True
            )
            msg = "✅ Background image saved to MongoDB! Use the exclusive menu below to adjust fonts and RGB colors."
        else:
            msg = "❌ Invalid file type! Please upload a PNG, JPG, or WEBP."
    else:
        msg = "🎨 Welcome to the Customizer! Select your fonts and colors below.\n*(To set a background image, run this command again and attach an image!)*"

    if ctx.interaction:
        await ctx.interaction.followup.send(msg, view=CustomizeView(), ephemeral=True)
    else:
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(msg, view=CustomizeView(), delete_after=120)

@bot.hybrid_command(name="stats", aliases=["st", "profile", "rank", "lvl"], description="Shows a user's customized level and XP card.")
async def stats(ctx, member: discord.Member = None):
    if ctx.interaction:
        await ctx.defer()
    member = member or ctx.author
    try:
        user_data = await xp_collection.find_one({"_id": member.id})
    except Exception:
        user_data = None
    if not user_data:
        user_data = {"total": 0, "level": 1}
        
    try:
        custom_data = await customizations_collection.find_one({"_id": member.id})
    except Exception:
        custom_data = None
    if not custom_data:
        custom_data = {}
    
    current_xp = user_data.get("total", 0)
    current_level = get_level_from_total_xp(current_xp)
    prev_level_xp = get_xp_requirement(current_level)
    next_level_xp = get_xp_requirement(current_level + 1)
    xp_into_level = current_xp - prev_level_xp
    xp_needed_for_level = next_level_xp - prev_level_xp
    percentage = min(max(xp_into_level / xp_needed_for_level, 0.0), 1.0) if xp_needed_for_level > 0 else 1.0

    bg_url = custom_data.get("bg_image")
    template = custom_data.get("template", "dark")
    font_choice = custom_data.get("font", "arial")

    bg_color = "#1e1e2e"
    text_color = "#ffffff"
    bar_color = "#cba6f7"
    panel_color = "#313244"
    accent_color = "#cba6f7"

    if template == "neon":
        bg_color, text_color, bar_color, panel_color, accent_color = "#000000", "#00ffcc", "#ff00ff", "#111111", "#ff00ff"
    elif template == "retro":
        bg_color, text_color, bar_color, panel_color, accent_color = "#2b213a", "#ffaa00", "#00ffff", "#4a3b5c", "#00ffff"
    elif template == "cyber":
        bg_color, text_color, bar_color, panel_color, accent_color = "#0f0f0f", "#ffff00", "#ff003c", "#222222", "#ff003c"
    elif template == "light":
        bg_color, text_color, bar_color, panel_color, accent_color = "#ffffff", "#000000", "#0055ff", "#eeeeee", "#0055ff"

    if custom_data.get("custom_text_color"):
        text_color = custom_data.get("custom_text_color")
    if custom_data.get("custom_bar_color"):
        bar_color = custom_data.get("custom_bar_color")
    if custom_data.get("custom_accent_color"):
        accent_color = custom_data.get("custom_accent_color")

    try:
        if bg_url:
            bg_img = await load_image_async(bg_url)
            background = Editor(bg_img).resize((900, 300))
        else:
            background = Editor(Canvas((900, 300), color=bg_color))
    except Exception:
        background = Editor(Canvas((900, 300), color=bg_color))

    try:
        main_font = Font(f"fonts/{font_choice}.ttf", size=45)
        sub_font = Font(f"fonts/{font_choice}.ttf", size=30)
        small_font = Font(f"fonts/{font_choice}.ttf", size=22)
    except Exception:
        main_font = Font.poppins(variant="bold", size=45)
        sub_font = Font.poppins(variant="regular", size=30)
        small_font = Font.poppins(variant="light", size=22)

    background.rectangle((20, 20), width=860, height=260, color=panel_color, radius=20, outline=accent_color, stroke_width=3)

    try:
        avatar_image = await load_image_async(str(member.display_avatar.url))
        profile = Editor(avatar_image).resize((200, 200)).circle_image()
        background.paste(profile, (50, 50))
    except Exception:
        pass

    background.text((300, 70), member.name.upper(), font=main_font, color=text_color)
    background.text((300, 140), f"LEVEL {current_level}", font=sub_font, color=bar_color)
    background.text((820, 140), f"{current_xp} / {next_level_xp} XP", font=small_font, color=text_color, align="right")

    background.rectangle((300, 200), width=520, height=35, color="#555555", radius=17)
    fill_width = int(520 * percentage)
    if fill_width > 0:
        background.rectangle((300, 200), width=fill_width, height=35, color=bar_color, radius=17)

    file = discord.File(fp=background.image_bytes, filename="stats.png")
    await ctx.send(file=file)

@bot.hybrid_command(name="leaderstats", aliases=["ls", "lstats", "top", "ldrst", "leaders"], description="Shows the top 15 most active users.")
async def leaderstats(ctx):
    if ctx.interaction:
        await ctx.defer()
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

@bot.hybrid_command(name="randomlinux", aliases=["rl", "linuxtip"], description="Shows a random Linux command and its description.")
async def randomlinux(ctx):
    selected = random.choice(LINUX_COMMANDS)
    embed = discord.Embed(
        title=f"🐧 Linux Command Tip",
        description=f"📁 **Command:** `{selected['cmd']}`\n\n💡 **What it does:** {selected['desc']}",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="whoami", aliases=["wa"], description="Shows your user info in a terminal style.")
async def whoami(ctx):
    roles_list = [r.name for r in ctx.author.roles if r.name != "@everyone"]
    roles_str = ", ".join(roles_list) if roles_list else "No assigned roles."
    embed = discord.Embed(title="💻 Identity Verification: whoami", color=discord.Color.dark_grey())
    embed.add_field(name="User ID", value=f"`{ctx.author.id}`", inline=True)
    embed.add_field(name="Administrator Status", value=f"`{ctx.author.guild_permissions.administrator}`", inline=True)
    embed.add_field(name="Active Roles", value=f"```text\n{roles_str}```", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="weather", aliases=["wx"], description="Shows current weather for a specified city.")
async def weather(ctx, *, city: str = ""):
    if ctx.interaction:
        await ctx.defer()
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

@bot.hybrid_command(name="tankfact", aliases=["tank", "tf"], description="Shows a random tank fact.")
async def tankfact(ctx):
    fact = random.choice(TANK_FACTS)
    embed = discord.Embed(title="🪖 Random Tank Fact", description=fact, color=discord.Color.dark_gray())
    await ctx.send(embed=embed)

@bot.hybrid_command(name="mmafact", aliases=["mma", "mf"], description="Shows a random MMA fact.")
async def mmafact(ctx):
    fact = random.choice(MMA_FACTS)
    embed = discord.Embed(title="🥊 Random MMA Fact", description=fact, color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.hybrid_command(name="pythontip", aliases=["pytip", "ptip"], description="Shows a random Python tip.")
async def pythontip(ctx):
    tip = random.choice(PYTHON_TIPS)
    embed = discord.Embed(title="🐍 Python Tip", description=tip, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.hybrid_command(name="tea", aliases=["brew"], description="Serves a cup of tea.")
async def tea(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"☕ Hey {member.mention}, here is a freshly brewed cup of hot tea for you. Enjoy!")

@bot.hybrid_command(name="ping", aliases=["latency", "pg"], description="Shows bot latency.")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency is `{latency}ms`.")

@bot.hybrid_command(name="serverinfo", aliases=["sinfo", "si"], description="Shows server information.")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"🏰 {guild.name} Server Info", color=discord.Color.blue())
    embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="Total Members", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="Created On", value=f"`{guild.created_at.strftime('%Y-%m-%d')}`", inline=True)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="avatar", aliases=["av", "pfp"], description="Shows a user's avatar.")
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ {member.name}'s Avatar", color=discord.Color.dark_magenta())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="coinflip", aliases=["cf", "flip"], description="Flips a coin.")
async def coinflip(ctx):
    choices = ["Heads", "Tails"]
    await ctx.send(f"🪙 The coin landed on: **{random.choice(choices)}**")

@bot.hybrid_command(name="diceroll", aliases=["dice", "roll"], description="Rolls a dice.")
async def diceroll(ctx, sides: int = 6):
    if sides < 2:
        return await ctx.send("❌ A dice must have at least 2 sides!")
    await ctx.send(f"🎲 You rolled a `{sides}`-sided dice and got: **{random.randint(1, sides)}**")

@bot.hybrid_command(name="8ball", aliases=["eightball", "magicball"], description="Ask the magic 8-ball.")
async def magic_ball(ctx, *, question: str):
    responses = [
        "It is certain.", "Without a doubt.", "Yes, definitely.", 
        "Ask again later.", "Cannot predict right now.", 
        "Don't count on it.", "My sources say no.", "Very doubtful."
    ]
    await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {random.choice(responses)}")

@bot.hybrid_command(name="joke", aliases=["j"], description="Tells a random tech joke.")
async def joke(ctx):
    await ctx.send(f"😂 {random.choice(TECH_JOKES)}")

@bot.hybrid_command(name="gif", aliases=["g"], description="Shows a random Linux gif.")
async def gif(ctx):
    embed = discord.Embed(title="🐧 Random Linux Graphic", color=discord.Color.green())
    embed.set_image(url=random.choice(LINUX_GIFS))
    await ctx.send(embed=embed)

@bot.hybrid_command(name="neofetch", aliases=["nf", "sysinfo"], description="Shows user and OS information in a neofetch style.")
async def neofetch(ctx):
    user_role_ids = [r.id for r in ctx.author.roles]

    TUX_ASCII = [
        r"       .--.           ",
        r"      |o_o |          ",
        r"      |:_/ |          ",
        r"     //   \ \         ",
        r"    (|     | )        ",
        r"   /'\_   _/`\        ",
        r"   \___)=(___/        "
    ]
    ARCH_ASCII = [
        r"          /\          ",
        r"         /  \         ",
        r"        /\   \        ",
        r"       /      \       ",
        r"      /   ,,   \      ",
        r"     /   |  |  -\     ",
        r"    /_-''    ''-_\    "
    ]
    UBUNTU_ASCII = [
        r"         .-.          ",
        r"       .(   ).        ",
        r"      (   .   )       ",
        r"     .-. `-' .-.      ",
        r"    (   )   (   )     ",
        r"     `-'     `-'      ",
        r"                      "
    ]
    DEBIAN_ASCII = [
        r"       _____          ",
        r"      /  __ \         ",
        r"     |  /  | |        ",
        r"     |  \_/  |        ",
        r"      \___.-'         ",
        r"                      ",
        r"                      "
    ]
    FEDORA_ASCII = [
        r"       ______         ",
        r"      / ____/         ",
        r"     / /___           ",
        r"    / ____/           ",
        r"   /_/                ",
        r"                      ",
        r"                      "
    ]
    MINT_ASCII = [
        r"   _____________      ",
        r"  |_  ___  ___  |     ",
        r"    | |  | |  | |     ",
        r"    | |  | |  | |     ",
        r"   _| |__| |__| |     ",
        r"  |_____________|     ",
        r"                      "
    ]
    POP_ASCII = [
        r"    ______            ",
        r"   |  __  |           ",
        r"   | |__) |           ",
        r"   |  ___/            ",
        r"   |_|                ",
        r"                      ",
        r"                      "
    ]
    MANJARO_ASCII = [
        r"   |||||||||| ||||    ",
        r"   |||||||||| ||||    ",
        r"   ||||       ||||    ",
        r"   |||| ||||| ||||    ",
        r"   |||| ||||| ||||    ",
        r"                      ",
        r"                      "
    ]
    ARTIX_ASCII = [
        r"        /\            ",
        r"       /  \           ",
        r"      / /\ \          ",
        r"     / /  \ \         ",
        r"    /_/    \_\        ",
        r"                      ",
        r"                      "
    ]
    WIN11_ASCII = [
        r"  #######   #######   ",
        r"  #######   #######   ",
        r"                      ",
        r"  #######   #######   ",
        r"  #######   #######   ",
        r"                      ",
        r"                      "
    ]
    WIN10_ASCII = [
        r"     ,.=-._____.-=.   ",
        r"    //  ||     ||  \\ ",
        r"   ||   ||     ||   ||",
        r"   ||---|---||        ",
        r"   ||   ||     ||   ||",
        r"    \\  ||     ||  // ",
        r"     `'=-._____.-='   "
    ]
    WINDOWS_ASCII = [
        r"     ,---.---.        ",
        r"    |  1 | 2  |       ",
        r"    |----+----|       ",
        r"    |  3 | 4  |       ",
        r"     `---'---'        ",
        r"                      ",
        r"                      "
    ]
    BSD_ASCII = [
        r"      /\  /\          ",
        r"     (  \/  )         ",
        r"     ( o  o )         ",
        r"      \ == /          ",
        r"       `--'           ",
        r"                      ",
        r"                      "
    ]

    distro_role_mapping = {
        1521868543799328808: ("Arch Linux", ARCH_ASCII),
        1521870392472502344: ("Manjaro", MANJARO_ASCII),
        1521870674669338654: ("EndeavourOS", ARCH_ASCII),
        1521871074994950295: ("Garuda Linux", ARCH_ASCII),
        1521871078308184074: ("Artix Linux", ARTIX_ASCII),
        1522137195102867526: ("Black Arch", ARCH_ASCII),
        1522143963904081920: ("CachyOS", ARCH_ASCII),
        1521870173861056655: ("Debian", DEBIAN_ASCII),
        1521870110552227910: ("Ubuntu", UBUNTU_ASCII),
        1521868791942742026: ("Linux Mint", MINT_ASCII),
        1521871399403393044: ("Kali Linux", DEBIAN_ASCII),
        1521871613958819860: ("Pop!_OS", POP_ASCII),
        1521871816321404969: ("Zorin OS", UBUNTU_ASCII),
        1521870225228955798: ("Gentoo", TUX_ASCII),
        1521872173688422420: ("Nobara", FEDORA_ASCII),
        1521872360393670819: ("Fedora", FEDORA_ASCII)
    }

    win_role_mapping = {
        1521909235594825941: ("Windows 11", WIN11_ASCII),
        1521909403496742973: ("Windows 10", WIN10_ASCII),
        1521909451739893982: ("Windows 8", WINDOWS_ASCII),
        1521909341802725427: ("Windows 7", WINDOWS_ASCII)
    }

    bsd_role_mapping = {
        1521909235594825999: ("FreeBSD", BSD_ASCII),
        1522211951709519872: ("GhostBSD", BSD_ASCII)
    }

    selected_linux = None
    selected_win = None
    selected_bsd = None

    for r_id in user_role_ids:
        if r_id in distro_role_mapping and not selected_linux:
            selected_linux = distro_role_mapping[r_id]
        if r_id in win_role_mapping and not selected_win:
            selected_win = win_role_mapping[r_id]
        if r_id in bsd_role_mapping and not selected_bsd:
            selected_bsd = bsd_role_mapping[r_id]

    final_os = "Linux (Tux)"
    final_ascii = TUX_ASCII

    if selected_linux:
        final_os = selected_linux[0]
        final_ascii = selected_linux[1]
    elif selected_win:
        final_os = selected_win[0]
        final_ascii = selected_win[1]
    elif selected_bsd:
        final_os = selected_bsd[0]
        final_ascii = selected_bsd[1]

    is_mod = ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator
    auth_level = "/Root" if is_mod else "/User"

    join_time = ctx.author.joined_at
    if join_time:
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = now - join_time
        d = diff.days
        h, rem = divmod(diff.seconds, 3600)
        m, _ = divmod(rem, 60)
        uptime_str = f"{d}d {h}h {m}m"
    else:
        uptime_str = "Unknown"

    role_count = len(ctx.author.roles) - 1

    top_line = f"{ctx.author.name}@Linux & Beyond"
    separator = "-" * len(top_line)

    stats_lines = [
        top_line,
        separator,
        f"OS: {final_os}",
        f"Host: Linux & Beyond",
        f"Authority: {auth_level}",
        f"Uptime: {uptime_str}",
        f"Roles: {role_count}",
        f"Shell: adminpingu-bot ?/slash",
        f"Prefix: ? (or use / anywhere)"
    ]

    neofetch_output = "```ansi\n"
    max_lines = max(len(final_ascii), len(stats_lines))
    for i in range(max_lines):
        left = final_ascii[i].ljust(22) if i < len(final_ascii) else " " * 22
        right = stats_lines[i] if i < len(stats_lines) else ""
        neofetch_output += f"{left}  {right}\n"
    neofetch_output += "```"

    await ctx.send(neofetch_output)

@bot.hybrid_command(name="cowsay", aliases=["cow"], description="Simulates the classic Linux cowsay command.")
async def cowsay(ctx, *, text: str = "Moo! AdminPingu is watching."):
    clean_text = text[:100]
    line_len = len(clean_text)
    top = " " + "_" * (line_len + 2)
    bottom = " " + "-" * (line_len + 2)
    speech = f"< {clean_text} >"
    cow = (
        "```\n"
        f"{top}\n"
        f"{speech}\n"
        f"{bottom}\n"
        "        \\   ^__^\n"
        "         \\  (oo)\\_______\n"
        "            (__)\\       )\\/\\\n"
        "                ||----w |\n"
        "                ||     ||\n"
        "```"
    )
    await ctx.send(cow)

@bot.hybrid_command(name="fortune", aliases=["ft"], description="Simulates the classic fortune command.")
async def fortune(ctx):
    fortunes = [
        "A computer program does what you tell it to do, not what you want it to do.",
        "There are only two hard things in Computer Science: cache invalidation and naming things.",
        "The best way to predict the future is to implement it.",
        "In Linux, everything is a file — including your patience by 3 AM.",
        "Real programmers count from 0.",
        "sudo make me a sandwich.",
        "It's not a bug, it's an undocumented feature.",
        "Talk is cheap. Show me the code. — Linus Torvalds",
        "Given enough eyeballs, all bugs are shallow.",
        "The Linux philosophy: 'Laugh in the face of danger.' Then hide until it goes away.",
        "One does not simply compile the kernel without coffee.",
        "rm -rf is a lifestyle choice, not a command."
    ]
    await ctx.send(f"🥠 `{random.choice(fortunes)}`")

@bot.hybrid_command(name="packagemap", aliases=["pkg", "pkgcheat"], description="Compares package manager commands.")
async def packagemap(ctx, action: str = "install"):
    action = action.lower().strip()
    cheatsheet = {
        "install": {
            "Debian/Ubuntu (apt)": "sudo apt install <package>",
            "Fedora/RHEL (dnf)": "sudo dnf install <package>",
            "Arch (pacman)": "sudo pacman -S <package>",
            "openSUSE (zypper)": "sudo zypper install <package>",
            "Alpine (apk)": "sudo apk add <package>"
        },
        "remove": {
            "Debian/Ubuntu (apt)": "sudo apt remove <package>",
            "Fedora/RHEL (dnf)": "sudo dnf remove <package>",
            "Arch (pacman)": "sudo pacman -R <package>",
            "openSUSE (zypper)": "sudo zypper remove <package>",
            "Alpine (apk)": "sudo apk del <package>"
        },
        "update": {
            "Debian/Ubuntu (apt)": "sudo apt update && sudo apt upgrade",
            "Fedora/RHEL (dnf)": "sudo dnf upgrade --refresh",
            "Arch (pacman)": "sudo pacman -Syu",
            "openSUSE (zypper)": "sudo zypper update",
            "Alpine (apk)": "sudo apk upgrade"
        }
    }
    
    if action not in cheatsheet:
        return await ctx.send("❌ Valid actions: `install`, `remove`, `update`.")
        
    embed = discord.Embed(title=f"📦 Package Map: '{action}'", color=discord.Color.gold())
    for os_name, cmd in cheatsheet[action].items():
        embed.add_field(name=os_name, value=f"`{cmd}`", inline=False)
        
    await ctx.send(embed=embed)

keep_alive()
try:
    bot.run(os.environ.get("TOKEN"))
except Exception as e:
    print(f"CRITICAL ERROR: Failed to launch the Discord bot. Details: {e}")
