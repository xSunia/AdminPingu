#This bot is not fucking ai coded i builded the project myself i used ai for some suggestions and the  long strings
# cause i dont know how to make good looking texts i hope you understond me 👍
import discord
from discord.ext import commands, tasks
from discord.ui import Select, View, Modal, TextInput
from flask import Flask
from threading import Thread
import threading
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
import base64
import sys
import ctypes
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from unidecode import unidecode
from easy_pil import Editor, Canvas, Font, load_image_async
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from google import genai
from google.genai import types

# =====================================================================
# Logging / Reliability fix cuz the bot kept straight-up dying 
# =====================================================================
# WHY THIS IS HERE:
# Bot used to ghost us w zero trace in logs. classic skill issue caused 
# by these 4 things, all patched below:
#
#   1) stdout was block-buffered. when the proc gets OOM-killed or crashes, 
#      anything chillin in the buffer is gone forever. RIP final logs.
#   2) logging.basicConfig() was missing. discord.py's internal logs 
#      (rate limits, gateway drops, etc.) had nowhere to go, total void.
#   3) background @tasks.loop jobs had no .error() handlers. one tiny exception 
#      and the loop dead-ass dies forever w/ just a stderr traceback.
#   4) no top-level try/except around bot.run(), no loop exception hook, 
#      no thread hook. bad tokens or flask thread crashes just killed 
#      the whole app silently.
#
# none of this changes bot logic/features — just makes sure that when 
# shit breaks, we actually know why instead of guessing.

# Force unbuffered stdout/stderr so print()/logs get flushed instantly 
# instead of getting vaporized if the process crashes unexpectedly fr.
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    # reconfigure() needs Python 3.7+; if unavailable, keep defaults.
    pass

# Where the persistent log file lives. This acts as a safety net that
# survives even if the hosting platform's own log viewer drops, trims,
# or fails to capture console output for any reason.
LOG_FILE_PATH = os.environ.get("ADMINPINGU_LOG_FILE", "adminpingu.log")

LOG_FORMAT = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("AdminPingu")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(LOG_FORMAT)
logger.addHandler(console_handler)

file_handler = None
try:
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(file_handler)
except Exception as log_setup_error:
   # if log file cant even be created (like read-only fs n shit), 
   #dont crash and burn on startup, just fallback to console logging bruh
    print(f"Could not create log file handler: {log_setup_error}", flush=True)

# Make discord.py's own internal logger ("discord", "discord.gateway",
# "discord.ext.tasks", ...) share our handlers, so gateway disconnects,
# reconnect attempts, and rate-limit warnings are no longer swallowed
# silently — they'll show up in both the console and adminpingu.log.
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.INFO)
discord_logger.addHandler(console_handler)
if file_handler:
    discord_logger.addHandler(file_handler)


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """
    Global safety net for the MAIN thread. Without this, an exception
    that escapes all the way to the top of the program just prints a
    traceback and exits — and depending on buffering, that traceback
    can be the exact thing that gets lost. Routing it through our
    logger guarantees it is flushed to both the console and the log
    file before the process actually dies.
    """
    if issubclass(exc_type, KeyboardInterrupt):
    
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical(
        "Uncaught exception crashed the main thread — this is almost "
        "certainly why the bot went offline:",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


sys.excepthook = handle_uncaught_exception


def handle_thread_exception(args):
    """
    Same safety net as above, but for background threads (namely the
    Flask keep-alive thread). By default, an exception inside a thread
    is printed once to stderr and then the thread just quietly dies —
    this makes sure it's logged clearly instead.
    """
    logger.critical(
        f"Uncaught exception in thread '{args.thread.name}': "
        f"{args.exc_type.__name__}: {args.exc_value}",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


threading.excepthook = handle_thread_exception


app = Flask('')

@app.route('/')
def home():
    return "AdminPingu is currently online and fully operational."

def run():
    # Runs inside its own background thread. Any exception raised here
    # is now caught by threading.excepthook (set up above) instead of
    # silently killing the thread with no explanation.
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run, name="FlaskKeepAliveThread", daemon=True)
    t.start()
    logger.info("Flask keep-alive server started on port 8080.")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

BOT_START_TIME = time.time()

# ==========================================
# Channel & role IDs
# ==========================================
LOG_CHANNEL_ID = 123456789012345678
WARNINGS_CHANNEL_ID = 1521880436270301354
LEVEL_LOG_CHANNEL_ID = 1521880096854769785
REMINDER_CHANNEL_ID = 123456789012345678
EPIC_LEVEL_100_CHANNEL = 1510339895032418508

ROLES_CHANNEL_ID = 1521868274240065597

USER_ROLE_ID = 1510547520273649704
MEDIA_ROLE_ID = 1521875919864856714

ACTIVE_EVENT_CHANNEL_ID = None

# Channels where users are free to post media/GIF links with no restrictions
# exempt from the identical-message spam filter below.
UNRESTRICTED_MEDIA_CHANNEL_IDS = [
    1510347156358168697,
    1521943152490189012,
]

# Channels where EVERYONE may post media not just Level 10+ / media role

MEDIA_CHANNEL_IDS = [
    1510346595298709646,
    1528490372240510996,
    1534663553334902955,
    1510347496139002078,
    1510350382147174532,
    1510347716037967962,
    1510347277938589749,
    1534664073592049874,
    1534664109419659314,
]

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

# ==========================================
# Static content used by fun/utility commands
# ==========================================
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
    1534520300807520379, 1521872759691542588, 1521873026776301608, 1521873129868365964,
    1521909235594825941, 1521909235594825999,
    1522137195102867526, 1522137253856415784, 1522143963904081920,
    1521909451739893982, 1521909341802725427, 1522212167393214514, 1522212092663300248,
    1522211951709519872, 1522211033073324234, 1522211796532854826, 1522211599744499834,
    1521909403496742973, 1534519999681658941
]
ALL_GPU_ROLES = [1521879270530486414, 1521879224951246928, 1521879315648614410]

# ==========================================
# Chat filter setup
# ==========================================
STRICT_BANNED_WORDS = {
    "nigger", "nigga", "porn", "porno", "sex", "pussy", "fuck",
    "bitch", "cunt", "dick", "asshole", "slut", "whore",
    "faggot", "childporn", "rape", "pusy", "fck", "btch"
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

# ==========================================
# Database setup
# ==========================================
MONGO_URI = os.environ.get("MONGO_URI")

try:
    mongo_client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = mongo_client["AdminPinguDB"]
    xp_collection = db["users_xp"]
    config_collection = db["server_config"]
    warnings_collection = db["user_warnings"]
    customization_collection = db["user_customization"]
except Exception as e:
    print(f"MongoDB Initialization Error: {e}")

warning_db = {}
user_message_cache = {}
xp_message_counter = {}
last_user_message_time = {}  # user_id -> last message timestamp (drives cache TTL cleanup)
LAST_NEWS_URL = ""
last_activity_time = time.time()

# ==========================================
# Leveling math 
# ==========================================
# xp curve got reworked cuz peopol started crying it was too hard:
#   - lvl 1-10: brain-dead linear curve each lvl costs L*100 xp 
#     (100, 200, 300 ... 1000). takes like 30 mins of brainrot chatting.
#   - lvl 10-20: light-medium, first baby step up.
#   - lvl 20-30: medium difficulty.
#   - lvl 30-50: still medium, just a painfully long stretch of it.
#   - lvl 50-75: kinda hard, time to actually touch some grass and grind.
#   - lvl 75-90: a bit more cooked than the 50-75 band.
#   - lvl 90-100: genuinely down-bad hard, final boss stretch.
#   - lvl 100+: keeps scaling like the 90-100 mental asylum tier just in case 
#     some no-lifers actually raise the level cap later.
def _geometric_interp(level, low_level, low_value, high_level, high_value):
    """Smoothly grows from low_value to high_value as level goes low_level -> high_level."""
    t = (level - low_level) / (high_level - low_level)
    return low_value * ((high_value / low_value) ** t)

def _xp_delta_for_level(level):
    """Returns how much XP is needed to go from (level) to (level + 1)."""
    if level <= 10:
        # Levels 1-10: exactly level * 100 1->2 is 100  2->3 is 200 ... 10->11 is 1000
        value = level * 100
    elif level <= 20:
        # Light-medium: 10 -> 20.
        value = _geometric_interp(level, 10, 1000, 20, 2000)
    elif level <= 30:
        # Medium: 20 -> 30.
        value = _geometric_interp(level, 20, 2000, 30, 3500)
    elif level <= 50:
        # Medium (longer stretch): 30 -> 50.
        value = _geometric_interp(level, 30, 3500, 50, 8000)
    elif level <= 75:
        # Somewhat hard: 50 -> 75.
        value = _geometric_interp(level, 50, 8000, 75, 20000)
    elif level <= 90:
        # A bit harder: 75 -> 90.
        value = _geometric_interp(level, 75, 20000, 90, 45000)
    elif level <= 100:
        # Genuinely hard, steepest final stretch: 90 -> 100.
        value = _geometric_interp(level, 90, 45000, 100, 150000)
    else:
        # Beyond level 100 (future-proofing): keep compounding at the same
        # rate as the final band so the curve never breaks or plateaus.
        value = 150000 * (1.35 ** (level - 100))
    return max(50, round(value))

# Every 3 messages a user gets awarded XP in the 5-30 range, weighted around
# 15. Values of 10 or below and 25 or above are rarer than the mid band.
def get_weighted_xp_gain():
    """Returns a weighted random XP amount between 5 and 30, centered on 15."""
    tier = random.choices(
        population=["low", "mid", "high"],
        weights=[20, 60, 20],  # low: 5-10, mid: 11-24 (favored), high: 25-30
        k=1
    )[0]
    if tier == "low":
        return random.randint(5, 10)
    elif tier == "mid":
        return random.randint(11, 24)
    return random.randint(25, 30)

_MAX_PRECOMPUTED_LEVEL = 200
_XP_REQUIREMENT_TABLE = [0, 0]
for _lvl in range(1, _MAX_PRECOMPUTED_LEVEL + 1):
    _XP_REQUIREMENT_TABLE.append(_XP_REQUIREMENT_TABLE[-1] + _xp_delta_for_level(_lvl))

def get_xp_requirement(level):
    """Total XP needed to REACH `level` (level 1 starts at 0 XP)."""
    if level <= 1:
        return 0
    if level < len(_XP_REQUIREMENT_TABLE):
        return _XP_REQUIREMENT_TABLE[level]
    total = _XP_REQUIREMENT_TABLE[-1]
    for lvl in range(len(_XP_REQUIREMENT_TABLE) - 1, level):
        total += _xp_delta_for_level(lvl)
    return total

def get_level_from_total_xp(total_xp):
    level = 1
    while total_xp >= get_xp_requirement(level + 1):
        level += 1
    return level

# ==========================================
# Sunday event persistence helpers
# ==========================================
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

# ==========================================
# Tech news persistence helpers
# ==========================================
# FIX: LAST_NEWS_URL used to be an in-memory-only variable, which reset to ""
# every time the bot restarted (e.g. on every Render deploy). That meant the
# task would think the current top RSS entry was "new" again right after every
# restart, and repost the same article. Now the last posted URL is persisted
# to MongoDB and restored on startup, so a restart never causes a duplicate post.
async def save_news_state(last_url):
    try:
        await config_collection.update_one(
            {"_id": "news_state"},
            {"$set": {"last_url": last_url}},
            upsert=True
        )
    except Exception as e:
        print(f"News state save error: {e}")

async def load_news_state():
    try:
        return await config_collection.find_one({"_id": "news_state"})
    except Exception as e:
        print(f"News state load error: {e}")
        return None

# ==========================================
# Kernel release system
# ==========================================
# Every time a new AdminPingu build is shipped, the bot bumps its kernel
# version (starting at 1.0, +0.1 per release) and posts a release
# announcement to the kernel channel: the lainn.gif boot screen with
# "Kernel Compiling..." (Terminus, gray) and "Kernel Version: x.y <codename>"
# (Terminus, turquoise) baked into the animation, followed by the release
# title and the changelog. State lives in MongoDB so it survives Render's
# ephemeral filesystem between deploys.

KERNEL_CHANNEL_ID = 1534868928910852097
KERNEL_STATE_ID = "kernel_release_state"
KERNEL_CHANGELOG_ID = "kernel_changelog"
KERNEL_GIF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lainn.gif")
KERNEL_TERMINUS_FONT = "TerminusTTF-4.49.3.ttf"
KERNEL_TURQUOISE = (64, 224, 208)
KERNEL_GRAY = (169, 169, 169)

# 100 dessert codenames, one per release.
KERNEL_CODENAMES = [
    "Oreo", "Caramella", "Latte", "Cheesecake", "Tiramisu", "Macaron",
    "Praline", "Brownie", "Eclair", "Fudge", "Marzipan", "Biscotti",
    "Cupcake", "Mochi", "Cannoli", "Panna Cotta", "Baklava", "Churro",
    "Gelato", "Sorbet", "Truffle", "Muffin", "Doughnut", "Cronut",
    "Strudel", "Danish", "Cookie", "Pancake", "Waffle", "Crepe",
    "Pudding", "Crumble", "Tart", "Scone", "Meringue", "Profiterole",
    "Nougat", "Halva", "Toffee", "Cinnamon Roll", "Bomboloni", "Beignet",
    "Zeppole", "Panettone", "Yule Log", "Shortbread", "Gingersnap",
    "Snickerdoodle", "Ravani", "Kulfi", "Gulab Jamun", "Jalebi",
    "Lamington", "Pavlova", "Anzac Biscuit", "Tim Tam", "Hokey Pokey",
    "Banoffee", "Custard Tart", "Rice Pudding", "Flan", "Tres Leches",
    "Alfajor", "Dulce de Leche", "Brigadeiro", "Quindim", "Beijinho",
    "Oblea", "Mango Sticky Rice", "Dragon Beard", "Sweet Rice Ball",
    "Tangyuan", "Shaved Ice", "Snow Skin Mooncake", "Egg Tart",
    "Butter Mochi", "Haupia", "Malasada", "Dole Whip", "Choc Chip",
    "Rock Road", "Battenberg", "Eccles Cake", "Bakewell", "Saffron Cake",
    "Parkin", "Roly Poly", "Eton Mess", "Treacle Tart", "Victoria Sponge",
    "Madeleine", "Financier", "Dacquoise", "Sable", "Pain d'Epices",
    "Kadaif", "Lokum", "Kunefe", "Babka", "Rugelach",
]

async def _kernel_get_state():
    try:
        return await config_collection.find_one({"_id": KERNEL_STATE_ID}) or {}
    except Exception as e:
        print(f"Kernel state load error: {e}")
        return {}

async def _kernel_bump_state(state):
    if not state.get("version"):
        version = "1.0"
        codename_index = 1
    else:
        major, _, minor = str(state["version"]).partition(".")
        try:
            minor_num = int(minor) if minor else 0
        except ValueError:
            minor_num = 0
        version = f"{major}.{minor_num + 1}"
        codename_index = int(state.get("codename_index", 0) or 0) + 1
    codename = KERNEL_CODENAMES[(codename_index - 1) % len(KERNEL_CODENAMES)]
    try:
        await config_collection.update_one(
            {"_id": KERNEL_STATE_ID},
            {"$set": {"version": version, "codename_index": codename_index}},
            upsert=True
        )
    except Exception as e:
        print(f"Kernel state save error: {e}")
    return version, codename

async def _kernel_get_pending_changelog():
    try:
        return await config_collection.find_one({"_id": KERNEL_CHANGELOG_ID})
    except Exception as e:
        print(f"Kernel changelog load error: {e}")
        return None

async def _kernel_set_changelog(added, fixed, removed):
    try:
        await config_collection.update_one(
            {"_id": KERNEL_CHANGELOG_ID},
            {"$set": {"added": added, "fixed": fixed, "removed": removed}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Kernel changelog save error: {e}")
        return False

async def _kernel_clear_changelog():
    try:
        await config_collection.delete_one({"_id": KERNEL_CHANGELOG_ID})
    except Exception:
        pass

def _render_kernel_gif(version, codename):
    """Bakes 'Kernel Compiling...' (gray) + 'Kernel Version: x.y <codename>'
    (turquoise) into every frame of lainn.gif. Returns GIF bytes (or None)."""
    if not os.path.exists(KERNEL_GIF_PATH):
        print(f"⚠️ Kernel GIF not found: {KERNEL_GIF_PATH}")
        return None
    font_path = get_font_path(KERNEL_TERMINUS_FONT)
    line1 = "Kernel Compiling..."
    line2 = f'Kernel Version: {version} "{codename}"'
    try:
        font1 = ImageFont.truetype(font_path, 34) if font_path else ImageFont.load_default()
        font2 = ImageFont.truetype(font_path, 30) if font_path else ImageFont.load_default()
    except Exception:
        font1 = font2 = ImageFont.load_default()

    src = Image.open(KERNEL_GIF_PATH)
    frames, durations = [], []
    for frame in ImageSequence.Iterator(src):
        f = frame.convert("RGBA")
        W, H = f.size
        draw = ImageDraw.Draw(f)
        b1 = draw.textbbox((0, 0), line1, font=font1)
        b2 = draw.textbbox((0, 0), line2, font=font2)
        h1, h2 = b1[3] - b1[1], b2[3] - b2[1]
        w1, w2 = b1[2] - b1[0], b2[2] - b2[0]
        block_w = max(w1, w2)
        block_h = h1 + h2 + 14
        block_x = (W - block_w) // 2 - 40
        block_y = (H - block_h) // 2 - 20
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(band)
        bd.rounded_rectangle(
            [block_x - 10, block_y - 8, block_x + block_w + 90, block_y + block_h + 8],
            radius=14, fill=(10, 10, 14, 170)
        )
        f = Image.alpha_composite(f, band)
        draw = ImageDraw.Draw(f)
        cx = W // 2
        draw.text((cx, block_y + h1 // 2), line1, font=font1, fill=KERNEL_GRAY, anchor="mm")
        draw.text((cx, block_y + h1 + 7 + h2 // 2), line2, font=font2, fill=KERNEL_TURQUOISE, anchor="mm")
        frames.append(f)
        durations.append(frame.info.get("duration", 130))

    buf = io.BytesIO()
    frames[0].save(buf, save_all=True, append_images=frames[1:], format="GIF",
                   duration=durations, loop=0)
    buf.seek(0)
    return buf

async def _kernel_announce(pending):
    channel = bot.get_channel(KERNEL_CHANNEL_ID)
    if channel is None:
        print(f"⚠️ Kernel channel not found: {KERNEL_CHANNEL_ID}")
        return False
    state = await _kernel_get_state()
    version, codename = await _kernel_bump_state(state)
    try:
        gif_bytes = await asyncio.to_thread(_render_kernel_gif, version, codename)
    except Exception as e:
        print(f"Kernel GIF render error: {e}")
        gif_bytes = None
    added = (pending or {}).get("added") or []
    fixed = (pending or {}).get("fixed") or []
    removed = (pending or {}).get("removed") or []

    embed = discord.Embed(
        title="🐧 New AdminPingu Kernel Has Released!",
        description=f"**Kernel `{version}` — codename \"{codename}\"** is now live.",
        color=discord.Color.from_rgb(*KERNEL_TURQUOISE)
    )
    if added:
        embed.add_field(name="➕ Added", value="\n".join(f"• {a}" for a in added), inline=False)
    if fixed:
        embed.add_field(name="🔧 Fixed", value="\n".join(f"• {f}" for f in fixed), inline=False)
    if removed:
        embed.add_field(name="🗑️ Removed", value="\n".join(f"• {r}" for r in removed), inline=False)
    if not (added or fixed or removed):
        embed.add_field(name="⚙️ Maintenance", value="Stability improvements and housekeeping.", inline=False)
    embed.set_footer(text=f"AdminPingu Linux — Kernel {version} ({codename})")

    try:
        files = [discord.File(gif_bytes, filename="kernel_compiling.gif")] if gif_bytes else []
        await channel.send(embed=embed, files=files)
    except Exception as e:
        print(f"Kernel release send error: {e}")
        return False
    await _kernel_clear_changelog()
    print(f"🐧 Kernel {version} ({codename}) release announced in #{channel.name}.")
    return True

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
        new_total = user_data["total"] + amount
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

# ==========================================
# OS / GPU role picker menus
# ==========================================
class DistroSelect(Select):
    def __init__(self, placeholder, options, custom_id, max_values=None):
        # max_values=None -> allow picking any number (OS menus).
        # max_values=1    -> single, mutually-exclusive pick (DE/WM menu).
        max_v = max_values if max_values is not None else len(options)
        super().__init__(placeholder=placeholder, min_values=0, max_values=max_v, options=options, custom_id=custom_id)
        self.menu_role_ids = [int(opt.value) for opt in options]

    async def callback(self, interaction: discord.Interaction):
        selected_role_ids = [int(v) for v in self.values]
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
            discord.SelectOption(label="NVIDIA Graphics", value="1521879270530486414", emoji="<:nvidia:1521978895950418070>"),
            discord.SelectOption(label="AMD Graphics", value="1521879224951246928", emoji="<:amd:1521978857278800036>"),
            discord.SelectOption(label="Intel Graphics", value="1521879315648614410", emoji="<:intel:1521978932524613745>")
        ]
        super().__init__(placeholder="🖥️ Select Your Graphics Driver", min_values=0, max_values=1, options=options, custom_id="gpu_select")

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
    """Server role picker, one menu per category (FIRST message).

    Discord lets us stack up to 5 select menus on a single message, so the
    first roles message hosts five categories side by side: Arch Based,
    Debian & Ubuntu Based, Fedora & Independent, FreeBSD & Windows Family and
    Graphics. The DE & WM menu doesn't fit on the first message anymore, so it
    is posted as a separate second message (see DewmView below).
    """

    def __init__(self):
        super().__init__(timeout=None)
        arch_opts = [
            discord.SelectOption(label="Arch Linux", value="1521868543799328808", emoji="<:arch:1536476838942216263>"),
            discord.SelectOption(label="Manjaro", value="1521870392472502344", emoji="<:manjaro:1521985873313271960>"),
            discord.SelectOption(label="EndeavourOS", value="1521870674669338654", emoji="<:endeavouros:1521986003479298219>"),
            discord.SelectOption(label="Garuda Linux", value="1521871074994950295", emoji="<:garuda:1536476906784956436>"),
            discord.SelectOption(label="Artix Linux", value="1521871078308184074", emoji="<:artix:1521985617074851860>"),
            discord.SelectOption(label="Black Arch", value="1522137195102867526", emoji="<:blackarch:1536477527722434653>"),
            discord.SelectOption(label="CachyOS", value="1522143963904081920", emoji="<:cachy:1536476853789925416>"),
        ]
        deb_opts = [
            discord.SelectOption(label="Debian", value="1521870173861056655", emoji="<:debian:1536476872114831370>"),
            discord.SelectOption(label="Ubuntu", value="1521870110552227910", emoji="<:ubuntu:1521985775170752642>"),
            discord.SelectOption(label="Linux Mint", value="1521868791942742026", emoji="<:linuxmint:1521986158656094309>"),
            discord.SelectOption(label="Kali Linux", value="1521871399403393044", emoji="<:kali:1536476996731805726>"),
            discord.SelectOption(label="Pop!_OS", value="1521871613958819860", emoji="<:pop_os:1521985910076604536>"),
            discord.SelectOption(label="Zorin OS", value="1521871816321404969", emoji="<:zorin:1536487843034308640>"),
            discord.SelectOption(label="MX Linux", value="1521871679368986655", emoji="<:mxlinux:1521985961364295801>"),
            discord.SelectOption(label="Deepin", value="1521871896117776468", emoji="<:deepin:1521985680484601897>"),
            discord.SelectOption(label="Elementary OS", value="1521872016901406720", emoji="<:elementary:1521985644174250124>"),
            discord.SelectOption(label="Parrot OS", value="1522137253856415784", emoji="<:parrot:1536476967493173481>"),
        ]
        fedora_indep_opts = [
            discord.SelectOption(label="Fedora", value="1521872360393670819", emoji="<:fedora:1536477069251448912>"),
            discord.SelectOption(label="Nobara", value="1521872173688422420", emoji="<:nobara:1536477048086986773>"),
            discord.SelectOption(label="Gentoo", value="1521870225228955798", emoji="<:gentoo:1536476893300138135>"),
            discord.SelectOption(label="Red Star OS", value="1521872534117679206", emoji="<:redstaros:1536477117741662329>"),
            discord.SelectOption(label="Void Linux", value="1521872635968098344", emoji="<:void:1536477143977037956>"),
            discord.SelectOption(label="NixOS", value="1534520300807520379", emoji="<:nixos:1536477164227010600>"),
            discord.SelectOption(label="Alpine Linux", value="1521872759691542588", emoji="<:alpine:1536477555274547271>"),
            discord.SelectOption(label="openSUSE", value="1521873026776301608", emoji="<:opensuse:1536477479425024070>"),
            discord.SelectOption(label="Slackware", value="1521873129868365964", emoji="<:slcakware:1536477186851344544>"),
            discord.SelectOption(label="Chimera Linux", value="1534519999681658941", emoji="<:chimera:1536484553592541225>"),
            discord.SelectOption(label="Linux From Scratch", value="1538268578497962065", emoji="<:linuxfromscratch:1538279252749717586>"),
        ]
        bsd_win_opts = [
            discord.SelectOption(label="FreeBSD", value="1521909235594825999", emoji="<:freesbd:1536477374378410064>"),
            discord.SelectOption(label="GhostBSD", value="1522211951709519872", emoji="<:ghostbsd:1536477283626389555>"),
            discord.SelectOption(label="OpenBSD", value="1522211033073324234", emoji="<:openbsd:1536477302496694282>"),
            discord.SelectOption(label="DragonFly BSD", value="1522211796532854826", emoji="<:dragonfltbsd:1536477329172205758>"),
            discord.SelectOption(label="NetBSD", value="1522211599744499834", emoji="<:netbsd:1536477353687912511>"),
            discord.SelectOption(label="Windows 11", value="1521909235594825941", emoji="<:win11:1536477207247978638>"),
            discord.SelectOption(label="Windows 10", value="1521909403496742973", emoji="<:win10:1536477231507972106>"),
            discord.SelectOption(label="Windows 8", value="1521909451739893982", emoji="<:win7:1536477261228671067>"),
            discord.SelectOption(label="Windows 7", value="1521909341802725427", emoji="<:win7:1536477261228671067>"),
            discord.SelectOption(label="Windows Vista", value="1522212167393214514", emoji="<:win7:1536477261228671067>"),
            discord.SelectOption(label="Windows XP", value="1522212092663300248", emoji="<:win7:1536477261228671067>"),
        ]
        self.embed = discord.Embed(
            title="Choose Your OS, Hardware & Desktop",
            description=(
                "Pick any OS role from the dropdowns below — no dual-boot limit! "
                "For **Graphics**, only one selection is kept at a time.\n\n"
                "**🐧 Arch Based** — Arch & Arch-based distros\n"
                "**🐧 Debian & Ubuntu Based** — Debian-family distros\n"
                "**🐧 Fedora & Independent** — Fedora/RHEL-based + independent distros\n"
                "**🧬 FreeBSD & Windows Family** — BSD systems + Windows\n"
                "**🖥️ Graphics** — GPU driver roles\n"
                "**🖼️ DE / WM** — desktops & window managers in the next message\n"
                "**🍎 Apple & Android** — Apple & Android roles in the next message\n"
                "**🖥️ Other Operating Systems** — other OS roles in the next message"
            ),
            color=discord.Color.dark_theme(),
        )
        self.add_item(DistroSelect(
            placeholder="🐧 1. Select Arch / Arch-based roles",
            options=arch_opts,
            custom_id="roles_arch",
        ))
        self.add_item(DistroSelect(
            placeholder="🐧 2. Select Debian & Ubuntu-based roles",
            options=deb_opts,
            custom_id="roles_deb",
        ))
        self.add_item(DistroSelect(
            placeholder="🐧 3. Select Fedora & Independent roles",
            options=fedora_indep_opts,
            custom_id="roles_fedora_indep",
        ))
        self.add_item(DistroSelect(
            placeholder="🧬 4. Select FreeBSD & Windows roles",
            options=bsd_win_opts,
            custom_id="roles_bsd_win",
        ))
        self.add_item(GPUSelect())


class DewmView(View):
    """Second roles message: DE / WM menu (single pick)."""

    def __init__(self):
        super().__init__(timeout=None)
        dewm_opts = [
            discord.SelectOption(label="KDE Plasma", value="1535969909954183239", emoji="<:kde:1536489019813265428>"),
            discord.SelectOption(label="GNOME", value="1535970090724495470", emoji="<:gnome:1536477450308034732>"),
            discord.SelectOption(label="XFCE", value="1535970501740990494", emoji="<:xfce:1536477584358121472>"),
            discord.SelectOption(label="Cinnamon", value="1535970676337418240", emoji="<:cinnamon:1536477619174768762>"),
            discord.SelectOption(label="MATE", value="1535970708046356552", emoji="<:mate:1536489133373915187>"),
            discord.SelectOption(label="Niri", value="1535970826686431314", emoji="<:niri:1536477429118271618>"),
            discord.SelectOption(label="Hyprland", value="1535971021008543744", emoji="<:hyperland:1536477403118051368>"),
            discord.SelectOption(label="i3", value="1535971133260701716", emoji="<:i3:1536489182069784586>"),
            discord.SelectOption(label="Sway", value="1535971171260964944", emoji="<:sway:1536489216140247082>"),
            discord.SelectOption(label="Mango WM", value="1535971353801396275", emoji="<:mangowm:1536489244011270184>"),
        ]
        apple_android_opts = [
            discord.SelectOption(label="Android", value="1538125479222181888", emoji="<:android:1538125170835718174>"),
            discord.SelectOption(label="MacOS", value="1538125249315479593", emoji="<:mac:1538125227794370590>"),
            discord.SelectOption(label="iOS", value="1538125362452496425", emoji="<:ios:1538125201236295754>"),
        ]
        otheros_opts = [
            discord.SelectOption(label="Temple OS", value="1538277203564044348", emoji="<:templeos:1538279317971402854>"),
            discord.SelectOption(label="Haiku", value="1538277859263520949", emoji="<:haiku:1538279349453594624>"),
            discord.SelectOption(label="IllumOS", value="1538277539640905849", emoji="<:illumos:1538279369259352266>"),
        ]
        self.embed = discord.Embed(
            title="🖼️ Desktop Environment / Window Manager & Apple / Android",
            description=(
                "**🖼️ DE / WM** — Pick any number of **DE / WM**s below, "
                "no limit — you can hold multiple at once.\n\n"
                "**🍎 Apple & Android** — Pick your **Apple & Android** platform "
                "below. You can hold multiple selections at once.\n\n"
                "**🖥️ Other Operating Systems** — Pick your **other OS** roles "
                "below. You can hold multiple selections at once."
            ),
            color=discord.Color.dark_theme(),
        )
        self.add_item(DistroSelect(
            placeholder="🖼️ 1. Select your DE / WM (multi)",
            options=dewm_opts,
            custom_id="roles_dewm",
        ))
        self.add_item(DistroSelect(
            placeholder="🍎 2. Select Apple & Android roles",
            options=apple_android_opts,
            custom_id="roles_apple_android",
        ))
        self.add_item(DistroSelect(
            placeholder="🖥️ 3. Select Other Operating Systems",
            options=otheros_opts,
            custom_id="roles_otheros",
        ))

# ==========================================
# Ticket system
# ==========================================
TICKET_CHANNEL_ID = 1534677201935536218
TICKET_CATEGORY_NAME = "🎫 Tickets"
TICKET_OWNERS = {}

def _ticket_owner_from_channel(channel):
    if channel and channel.name and channel.name.startswith("ticket-"):
        try:
            return int(channel.name.split("-", 1)[1])
        except (ValueError, IndexError):
            return None
    return None

def _is_ticket_channel(channel):
    if not channel or not isinstance(channel, discord.TextChannel):
        return False
    if channel.name.startswith("ticket-"):
        return True
    return bool(channel.category and channel.category.name == TICKET_CATEGORY_NAME)

def _ticket_menu_embed():
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description=(
            "Need help from the staff team?\n\n"
            "Click the button below to **open a private ticket**. "
            "A moderator will assist you as soon as possible.\n\n"
            "⚠️ **WARNING**\n"
            "Tickets are reserved for real support requests. "
            "Opening unnecessary tickets or abusing this system may result in "
            "a **penalty (warning / mute / ban)**."
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="Tickets are handled by our moderators.")
    return embed

async def _ticket_menu_posted():
    try:
        doc = await config_collection.find_one({"_id": "ticket_menu"})
        return bool(doc and doc.get("posted"))
    except Exception:
        return True

async def _set_ticket_menu_posted():
    try:
        await config_collection.update_one({"_id": "ticket_menu"}, {"$set": {"posted": True}}, upsert=True)
    except Exception as e:
        print(f"Ticket menu save error: {e}")

class TicketCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_close")

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        owner_id = TICKET_OWNERS.get(channel.id) if channel else None
        if owner_id is None:
            owner_id = _ticket_owner_from_channel(channel)
        is_mod = interaction.user.guild_permissions.manage_messages or interaction.user.guild_permissions.administrator
        if not (is_mod or interaction.user.id == owner_id):
            return await interaction.response.send_message(
                "❌ Only the ticket owner or a moderator can close this ticket.", ephemeral=True
            )
        try:
            await interaction.response.send_message("🔒 **This ticket is being closed. Thank you for reaching out!**")
        except Exception:
            try:
                await interaction.response.defer()
            except Exception:
                pass
        await asyncio.sleep(2)
        TICKET_OWNERS.pop(channel.id, None)
        try:
            await channel.delete()
        except Exception:
            pass

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCloseButton())

class TicketOpenButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎫 Open a Ticket", style=discord.ButtonStyle.primary, custom_id="ticket_open")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(guild.channels, name=f"ticket-{user.id}")
        if existing:
            return await interaction.response.send_message(
                f"❌ You already have an open ticket: {existing.mention}", ephemeral=True
            )

        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            try:
                category = await guild.create_category(TICKET_CATEGORY_NAME, position=len(guild.categories))
            except discord.HTTPException:
                category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
                if not category:
                    return await interaction.response.send_message(
                        "❌ Failed to create the ticket category. Please try again later.", ephemeral=True
                    )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True, add_reactions=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_messages=True,
                manage_channels=True, read_message_history=True, embed_links=True,
                attach_files=True, add_reactions=True
            )
        }
        for role in guild.roles:
            if role.permissions.manage_messages or role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True,
                    embed_links=True, attach_files=True, add_reactions=True
                )

        try:
            channel = await guild.create_text_channel(f"ticket-{user.id}", category=category, overwrites=overwrites)
        except discord.HTTPException:
            return await interaction.response.send_message(
                "❌ Failed to create the ticket channel. Please try again later.", ephemeral=True
            )
        TICKET_OWNERS[channel.id] = user.id

        embed = discord.Embed(
            title="🎫 Ticket Opened",
            description=(
                f"Welcome, {user.mention}! A moderator will be with you shortly.\n\n"
                "Please describe your issue in detail so we can help you as quickly as possible.\n\n"
                "⚠️ **IMPORTANT**\n"
                "Please do not open unnecessary tickets or spam this channel. "
                "Abusing the ticket system may result in a **penalty (warning / mute / ban)**."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Ticket ID: {channel.id} | Owner: {user}")
        await channel.send(embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"✅ Your ticket has been opened: {channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketOpenButton())

@bot.hybrid_command(name="ticketsetup", description="Posts the ticket menu in the ticket channel.")
async def ticketsetup(ctx):
    if not (ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator):
        return await ctx.send("❌ You don't have permission to use this command.", ephemeral=True)
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if not channel:
        return await ctx.send("❌ Ticket channel not found. Check TICKET_CHANNEL_ID.", ephemeral=True)
    await channel.send(embed=_ticket_menu_embed(), view=TicketView())
    await ctx.send(f"✅ Ticket menu posted in {channel.mention}", ephemeral=True)

@bot.hybrid_command(name="close", description="Closes the current ticket channel. Moderators and the ticket owner can use this.")
async def close_ticket(ctx):
    channel = ctx.channel
    if not _is_ticket_channel(channel):
        return await ctx.send("❌ This command can only be used inside a ticket channel.", ephemeral=True)
    owner_id = TICKET_OWNERS.get(channel.id)
    if owner_id is None:
        owner_id = _ticket_owner_from_channel(channel)
    is_mod = ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator
    if not (is_mod or ctx.author.id == owner_id):
        return await ctx.send("❌ Only the ticket owner or a moderator can close this ticket.", ephemeral=True)
    await ctx.send("🔒 **This ticket is being closed. Thank you for reaching out!**")
    await asyncio.sleep(2)
    TICKET_OWNERS.pop(channel.id, None)
    try:
        await channel.delete()
    except Exception:
        pass

# ==========================================
# Background loops
# ==========================================
@tasks.loop(minutes=30)
async def half_hourly_reminder():
    # NOTE: this body previously had NO try/except at all. Any failure
    # here (e.g. channel.send() hitting discord.Forbidden, a rate
    # limit, or a network blip) used to propagate all the way up and
    # PERMANENTLY stop this loop for the rest of the process's life —
    # with no automatic retry and only a bare stderr traceback as a
    # trace. It is now caught and logged, and the .error() handler
    # below acts as a second safety net either way.
    await bot.wait_until_ready()
    global REMINDER_CHANNEL_ID, last_activity_time
    try:
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
    except Exception as e:
        logger.error(f"Half-hourly reminder error: {e}", exc_info=True)


@half_hourly_reminder.error
async def half_hourly_reminder_error(error):
    # discord.py calls this automatically if the loop body above ever
    # raises anyway. Without this, the loop silently stops forever and
    # the only trace is a bare stderr traceback that is easy to miss.
    logger.error(f"half_hourly_reminder loop crashed: {error}", exc_info=error)


@tasks.loop(hours=24)
async def reset_daily_xp():
    try:
        await xp_collection.update_many({}, {"$set": {"daily": 0}})
    except Exception as e:
        logger.error(f"Failed to reset daily XP: {e}", exc_info=True)


@reset_daily_xp.error
async def reset_daily_xp_error(error):
    logger.error(f"reset_daily_xp loop crashed: {error}", exc_info=error)

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
        await save_news_state(entry.link)  # persist immediately so a restart never reposts this article again
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
        logger.error(f"Tech news stream error: {e}", exc_info=True)


@daily_tech_news.error
async def daily_tech_news_error(error):
    logger.error(f"daily_tech_news loop crashed: {error}", exc_info=error)


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
        logger.error(f"Sunday Event Error: {e}", exc_info=True)
        ACTIVE_EVENT_CHANNEL_ID = None
        await clear_event_state()


@sunday_xp_event.error
async def sunday_xp_event_error(error):
    logger.error(f"sunday_xp_event loop crashed: {error}", exc_info=error)


# ==========================================
# Startup / lifecycle events
# ==========================================
@bot.event
async def on_ready():
    print('==========================================')
    print(f'🤖 Bot Is Online: {bot.user.name}')
    print('🚀 Engine Status: READY AND OPERATIONAL')
    print('==========================================')
    global last_activity_time, ACTIVE_EVENT_CHANNEL_ID, LAST_NEWS_URL
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
        print('❌ MongoDB Connection Error: Database is NOT reachable! XP, warnings and configs will fail to save.')
        print(f'   Details: {e}')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Slash Commands: {len(synced)} command(s) synced globally. (May take up to 1 hour to appear everywhere the first time.)')
    except Exception as e:
        print(f'❌ Slash Command Sync Error: {e}')
    await bot.change_presence(activity=discord.Game(name="Managing the Server | ?help or /help"))

    # on_ready can fire more than once over a long uptime (e.g. after a
    # dropped gateway session forces a full re-identify instead of a
    # resume). Calling .start() on a loop that is already running
    # raises RuntimeError, which — since this used to have no
    # is_running() guard — would abort the rest of on_ready right here
    # and skip everything below (event/news/distro state restoration).
    # is_running() makes every restart/reconnect idempotent and safe.
    for loop_job in (half_hourly_reminder, reset_daily_xp, daily_tech_news, sunday_xp_event, daily_distro_vs, clear_memory_caches):
        if not loop_job.is_running():
            loop_job.start()
    try:
        bot.add_view(RolesView())
        bot.add_view(DewmView())
        bot.add_view(TicketView())
    except Exception as e:
        print(f"View registration error: {e}")
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

    # Restore last posted tech-news URL so a bot restart/redeploy never reposts
    # the same article to the news channel again.
    try:
        news_state = await load_news_state()
        if news_state and news_state.get("last_url"):
            LAST_NEWS_URL = news_state["last_url"]
            print(f"📰 Restored last posted news URL from DB — duplicate re-posts after restart are prevented.")
    except Exception as e:
        print(f"News state restore error: {e}")

    # Restore the configured Distro VS channel + last-sent timestamp so the
    # 12-hour cadence survives bot restarts too (see distro_vs section below).
    try:
        distro_state = await load_distro_vs_config()
        if distro_state and distro_state.get("channel_id"):
            print(f"⚔️ Distro VS channel restored: {distro_state['channel_id']} "
                  f"(last sent: {distro_state.get('last_sent', 'never')}).")
        else:
            print("⚔️ Distro VS channel not configured yet — use ?setdistrochannel to set one.")
    except Exception as e:
        print(f"Distro VS state restore error: {e}")

    # Apply channel settings: 3s slowmode everywhere, open media to everyone
    # in the media channels, and let everyone type/post media in the epic
    # milestone channel (media gate devre dışı bırakıldı — her tür medya serbest).
    try:
        for channel_id in MEDIA_CHANNEL_IDS + [EPIC_LEVEL_100_CHANNEL]:
            channel = bot.get_channel(channel_id)
            if channel is None:
                continue
            try:
                await channel.edit(slowmode_delay=3)
            except Exception as e:
                print(f"  ⚠️ Could not set slowmode on {channel_id}: {e}")
            try:
                await channel.set_permissions(
                    channel.guild.default_role,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                )
            except Exception as e:
                print(f"  ⚠️ Could not open send/media perms on {channel_id}: {e}")
    except Exception as e:
        print(f"Channel settings error: {e}")

    # Post the ticket menu in the ticket channel once (persisted in DB so a
    # restart never duplicates the menu message).
    try:
        if not await _ticket_menu_posted():
            ticket_channel = bot.get_channel(TICKET_CHANNEL_ID)
            if ticket_channel:
                await ticket_channel.send(embed=_ticket_menu_embed(), view=TicketView())
                await _set_ticket_menu_posted()
                print("🎫 Ticket menu posted in the ticket channel.")
    except Exception as e:
        print(f"Ticket menu post error: {e}")

    # Every startup/redeploy: wipe the roles channel, lock it (@everyone
    # can't type — same as ?sudolock) and post a fresh role menu so the
    # selection is always clean and available at <#1521868274240065597>.
    try:
        roles_channel = bot.get_channel(ROLES_CHANNEL_ID)
        if roles_channel is None:
            print(f"⚠️ Roles channel not found: {ROLES_CHANNEL_ID}")
        else:
            try:
                await roles_channel.purge(limit=None)
            except Exception as e:
                print(f"  ⚠️ Roles channel purge failed: {e}")
            try:
                await roles_channel.set_permissions(
                    roles_channel.guild.default_role, send_messages=False
                )
            except Exception as e:
                print(f"  ⚠️ Roles channel lock failed: {e}")
            roles_view = RolesView()
            await roles_channel.send(embed=roles_view.embed, view=roles_view)
            dewm_view = DewmView()
            await roles_channel.send(embed=dewm_view.embed, view=dewm_view)
            print("🎭 Roles menus posted (5 categories + DE/WM & Apple/Android second message).")
    except Exception as e:
        print(f"Roles menu post error: {e}")

    # Kernel release: announced only when a new build is actually pending
    # (?kernelnotes was used before the deploy). A plain restart therefore
    # never bumps the version number or spams the kernel channel.
    try:
        pending = await _kernel_get_pending_changelog()
        if pending:
            await _kernel_announce(pending)
        else:
            print("🐧 No pending kernel release — version unchanged.")
    except Exception as e:
        print(f"Kernel release error: {e}")

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
    # Memory hygiene: drop this member's in-RAM cache rows immediately so we
    # don't keep data for users who no longer exist.
    user_message_cache.pop(member.id, None)
    xp_message_counter.pop(member.id, None)
    last_user_message_time.pop(member.id, None)
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

@bot.event
async def on_guild_channel_delete(channel):
    # A terminal channel can disappear by being deleted directly (not just
    # via ?close); always clean up its sandbox state to avoid a memory leak.
    TERMINAL_STATE.pop(channel.id, None)

# ==========================================
# Warning system
# ==========================================
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

# ==========================================
# Terminal sandbox: allow-list and safety checks
# ==========================================
# The terminal lets people run small python snippets in Discord. That's a
# whole-ass security surface, so this sandbox got a glow-up:
#   - code runs in a SEPARATE disposable process (never in the bot's memory),
#   - imports are allow-listed, dangerous stdlib leaks get scrubbed,
#   - timeouts are enforced by killing the process, not by thread tricks,
#   - everything below is defense in depth: static AST filter first, then a
#     fresh interpreter with restricted builtins that re-checks itself.
# Curated list of standard-library modules that are (mostly) harmless in a
# text-only, no-filesystem, no-network sandbox. Anything not on this list is
# rejected by check_code_safety(). Modules that leak `os` / `sys` / `threading`
# / etc. at top level or in submodules (queue, email, xml, uuid, secrets,
# gettext, locale, argparse, dataclasses, traceback, timeit, plistlib, ...)
# are intentionally NOT here. The child process also scrubs those leaked
# module attributes at runtime as a second layer (see _BLOCKED_LEAK_MODULES).
ALLOWED_TERMINAL_MODULES = {
    "random", "time", "math", "datetime", "string", "re", "itertools",
    "functools", "collections", "statistics", "json", "textwrap", "calendar",
    "decimal", "fractions", "cmath", "bisect", "heapq", "copy", "enum",
    "typing", "operator", "unicodedata", "difflib", "pprint", "array",
    "keyword", "numbers", "colorsys", "types", "warnings", "weakref", "abc",
    "contextlib", "graphlib", "zoneinfo", "ipaddress", "html", "csv",
    "hashlib", "struct", "ast", "io", "zlib", "binascii", "base64", "hmac",
    "token", "tokenize", "stringprep",
}

TERMINAL_STATE = {}

# Function names that are blocked when called directly. `open` blocks
# io.open() / codecs.open() / plain open(...) file access; getattr/setattr/
# delattr/vars can smuggle dunder lookups (getattr(obj, "__class__")), and
# breakpoint() drops straight into the debugger, so all of them are removed.
BLOCKED_SAFE_NAMES = [
    "open", "eval", "exec", "compile", "__import__", "globals", "locals",
    "getattr", "setattr", "delattr", "vars", "breakpoint", "memoryview",
]

# Attribute calls that can reach outside the sandbox (subprocess / os.system
# style escapes). "open" covers io.open()/codecs.open()/plain open(), FileIO
# is the other stdlib way to open files, and the os.* / os.path style names
# are dead weight since `os` itself can never be imported. getattr/setattr/
# delattr/vars are handled via BLOCKED_SAFE_NAMES (they smuggle dunders).
BLOCKED_SAFE_ATTRS = [
    "system", "popen", "spawn", "run", "open", "Popen", "call",
    "check_call", "check_output", "getoutput", "getstatusoutput",
    "startfile", "execv", "execve", "execvp", "posix_spawn", "fork",
    "dlopen", "LoadLibrary", "shell", "FileIO", "environ", "getenv",
    "remove", "unlink", "rename", "mkdir", "rmdir", "chmod", "chown",
    "symlink", "link", "listdir", "scandir", "walk",
]


def check_code_safety(code):
    """AST-based safety filter for the terminal sandbox."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                if root_module not in ALLOWED_TERMINAL_MODULES:
                    return False, f"Security Error: Module `{alias.name}` is not on the sandbox allow-list."
        if isinstance(node, ast.ImportFrom):
            root_module = (node.module or "").split(".")[0]
            if root_module not in ALLOWED_TERMINAL_MODULES:
                return False, f"Security Error: Module `{node.module}` is not on the sandbox allow-list."
        if isinstance(node, ast.Attribute):
            # CRITICAL FIX: block ALL dunder attribute access. The classic
            # Python sandbox escape chain reaches into objects through
            # __class__ / __bases__ / __subclasses__ / __globals__ and then
            # runs os.system(...) or reads the bot token from os.environ.
            # Before this check, `().__class__.__bases__[0].__subclasses__()
            # ...` and `io.open("/etc/passwd").read()` completely bypassed
            # the old allow-list. Legitimate sandbox code never calls dunders
            # explicitly (x + y, x[key], len(x) don't produce Attribute
            # nodes), so blocking them costs nothing in practice.
            if node.attr.startswith("__") and node.attr.endswith("__"):
                return False, f"Security Error: Access to `{node.attr}` is blocked in the sandbox."
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in BLOCKED_SAFE_NAMES:
                    return False, f"Security Error: The function `{node.func.id}` is blocked in the sandbox."
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in BLOCKED_SAFE_ATTRS:
                    return False, f"Security Error: The attribute `{node.func.attr}` is blocked."
                # .format() is blocked because the old dunder-escape chain
                # (`"{0.__class__.__bases__[0]}".format(...)`) hid dunder
                # lookups from the AST walker — plain attribute access.
                # f-strings still work fine, so this costs nothing real.
                if node.func.attr in ("format", "format_map"):
                    return False, "Security Error: str.format() / format_map() are blocked in the sandbox."
    return True, ""

TERMINAL_TIMEOUT = 15.0
TERMINAL_INPUT_TIMEOUT = 60.0
MEMORY_LIMIT_MB = 256.0

# User code now runs in a whole separate Python process, not in a bot thread.
# The old thread watchdog (ctypes SetAsyncExc) could not stop C-level loops,
# and a stuck thread corrupted bot state. A subprocess can just be killed —
# an infinite loop, a memory hog or even a native crash can only take out
# the disposable child, never the bot. Markers on the child's stderr tell
# the bot that input() is blocking (prompt) and that a line was consumed.
_SANDBOX_INPUT_MARK = "\x00INPUT\x00"
_SANDBOX_OK_MARK = "\x00OK\x00"

# Module roots scrubbed out of any imported module in the child. Some stdlib
# modules (binhex.os, uuid.os, contextlib.os, argparse._os, queue.threading,
# enum.sys, ...) leak a handle to os/sys/subprocess as a plain attribute, and
# `module.os.system(...)` would skip right past the AST checks. The child
# sets every attribute pointing at one of these to None after importing.
_BLOCKED_LEAK_MODULES = frozenset({
    "os", "sys", "subprocess", "shutil", "ctypes", "importlib", "pathlib",
    "socket", "tempfile", "threading", "multiprocessing", "pickle", "marshal",
    "inspect", "platform", "getpass", "signal", "resource", "mmap", "zipfile",
    "tarfile", "gzip", "bz2", "lzma", "shlex", "urllib", "http", "ftplib",
    "smtplib", "poplib", "imaplib", "nntplib", "readline", "pdb", "bdb",
    "code", "codeop", "site", "builtins", "winreg", "msvcrt", "winsound",
    "posix", "pwd", "grp", "spwd", "crypt", "tty", "termios", "fcntl",
    "select", "tracemalloc", "pkgutil",
})

# The child process bootstrap. User code and config travel through environment
# variables (never the command line), so no quoting weirdness and nothing
# user-controlled can hit the shell. The child re-checks the allow-list
# itself, scrubs leaked modules, applies the memory cap where the OS allows,
# enforces its own compute cap (best effort — the parent kill is the real
# backstop), and proxies print()/input() over pipes.
_CHILD_HARNESS = r'''
import base64
import ctypes
import io
import os as _os
import sys as _sys
import threading as _threading
import traceback as _traceback

CODE = base64.b64decode(_os.environ["AP_SANDBOX_CODE_B64"]).decode("utf-8", "replace")
ALLOWED = frozenset(eval(_os.environ["AP_SANDBOX_ALLOWED"]))
COMPUTE_TIMEOUT = float(_os.environ["AP_SANDBOX_TIMEOUT"])
MEMORY_LIMIT_MB = float(_os.environ["AP_SANDBOX_MEMORY_MB"])

try:
    import resource as _resource
    _cap = int(MEMORY_LIMIT_MB * 1024 * 1024)
    _resource.setrlimit(_resource.RLIMIT_AS, (_cap, _cap))
except Exception:
    pass

BLOCKED_ROOTS = frozenset(_os.environ["AP_SANDBOX_BLOCKED"].split(","))

def _scrub_module(mod):
    if mod is None:
        return
    try:
        items = list(mod.__dict__.items())
    except Exception:
        return
    for name, val in items:
        if isinstance(val, type(_sys)):
            root = (getattr(val, "__name__", "") or "").split(".")[0]
            if root in BLOCKED_ROOTS:
                try:
                    mod.__dict__[name] = None
                except Exception:
                    pass

def _scrub_tree(mod):
    seen = set()
    stack = [mod]
    while stack:
        cur = stack.pop()
        if id(cur) in seen:
            continue
        seen.add(id(cur))
        _scrub_module(cur)
        for name, val in list(cur.__dict__.items()):
            if isinstance(val, type(_sys)):
                stack.append(val)

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".")[0]
    if root not in ALLOWED:
        raise ImportError(f"Module '{name}' is not on the sandbox allow-list.")
    mod = __import__(name, globals, locals, fromlist, level)
    _scrub_tree(mod)
    return mod

_OUT = io.StringIO()

code_text = CODE
_input_lines = []
if "---INPUT---" in code_text:
    code_text, _, _input_block = code_text.partition("---INPUT---")
    _input_lines = [ln for ln in _input_block.strip().splitlines()]
_input_iter = iter(_input_lines)

def _sand_print(*args, sep=" ", end="\n", file=None):
    text = sep.join(str(a) for a in args) + end
    if file is None:
        _OUT.write(text)
    else:
        try:
            file.write(text)
        except Exception:
            _OUT.write(text)

def _raise_in_main(exc_type):
    tid = _threading.main_thread().ident
    if tid is None:
        return
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exc_type))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.c_long(0))

class _ComputeWatchdog:
    def __init__(self, limit):
        self._limit = limit
        self._timer = None

    def arm(self):
        self.cancel()
        self._timer = _threading.Timer(self._limit, _raise_in_main, args=(TimeoutError,))
        self._timer.daemon = True
        self._timer.start()

    def cancel(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

_watchdog = _ComputeWatchdog(COMPUTE_TIMEOUT)

def _sand_input(prompt=""):
    if prompt:
        _OUT.write(str(prompt))
    try:
        return next(_input_iter)
    except StopIteration:
        pass
    _watchdog.cancel()
    try:
        print("\x00INPUT\x00" + str(prompt), file=_sys.stderr, flush=True)
    except Exception:
        pass
    try:
        line = _sys.stdin.readline()
    except Exception:
        line = ""
    try:
        print("\x00OK\x00", file=_sys.stderr, flush=True)
    except Exception:
        pass
    _watchdog.arm()
    return line.rstrip("\r\n")

_safe_builtins = {
    "print": _sand_print, "input": _sand_input, "range": range, "len": len,
    "int": int, "float": float, "str": str, "bool": bool, "list": list,
    "dict": dict, "set": set, "tuple": tuple, "sum": sum, "min": min,
    "max": max, "abs": abs, "round": round, "type": type,
    "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
    "IndexError": IndexError, "KeyError": KeyError, "ZeroDivisionError": ZeroDivisionError,
    "StopIteration": StopIteration, "enumerate": enumerate, "zip": zip,
    "map": map, "filter": filter, "all": all, "any": any, "sorted": sorted,
    "reversed": reversed, "isinstance": isinstance, "issubclass": issubclass,
    "chr": chr, "ord": ord, "hex": hex, "oct": oct, "bin": bin, "pow": pow,
    "divmod": divmod, "frozenset": frozenset, "iter": iter, "next": next,
    "__import__": _safe_import,
}
_env = {"__builtins__": _safe_builtins}

_watchdog.arm()
try:
    exec(code_text, _env, _env)
except TimeoutError:
    _OUT.write("Timeout Error: Code execution took too long (%d second limit, infinite loop?).\n" % int(COMPUTE_TIMEOUT))
except MemoryError:
    _OUT.write("Memory Error: Code tried to use too much memory.\n")
except Exception as e:
    _OUT.write("".join(_traceback.format_exception_only(type(e), e)).strip() + "\n")
finally:
    _watchdog.cancel()

_sys.stdout.write(_OUT.getvalue())
_sys.stdout.flush()
'''


def _build_child_environment(code):
    env = dict(os.environ)
    env["AP_SANDBOX_CODE_B64"] = base64.b64encode(code.encode("utf-8")).decode("ascii")
    env["AP_SANDBOX_ALLOWED"] = repr(sorted(ALLOWED_TERMINAL_MODULES))
    env["AP_SANDBOX_TIMEOUT"] = repr(TERMINAL_TIMEOUT)
    env["AP_SANDBOX_MEMORY_MB"] = repr(MEMORY_LIMIT_MB)
    env["AP_SANDBOX_BLOCKED"] = ",".join(sorted(_BLOCKED_LEAK_MODULES))
    return env


async def _send_terminal_prompt(channel_id, prompt):
    channel = bot.get_channel(channel_id)
    if channel is None:
        return
    try:
        extra = f" Prompt: `{prompt}`" if prompt else ""
        await channel.send(f"⌨️ **input() is waiting** for your message (up to 60 seconds)...{extra}")
    except Exception:
        pass


async def _send_terminal_note(channel_id, text):
    channel = bot.get_channel(channel_id)
    if channel is None:
        return
    try:
        await channel.send(text)
    except Exception:
        pass


def execute_sandbox_sync(code, channel_id=None, loop=None):
    """Runs user code in a fresh, disposable Python subprocess.

    A subprocess — not a thread — is the real sandbox boundary. User code
    never executes inside the bot, so an infinite loop, memory blow-up or
    native crash can only kill the child. The parent streams the child's
    stdout/stderr back, feeds input() through the stdin pipe, and kills the
    child once the total budget (compute + input wait + margin) runs out.
    """
    check_code = code
    if "---INPUT---" in code:
        check_code, _, _ = code.partition("---INPUT---")
    safe, msg = check_code_safety(check_code)
    if not safe:
        return msg

    state = TERMINAL_STATE.get(channel_id) if channel_id else None
    if state is None:
        state = {"waiting": threading.Event(), "values": [], "need_input": False}
        if channel_id:
            TERMINAL_STATE[channel_id] = state
    state["waiting"].clear()
    state["values"].clear()
    state["need_input"] = False

    try:
        child = subprocess.Popen(
            [sys.executable, "-u", "-c", _CHILD_HARNESS],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_build_child_environment(code),
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as e:
        return f"Sandbox Error: could not start worker process ({e})"

    out_lines = []
    err_lines = []

    def _stdout_reader():
        while True:
            line = child.stdout.readline()
            if line == "":
                break
            out_lines.append(line)

    def _stderr_reader():
        while True:
            line = child.stderr.readline()
            if line == "":
                break
            if line.startswith(_SANDBOX_INPUT_MARK):
                prompt = line[len(_SANDBOX_INPUT_MARK):].rstrip("\r\n")
                state["need_input"] = True
                if loop is not None:
                    try:
                        asyncio.run_coroutine_threadsafe(
                            _send_terminal_prompt(channel_id, prompt), loop).result(timeout=5)
                    except Exception:
                        pass
            elif line.startswith(_SANDBOX_OK_MARK):
                state["need_input"] = False
            else:
                err_lines.append(line)

    readers = [
        threading.Thread(target=_stdout_reader, daemon=True),
        threading.Thread(target=_stderr_reader, daemon=True),
    ]
    for t in readers:
        t.start()

    total_deadline = time.monotonic() + TERMINAL_TIMEOUT + TERMINAL_INPUT_TIMEOUT + 10.0
    input_deadline = None
    timed_out = False
    try:
        while True:
            if child.poll() is not None:
                break
            if time.monotonic() >= total_deadline:
                timed_out = True
                break
            if state["need_input"]:
                # Input sent before the child signalled input() must not get
                # stranded — drain it immediately, no waiting involved.
                if state["values"]:
                    while state["values"]:
                        value = state["values"].pop(0)
                        try:
                            child.stdin.write(value + "\n")
                            child.stdin.flush()
                        except Exception:
                            break
                    input_deadline = None
                    continue
                if input_deadline is None:
                    input_deadline = time.monotonic() + TERMINAL_INPUT_TIMEOUT
                remaining = min(total_deadline, input_deadline) - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                got = state["waiting"].wait(remaining)
                state["waiting"].clear()
                if got:
                    while state["values"]:
                        value = state["values"].pop(0)
                        try:
                            child.stdin.write(value + "\n")
                            child.stdin.flush()
                        except Exception:
                            break
                    input_deadline = None
            else:
                state["waiting"].wait(0.3)
                state["waiting"].clear()
    finally:
        try:
            child.stdin.close()
        except Exception:
            pass
        if child.poll() is None:
            try:
                child.kill()
            except Exception:
                pass
            child.wait()

    for t in readers:
        t.join(timeout=2.0)

    stdout = "".join(out_lines)
    stderr = "".join(err_lines)

    if timed_out:
        if loop is not None and state["need_input"]:
            try:
                asyncio.run_coroutine_threadsafe(
                    _send_terminal_note(channel_id, "⏰ No input received within 60 seconds."), loop).result(timeout=5)
            except Exception:
                pass
        note = "Timeout Error: Code execution took too long and was killed by the sandbox (infinite loop or input() timeout).\n"
        if not stdout:
            stdout = note
        elif not stdout.endswith("\n"):
            stdout += "\n" + note
        else:
            stdout += note
    elif child.returncode != 0:
        if stderr:
            stdout += f"\n[Sandbox process crashed with exit code {child.returncode}]\n{stderr}"
        else:
            stdout += f"\n[Sandbox process crashed with exit code {child.returncode}]"

    state["values"].clear()
    state["waiting"].clear()
    state["need_input"] = False
    return stdout


async def execute_sandbox(code, channel_id=None):
    """Runs the sandbox on a worker thread. The child process is hard-killed
    once the total budget (compute + input wait + margin) is exhausted."""
    loop = asyncio.get_running_loop()
    try:
        future = loop.run_in_executor(None, execute_sandbox_sync, code, channel_id, loop)
        output = await asyncio.wait_for(future, timeout=TERMINAL_INPUT_TIMEOUT + TERMINAL_TIMEOUT + 15.0)
        return output
    except asyncio.TimeoutError:
        return "Timeout Error: Code execution took too long (infinite loop?)."
    except Exception as e:
        return f"Execution Error: {e}"

TERMINAL_HELP_TEXT = (
    "```text\n"
    "AdminPingu Sandbox Terminal - Help\n"
    "-----------------------------------\n"
    "Allowed imports (" + str(len(ALLOWED_TERMINAL_MODULES)) + " modules):\n"
    + ", ".join(sorted(ALLOWED_TERMINAL_MODULES)) + "\n\n"
    "Allowed builtins: print, input, range, len, int, float, str, bool, list,\n"
    "dict, set, tuple, sum, min, max, abs, round, type, enumerate, zip, map,\n"
    "filter, all, any, sorted, reversed, isinstance, issubclass, chr, ord,\n"
    "hex, oct, bin, pow, divmod, frozenset, iter, next, plus common exceptions.\n\n"
    "Blocked: open, eval, exec, compile, __import__ (raw), globals, locals,\n"
    "getattr, setattr, delattr, vars, breakpoint, str.format/format_map,\n"
    "os.system/popen/spawn/run, io.open/codecs.open/FileIO, ALL __dunder__\n"
    "attribute access (__class__, __subclasses__, __globals__ ...), and any\n"
    "module not in the list above.\n\n"
    "Isolation:\n"
    "  Your code runs in a separate disposable Python process. Infinite\n"
    "  loops, memory hogs or crashes can never take the bot down; the\n"
    "  process is simply killed. No filesystem, no network, no env access.\n\n"
    "Live input() (60 seconds):\n"
    "  The bot now waits live for your reply. When your code calls input(),\n"
    "  it posts a prompt and waits up to 60 seconds for your next message.\n"
    "  You can also pre-feed values: add a line with only ---INPUT--- after\n"
    "  your code, then one value per line below it. Example:\n\n"
    "  name = input('Name: ')\n"
    "  print('Hello,', name)\n"
    "  ---INPUT---\n"
    "  Sunia\n\n"
    "Time limits:\n"
    "  Compute (incl. infinite loops / animations) is capped at 15 seconds.\n"
    "  input() waits up to 60 seconds per call.\n"
    "  Memory is capped at 256 MB where the OS supports it.\n\n"
    "Type close() or exit() to delete this terminal.\n"
    "```"
)

# ==========================================
# /customize command: font, background image and color picker
# ==========================================
FONTS_DIR = "fonts"
FONT_OPTIONS = [
    ("Arial", "ARIAL.TTF"),
    ("Alunas", "Alunas.ttf"),
    ("Brithany Calligraphy", "Brithany Calligraphy.ttf"),
    ("Diploma", "Diploma.ttf"),
    ("Impacted", "Impacted.ttf"),
    ("Olde English", "OldeEnglish.ttf"),
    ("Realtime", "Realtime.ttf"),
    ("Terminus", "TerminusTTF-4.49.3.ttf"),
    ("D2K", "d2k.ttf"),
    ("Impact", "impact.ttf"),
    ("Unicode Impact", "unicode.impact.ttf"),
]
DEFAULT_FONT_FILE = "impact.ttf"
DEFAULT_COLOR_HEX = "#cba6f7"
MAX_BACKGROUND_BYTES = 3 * 1024 * 1024
ALLOWED_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")

def get_font_path(filename):
    path = os.path.join(FONTS_DIR, filename)
    return path if os.path.exists(path) else None

async def get_user_customization(user_id):
    try:
        doc = await customization_collection.find_one({"_id": user_id})
    except Exception:
        doc = None
    if not doc:
        doc = {}
    return {
        "font": doc.get("font", DEFAULT_FONT_FILE),
        "color": doc.get("color", DEFAULT_COLOR_HEX),
        "bg_data": doc.get("bg_data")
    }

async def save_user_customization(user_id, state):
    await customization_collection.update_one(
        {"_id": user_id},
        {"$set": {
            "font": state["font"],
            "color": state["color"],
            "bg_data": state.get("bg_data")
        }},
        upsert=True
    )

def hex_to_rgb(hex_str):
    hex_str = hex_str.strip().lstrip("#")
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))

async def render_stats_card(member, current_xp, current_level, next_level_xp, prev_level_xp, custom):
    width, height = 900, 280
    color_hex = custom.get("color", DEFAULT_COLOR_HEX)

    if custom.get("bg_data"):
        try:
            raw = base64.b64decode(custom["bg_data"])
            bg_image = Image.open(io.BytesIO(raw)).convert("RGBA").resize((width, height))

            # BUGFIX: this used to be `Editor(bg_image.convert("RGB"))` followed
            # by `background.rectangle(..., color=(0, 0, 0, 140))` to darken the
            # background so the text stays readable on top of it. That looked
            # right, but Pillow's ImageDraw.rectangle() does NOT alpha-blend a
            # semi-transparent fill against the pixels already there — it just
            # overwrites that region with the literal (0, 0, 0, 140) RGBA value.
            # Since the darken rectangle covered the entire card (0,0)-(width,
            # height), it was wiping out the whole uploaded background image
            # every single time, leaving only a flat near-black card behind —
            # exactly the "background doesn't show up" bug.
            #
            # The fix: do the darkening ourselves with a real alpha composite
            # (Image.alpha_composite), which properly blends a translucent
            # black layer over the background instead of replacing it.
            dark_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 140))
            bg_image = Image.alpha_composite(bg_image, dark_overlay)

            background = Editor(bg_image)
        except Exception:
            background = Editor(Canvas((width, height), color="#1e1e2e"))
    else:
        background = Editor(Canvas((width, height), color="#1e1e2e"))

    font_file = custom.get("font", DEFAULT_FONT_FILE)
    font_path = get_font_path(font_file)
    if font_path:
        title_font = Font(path=font_path, size=30)
        text_font = Font(path=font_path, size=20)
    else:
        title_font = Font.poppins(variant="bold", size=30)
        text_font = Font.poppins(size=20)

    avatar_image = await load_image_async(str(member.display_avatar.url))
    profile = Editor(avatar_image).resize((120, 120)).circle_image()
    background.paste(profile, (30, 80))

    background.text((170, 40), member.name, font=title_font, color=color_hex)
    background.text((170, 90), f"Level {current_level}", font=text_font, color=color_hex)

    xp_into_level = max(current_xp - prev_level_xp, 0)
    xp_needed_for_level = max(next_level_xp - prev_level_xp, 1)
    percentage = min(max(xp_into_level / xp_needed_for_level, 0.0), 1.0)

    bar_x, bar_y, bar_w, bar_h = 170, 140, 680, 30
    background.rectangle((bar_x, bar_y), width=bar_w, height=bar_h, radius=15, color="#313244")
    fill_width = max(int(bar_w * percentage), bar_h) if percentage > 0 else 0
    if fill_width > 0:
        background.rectangle((bar_x, bar_y), width=fill_width, height=bar_h, radius=15, color=color_hex)
    background.text((bar_x, bar_y + 35), f"{current_xp} / {next_level_xp} XP", font=text_font, color="#cdd6f4")

    return discord.File(fp=background.image_bytes, filename="stats.png")

class HexColorModal(Modal, title="Set Your Stats Color"):
    hex_input = TextInput(label="Hex color (e.g. #89b4fa)", placeholder="#89b4fa", min_length=4, max_length=7, required=True)

    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        value = self.hex_input.value.strip()
        if not value.startswith("#"):
            value = "#" + value
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            return await interaction.response.send_message("❌ That's not a valid hex color. Use a format like `#89b4fa`.", ephemeral=True)
        self.parent_view.state["color"] = value
        await interaction.response.send_message(f"✅ Color set to `{value}`.", ephemeral=True)

class CustomizeView(View):
    def __init__(self, author, initial_state):
        super().__init__(timeout=300)
        self.author = author
        self.state = dict(initial_state)
        self.message = None

        font_select = Select(
            placeholder="Choose a font for your stats card",
            options=[discord.SelectOption(label=label, value=fname) for label, fname in FONT_OPTIONS],
            min_values=1, max_values=1
        )
        font_select.callback = self.on_font_selected
        self.add_item(font_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This customization menu isn't yours.", ephemeral=True)
            return False
        return True

    async def on_font_selected(self, interaction: discord.Interaction):
        self.state["font"] = interaction.data["values"][0]
        await interaction.response.send_message(f"✅ Font set to `{self.state['font']}`.", ephemeral=True)

    @discord.ui.button(label="Set Color", style=discord.ButtonStyle.primary, emoji="🎨")
    async def set_color_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(HexColorModal(self))

    @discord.ui.button(label="Upload Background", style=discord.ButtonStyle.secondary, emoji="🖼️")
    async def set_background_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📤 Send an image (`.jpg`, `.jpeg`, `.png`, or `.webp`, under 3MB) in this channel within 60 seconds.",
            ephemeral=True
        )

        def check(m):
            return m.author.id == self.author.id and m.channel.id == interaction.channel.id and m.attachments

        try:
            msg = await bot.wait_for('message', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            return await interaction.followup.send("❌ Timed out waiting for an image.", ephemeral=True)

        attachment = msg.attachments[0]
        if not attachment.filename.lower().endswith(ALLOWED_IMAGE_EXTS):
            return await interaction.followup.send("❌ Unsupported file type. Use jpg, jpeg, png, or webp.", ephemeral=True)
        if attachment.size > MAX_BACKGROUND_BYTES:
            return await interaction.followup.send("❌ That image is too large (max 3MB).", ephemeral=True)

        try:
            image_bytes = await attachment.read()
            Image.open(io.BytesIO(image_bytes)).verify()
            self.state["bg_data"] = base64.b64encode(image_bytes).decode("utf-8")
            await interaction.followup.send("✅ Background image saved for preview/finish.", ephemeral=True)
        except Exception:
            await interaction.followup.send("❌ Couldn't read that image, try a different file.", ephemeral=True)
        try:
            await msg.delete()
        except Exception:
            pass

    @discord.ui.button(label="Preview", style=discord.ButtonStyle.secondary, emoji="👁️")
    async def preview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            user_data = await xp_collection.find_one({"_id": self.author.id})
        except Exception:
            user_data = None
        if not user_data:
            user_data = {"total": 0}
        current_xp = user_data.get("total", 0)
        current_level = get_level_from_total_xp(current_xp)
        prev_level_xp = get_xp_requirement(current_level)
        next_level_xp = get_xp_requirement(current_level + 1)
        file = await render_stats_card(self.author, current_xp, current_level, next_level_xp, prev_level_xp, self.state)
        await interaction.followup.send(content="Here's a preview with your current settings:", file=file, ephemeral=True)

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, emoji="✅")
    async def finish_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await save_user_customization(self.author.id, self.state)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="✅ Your customization has been saved!", embed=None, view=self)
        self.stop()

    async def on_timeout(self):
        if self.message:
            for child in self.children:
                child.disabled = True
            try:
                await self.message.edit(content="⌛ Customization menu timed out. Run the command again to continue.", view=self)
            except Exception:
                pass

@bot.hybrid_command(name="customize", aliases=["cust", "customise"], description="Personalize your stats card font, color and background.")
async def customize(ctx):
    if ctx.interaction:
        await ctx.defer(ephemeral=True)
    initial_state = await get_user_customization(ctx.author.id)
    embed = discord.Embed(
        title="🎨 Customize Your Stats Card",
        description="Pick a font, set a hex color, and optionally upload a background image.\n"
                    "Use **Preview** anytime, then hit **Finish** to save.",
        color=discord.Color.blurple()
    )
    view = CustomizeView(ctx.author, initial_state)
    message = await ctx.send(embed=embed, view=view, ephemeral=True) if ctx.interaction else await ctx.send(embed=embed, view=view)
    view.message = message

# ==========================================
# Message handling: terminal, media gate, spam filter, profanity filter, XP
# ==========================================
_MEDIA_URL_RE = re.compile(r'https?://\S+\.(?:gif|png|jpe?g|webp|mp4|webm|mov)(?:\?\S*)?', re.IGNORECASE)
_MEDIA_HOST_RE = re.compile(r'(?:tenor\.com|giphy\.com|gph\.is|imgur\.com|coub\.com)', re.IGNORECASE)


def _message_has_media(message):
    if message.attachments:
        return True
    return bool(_MEDIA_URL_RE.search(message.content or "") or _MEDIA_HOST_RE.search(message.content or ""))


def _is_gif_media(message):
    for attachment in message.attachments:
        if attachment.filename.lower().endswith((".gif", ".webm", ".mp4")):
            return True
    if re.search(r'\.gif(?:\?|$)', message.content or "", re.IGNORECASE):
        return True
    return bool(re.search(r'(?:tenor\.com|giphy\.com)', message.content or "", re.IGNORECASE))


@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    # DM FIX: private messages have no guild, category, or Member permissions.
    # Previously `message.channel.category_id` crashed with AttributeError on
    # every DM and aborted the rest of the handler. AdminPingu only operates
    # inside the server, so DMs are simply ignored here.
    if not message.guild:
        return

    # Terminal handler runs first so terminal messages skip spam/XP logic.
    if getattr(message.channel, "category_id", None) == 1534663424322179252 and message.channel.name.startswith("terminal-"):
        is_mod = message.author.guild_permissions.manage_messages
        is_owner = str(message.author.id) in (message.channel.topic or "")

        if is_owner or is_mod:
            raw = message.content.strip()

            if raw.lower() in ['exit()', 'close()', 'exit', 'close', '?close']:
                TERMINAL_STATE.pop(message.channel.id, None)
                await message.channel.delete(reason="User closed terminal.")
                return

            if raw.lower() in ['help-terminal()', 'help-terminal', '?help-terminal']:
                await message.channel.send(TERMINAL_HELP_TEXT)
                return

            # If user code is currently blocked inside input(), feed the next
            # message straight to it instead of treating it as new code.
            state = TERMINAL_STATE.get(message.channel.id)
            if state and state["need_input"] and not state["waiting"].is_set():
                state["values"].append(raw)
                state["waiting"].set()
                try:
                    await message.add_reaction("✔️")
                except Exception:
                    pass
                return

            code = raw
            if code.startswith("```python"): code = code[9:]
            elif code.startswith("```py"): code = code[5:]
            elif code.startswith("```"): code = code[3:]
            if code.endswith("```"): code = code[:-3]
            code = code.strip()

            if not code:
                return

            if message.channel.id not in TERMINAL_STATE:
                TERMINAL_STATE[message.channel.id] = {
                    "waiting": threading.Event(),
                    "values": [],
                    "need_input": False,
                }

            await message.add_reaction("⏳")
            output = await execute_sandbox(code, message.channel.id)

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

    # Media gate: everyone may post media in MEDIA_CHANNEL_IDS. In the epic
    # (level milestone) channel only Level 10+ members may post media, and
    # only GIF media at that. Everywhere else media is left to Discord perms.
    # DISABLED: the epic channel now allows any media (resim/video gibi her tür
    # medya serbest). Geri açmak için aşağıdaki bloğun yorumunu kaldır.
    # if message.channel.id not in MEDIA_CHANNEL_IDS and message.channel.id == EPIC_LEVEL_100_CHANNEL:
    #     if _message_has_media(message):
    #         is_mod = message.author.guild_permissions.manage_messages
    #         has_media_role = any(r.id == MEDIA_ROLE_ID for r in message.author.roles)
    #         if not (is_mod or has_media_role):
    #             try:
    #                 await message.delete()
    #                 await message.channel.send(f"⚠️ {message.author.mention} Only **Level 10+** members can post media in this channel!", delete_after=5)
    #             except Exception:
    #                 pass
    #             return
    #         if not _is_gif_media(message):
    #             try:
    #                 await message.delete()
    #                 await message.channel.send(f"⚠️ {message.author.mention} Only **GIF** media is allowed in this channel!", delete_after=5)
    #             except Exception:
    #                 pass
    #             return

    global last_activity_time
    last_activity_time = time.time()
    last_user_message_time[message.author.id] = time.time()
    is_mod = message.author.guild_permissions.manage_messages
    if not is_mod:
        if message.channel.id != ACTIVE_EVENT_CHANNEL_ID and message.channel.id not in UNRESTRICTED_MEDIA_CHANNEL_IDS:
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
            gained = get_weighted_xp_gain()
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

# ==========================================
# Fuzzy shortcut matcher for the ? prefix
# ==========================================
def _is_subsequence(typed, full):
    it = iter(full)
    return all(ch in it for ch in typed)

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

    startswith_matches = []
    subsequence_matches = []
    for cmd in bot.commands:
        all_names = [cmd.name] + list(cmd.aliases)
        matched_start = any(name.lower().startswith(typed_cmd) for name in all_names)
        matched_subseq = any(_is_subsequence(typed_cmd, name.lower()) for name in all_names)
        if matched_start:
            startswith_matches.append(cmd)
        elif matched_subseq:
            subsequence_matches.append(cmd)

    candidates = startswith_matches if startswith_matches else subsequence_matches
    unique_candidates = list({c.name: c for c in candidates}.values())

    if len(unique_candidates) == 1:
        matched_cmd = unique_candidates[0]
        new_content = f"{prefix}{matched_cmd.name} {rest}".strip()
        message.content = new_content
        await bot.process_commands(message)
        return True
    elif 1 < len(unique_candidates) <= 8:
        options = ", ".join(f"`{prefix}{c.name}`" for c in unique_candidates)
        await message.channel.send(
            f"❓ I'm not sure which command `{prefix}{typed_cmd}` was meant to be. Did you mean: {options}?\n"
            f"Tip: use `?shortcuts` to see all the official short forms."
        )
        return True
    return False

# ==========================================
# Terminal sandbox command
# ==========================================
@bot.hybrid_command(name="terminal", aliases=["term"], description="Opens a private Python sandbox terminal.")
async def terminal(ctx):
    category = bot.get_channel(1534663424322179252)
    if not category or getattr(category, "type", None) is not discord.ChannelType.category:
        category = discord.utils.get(ctx.guild.categories, name__icontains="terminal")
    if not category:
        return await ctx.send("❌ Error: The terminal category (ID `1534663424322179252`) was not found in this server. Make sure the bot can see it.", ephemeral=True)

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
                    f"• Only you and the moderators can see this channel.\n"
                    f"• Only {len(ALLOWED_TERMINAL_MODULES)} whitelisted standard-library modules can be imported.\n"
                    f"• `eval`, `exec`, `compile`, `open`, and raw file/OS access are strictly **BLOCKED**.\n"
                    f"• Infinite loops and animations time out after **15 seconds**.\n"
                    f"• You cannot interact with or harm the Discord bot or the server.\n\n"
                    f"💡 **How to use:**\n"
                    f"Type your Python code directly into the chat and send it! (Code blocks work too).\n"
                    f"`input()` waits live: the bot posts a prompt and waits up to **60 seconds** for your next message.\n"
                    f"Type `help-terminal()` to see the full list of allowed imports and how `input()` works.\n\n"
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
    await ctx.send(f"✅ The automated rules reminder will now be sent to {target_channel.mention} (only when the chat has been active recently).")

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

@bot.hybrid_command(
    name="undo",
    aliases=["undohistory", "cleanbotmsgs"],
    description="Deletes AdminPingu's own recent messages in THIS channel and reports what was removed (mod)."
)
@commands.has_permissions(manage_messages=True)
async def undo(ctx, amount: int = 50):
    """Scoped ONLY to the channel this is run in — scans the last `amount`
    messages in this channel, deletes every one that AdminPingu itself sent,
    and posts a report of exactly what got removed. Useful for wiping old/
    outdated automated posts (e.g. the old Distro Showdown format) from a
    channel without touching any other channel or any human messages."""
    amount = max(1, min(amount, 200))

    def is_bot_message(m):
        return m.author.id == bot.user.id

    try:
        deleted = await ctx.channel.purge(limit=amount, check=is_bot_message)
    except discord.Forbidden:
        return await ctx.send("❌ I don't have permission to delete messages in this channel.")
    except Exception as e:
        return await ctx.send(f"❌ Error while undoing: {e}")

    if not deleted:
        return await ctx.send(
            f"ℹ️ No AdminPingu messages found to undo in {ctx.channel.mention} "
            f"(checked the last {amount} messages here)."
        )

    report_lines = []
    for m in reversed(deleted):  # oldest -> newest in the report
        if m.embeds and m.embeds[0].title:
            snippet = m.embeds[0].title
        elif m.content:
            snippet = m.content
        elif m.embeds and m.embeds[0].description:
            snippet = m.embeds[0].description
        else:
            snippet = "[attachment / other content]"
        snippet = snippet.replace("\n", " ")[:60]
        ts = m.created_at.strftime("%Y-%m-%d %H:%M UTC")
        report_lines.append(f"• `{ts}` — {snippet}")

    shown = report_lines[:25]
    remainder_note = f"\n…and {len(report_lines) - 25} more not shown." if len(report_lines) > 25 else ""

    embed = discord.Embed(
        title="↩️ Undo Complete",
        description=(
            f"Removed **{len(deleted)}** AdminPingu message(s) from {ctx.channel.mention} only "
            f"(no other channel was touched).\n\n**Removed messages:**\n"
            + "\n".join(shown) + remainder_note
        ),
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

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

@bot.hybrid_command(name="kernelnotes", description="Store the changelog for the next kernel release (admin).")
@commands.has_permissions(manage_guild=True)
async def kernelnotes(ctx, *, notes: str = ""):
    added, fixed, removed = [], [], []
    for raw in notes.splitlines():
        line = raw.strip()
        lower = line.lower()
        prefix = None
        if lower.startswith("added:"):
            prefix = "added"
        elif lower.startswith("fixed:"):
            prefix = "fixed"
        elif lower.startswith("removed:"):
            prefix = "removed"
        if prefix is None:
            continue
        item = line.split(":", 1)[1].strip()
        if not item:
            continue
        for part in item.split(";"):
            part = part.strip()
            if not part:
                continue
            if prefix == "added":
                added.append(part)
            elif prefix == "fixed":
                fixed.append(part)
            else:
                removed.append(part)
    if not (added or fixed or removed):
        return await ctx.send(
            "❌ No changelog entries found. Format:\n"
            "`?kernelnotes`\n"
            "`added: ...`\n`fixed: ...`\n`removed: ...`\n"
            "(separate multiple items on one line with `;`)",
            ephemeral=True
        )
    ok = await _kernel_set_changelog(added, fixed, removed)
    if ok:
        await ctx.send(
            f"✅ Changelog stored for the next kernel release.\n"
            f"➕ {len(added)} added | 🔧 {len(fixed)} fixed | 🗑️ {len(removed)} removed\n"
            f"Deploy the new code and the release banner posts automatically.",
            ephemeral=True
        )
    else:
        await ctx.send("❌ Could not save changelog.", ephemeral=True)

@bot.hybrid_command(name="kernelrelease", description="Force a kernel release announcement now (admin).")
@commands.has_permissions(manage_guild=True)
async def kernelrelease(ctx):
    pending = await _kernel_get_pending_changelog()
    announced = await _kernel_announce(pending or {})
    if announced:
        await ctx.send("🐧 Kernel release posted to the kernel channel.", ephemeral=True)
    else:
        await ctx.send("❌ Could not post the release (channel not found?).", ephemeral=True)

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
    await ctx.defer() if ctx.interaction else None
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
        if warn_count == 0:
            embed.add_field(
                name="ℹ️ Note",
                value="`user_warnings` is empty. This is expected if no one has been warned yet. "
                      "If you gave warnings and still see 0, make sure you're viewing the `AdminPinguDB` "
                      "database (not the default one) in your MongoDB client.",
                inline=False
            )
    except Exception as e:
        embed.add_field(name="Collection Error", value=f"`{e}`", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(
    name="emojiids",
    aliases=["eids"],
    description="DMs you the name and ID of every custom emoji in the server (mod)."
)
@commands.has_permissions(manage_messages=True)
async def emojiids(ctx):
    if ctx.interaction:
        await ctx.defer(ephemeral=True)
    emojis = sorted(ctx.guild.emojis, key=lambda e: e.name.lower())
    if not emojis:
        return await ctx.send("❌ This server has no custom emojis to list.", ephemeral=True)
    lines = [f"{emoji} `{emoji.name}` `{emoji.id}`" for emoji in emojis]
    header = f"**Total:** {len(emojis)} custom emojis in this server"
    messages = []
    current_chunk = header
    for line in lines:
        if len(current_chunk) + len(line) + 1 > 2000:
            messages.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += "\n" + line
    messages.append(current_chunk)
    try:
        for message in messages:
            await ctx.author.send(message)
    except discord.Forbidden:
        return await ctx.send(
            "⚠️ I couldn't send you the emoji list because your DMs are closed. "
            "Enable DMs from server members and try again.",
            ephemeral=True,
        )
    except Exception as e:
        logger.error(f"emojiids DM send error: {e}", exc_info=True)
        return await ctx.send("❌ Something went wrong while sending the emoji list.", ephemeral=True)
    await ctx.send(f"✅ Sent **{len(emojis)}** emoji IDs/names to your DMs.", ephemeral=True)

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

# ==========================================
# Stats: now font/color/background customizable, wide alias coverage
# ==========================================
@bot.hybrid_command(name="stats", aliases=["st", "s", "sta", "stat", "profile", "rank", "lvl"], description="Shows a user's level and XP info.")
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
    current_xp = user_data["total"]
    current_level = get_level_from_total_xp(current_xp)
    prev_level_xp = get_xp_requirement(current_level)
    next_level_xp = get_xp_requirement(current_level + 1)

    custom = await get_user_customization(member.id)
    file = await render_stats_card(member, current_xp, current_level, next_level_xp, prev_level_xp, custom)
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

@bot.hybrid_command(name="pythontip", aliases=["pytip", "ptip"], description="Shows a random Python tip.")
async def pythontip(ctx):
    tip = random.choice(PYTHON_TIPS)
    embed = discord.Embed(title="🐍 Python Tip", description=tip, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.hybrid_command(name="tea", aliases=["brew"], description="Serves a cup of tea.")
async def tea(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"🍵 Hey {member.mention}, here is a freshly brewed cup of hot tea for you. Enjoy!")

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

@bot.hybrid_command(name="neofetch", aliases=["nf", "sysinfo", "neo"], description="Shows user and OS information in a neofetch style.")
async def neofetch(ctx):

    TUX_ASCII = [
        r"        .--.         ",
        r"       |o_o |        ",
        r"       |:_/ |        ",
        r"      //   \ \       ",
        r"     (|     | )      ",
        r"    /'\_   _/`\     ",
        r"    \___)=(___/     ",
    ]

    ANDROID_ASCII = [
        "            ::                ::            ",
        "              ::  :======:  ..              ",
        "             :================:             ",
        "           :====================:           ",
        "         :===:   :========:   :===:         ",
        "        :======::==========::======:        ",
        "       .*==========================:        ",
        "       :============================:       ",
        " :=:                                    :=: ",
        "=====: :============================: :=====",
        "=====: :============================: :=====",
        "=====: :============================: :=====",
        "=====: :============================: :=====",
        "=====: :============================: :=====",
        "=====: :============================: :=====",
        "=====: :============================: :=====",
        "=====: :============================: :=====",
        "=====: :============================: :=====",
        ":====: :============================: :====:",
        "       :============================:       ",
        "       :============================:       ",
        "       :============================:       ",
        "       :============================:       ",
        "            :======:    :======:            ",
        "            :======:    :======:            ",
        "            :======:    :======:            ",
        "            :======:    :======:            ",
        "            :======:    :======:            ",
        "             :====:      :====:             ",
    ]

    IOS_ASCII = [
        "                            ...             ",
        "                        ::    ..            ",
        "                             ...            ",
        "                     :: .......             ",
        "                     .........              ",
        "                    ........                ",
        "                    .....                   ",
        "      .............       ...........::     ",
        "   .:....................................   ",
        "  ......................................... ",
        ".........................................   ",
        ".......................................     ",
        "......................................      ",
        ".......................................     ",
        "......................................      ",
        "......................................      ",
        ".......................................     ",
        ".......................................     ",
        "........................................    ",
        "........................................:.  ",
        "........................................... ",
        "............................................",
        " ...........................................",
        "  .......................................:. ",
        "   ......................................   ",
        "    ::..................................    ",
        "      .................................     ",
        "        ............:. .:..........:::.     ",
        "           .....             .:::.          ",
    ]

    ALMA_ASCII = [
        r"       /\/\           ",
        r"      / /  \          ",
        r"     / / /\ \         ",
        r"    /_/_/  \_\        ",
        r"                      ",
        r"                      ",
        r"                      "
    ]

    ROCKY_ASCII = [
        r"      .---.           ",
        r"     /   / \          ",
        r"    /   /   \         ",
        r"   /   /_____\        ",
        r"  /_________/         ",
        r"                      ",
        r"                      "
    ]

    CENTOS_ASCII = [
        r"      _____           ",
        r"     / ___/           ",
        r"    / /__             ",
        r"   / ___/             ",
        r"  /_/                 ",
        r"                      ",
        r"                      "
    ]

    LUBUNTU_ASCII = [
        r"      /\              ",
        r"     /  \             ",
        r"    / /\ \            ",
        r"   / /  \ \           ",
        r"  /_/    \_\          ",
        r"                      ",
        r"                      "
    ]

    BSD_ASCII = [
        r"       ##      ##     ",
        r"     #############    ",
        r"     ##########       ",
        r" #############        ",
        r"     ########         ",
        r"       #######        ",
        r"       ###########    "
    ]

    GENTOO_ASCII = [
        r"        .==...:==.            ",
        r"    .=.      ...::==.        ",
        r"  .=         ...::::--.      ",
        r" +.         ..:=-:::----..   ",
        r".=.       .:====*#::-----:.. ",
        r".=--       .+*###:::-----=... ",
        r" .==:::..    ...:::------==.= ",
        r"   .:===..  ....:::-----==. = ",
        r"     ...   ....:::------. .=. ",
        r"   ..     ....::::----...++.  ",
        r"  .     .....::::---. .++..   ",
        r" .    .....:::::-. .+++.      ",
        r"+ .......:::::. .+++..        ",
        r"+.....::::. ..****.           ",
        r".+: . ...*****=.              ",
        r" ..*******:.                  "
    ]

    FEDORA_ASCII = [
        r"               .+==========+.              ",
        r"          .====================.          ",
        r"        ==========================        ",
        r"      ==============================      ",
        r"    ==================================    ",
        r"   ==================        -=========   ",
        r"  =================-           +========  ",
        r" ==================   .=====    ========= ",
        r".==================   =======   =========.  ",
        r"+==================   =======. -=========+  ",
        r"===================   ====================  ",
        r"============     ==       :===============  ",
        r"=========        ==        ===============  ",
        r"=======-    =======   ===================+  ",
        r"=======   -========   ===================.  ",
        r"=======   =========   ==================+   ",
        r"======+   :=======.   ==================    ",
        r"=======-    ====-    +=================     ",
        r"=========           ==================      ",
        r"============.   .+==================        ",
        r"==================================          ",
        r"-==============================.            ",
        r"  +=======================+.               "
    ]

    ARCH_ASCII = [
        "                     --",
        "                     vv",
        "                    xvvr",
        "                   /cnnc/",
        "                  1znuunz1",
        "                 -Uuuuuunz[",
        "                  _xcvuuuuz-",
        "               +u(~>}juuuuuc~",
        "              ~cvczuffuuuuuuc~",
        "             <cuuunuvvuuuuuuuc~",
        "            ~cuuuuuunnunuuuuuuc~",
        "           _cuuuuuuczcvccuuuuuuc_",
        "          ]zuuuuuuct+lI>1vvuuuuuz]",
        "         {zuuuuuuc?      Ixvuuuuuz{",
        "        |znuuuuuc)        icuuuuunY/",
        "       fcnuuuuunc!         jvuuux\\1|)",
        "     IncnunnuuvuX<         xcuuuunj)-I",
        "    +vvuvczzcvnrr]        ljrnvczzzXcx1;",
        "   1Yzcnf(]~!                  !~](fnzYX1",
        " ;jn)-l                              l_(nj;",
        "I[i                                      i[I"
    ]
    UBUNTU_ASCII = [
        "                 I~?{(|t]   ~\\nczvj}",
        "             <1jvXYUUUCu   rUUYXXXYUX]",
        "          >\\cUUUJJUXcnvi  rJzXXXXXXzXC<",
        "        <rUUXYUv/]>       vYzXXXXXXXcC-",
        "      IxQJXYYt~           >XJYXXXXXUJt",
        "      ~[{tcjl               1nzYYXct+  !u<",
        "                               II    !|YUUi",
        "  }xcXYYct~                          ]CzzYv",
        "!cJYXXXXYUJt                          /UXzU{",
        "vYzXXXXXXXzC]                         >UzXYn",
        "xUzzXXXXXzzC_                         IYXXXc",
        " rJUYYYYUJU1                          <UzXYx",
        "  ~|xvcuj}I                           fUXzU}",
        "                                     }UXzYu",
        "     )|(fc(                   I;     uUzYYl",
        "     !XLYXUn>             </vXYYzn)   1Cc!",
        "       |UYzYUr-          (JUYXXXXYUY+  ]",
        "        ifYUXYUzj1+l    <CzzXXXXXXzYz",
        "          l)vYUUJJUYXn  !JXzXXXXXXzUu",
        "             ![/ncXYUL1  -XUYXXXYYUnI",
        "                  i+]{(;   }jvzzu/_"
    ]
    DEBIAN_ASCII = [
        "                +/zXUx1[1}|[i",
        "            +jLda*$$$$$$$$$$odCffx<",
        "         [cq#$$$$$kOJUYcczUQqa$$$$awC}",
        "       )m#$***dmz}            _fO*$o#$q|",
        "     <w$**#aL_                   _J#ok*$m<",
        "    ?oo*oJ}I                       ?d*hh$$1",
        "   (h**Y>                            O*oq/L",
        "  X$ow+              I}\\/\\)]>         p*hfII",
        " /$k$]             >YX/-!  Ii>        |$ob",
        "~aao1             jL~                 ioahi",
        "\\**J             jw                   !ah$t",
        "1*$f            !$+                   iaoO",
        "|**]            <$|                   ]**>",
        "|$o>             wh            !     )k$1",
        ")*#}             >dql     !_        \\$Q!",
        "<a*0            i~iuqxi          _nbq{",
        " 0#a!               }YpOu\\}[}/vUpmc_",
        " -$*Q+                ]/txuvut)-",
        "  n$a$wI",
        "   X$ko|",
        "    u$oh~",
        "     1k$b-",
        "      ;X$$z",
        "        ~J$b|!",
        "          ivo$Ci",
        "             ]XZJv)",
        "                <\\vx)[~I"
    ]
    MINT_ASCII = [
        "              I>_]{1))))1{]_>I",
        "          I+}(\\\\\\\\||||||||\\\\\\\\(}_I",
        "        _1\\\\\\||((||||||||||((||\\/\\)_",
        "      ]\\t/\\\\|||||||((((((||(((((((|\\\\]",
        "    _\\/{i>i~|||||(|\\\\\\\\\\\\||\\\\\\\\\\\\|((|\\\\_",
        "   }/(|[    |||||\\)]+<<+](([+<<~?)\\||((/{",
        "  1\\(|\\[    |||||<                i(|||(\\)",
        " [/(||\\[    |||\\l    ~~      <~I    (|||(\\[",
        "!\\(|||\\[    |||1    )//)    {/\\\\    [\\|||(\\!",
        "[\\||||\\[    |||1    )||(    1|(|    [\\(|||\\}",
        ")|||||\\[    |||1    )||(    1|(\\    [\\(||||(",
        "(|||||\\[    |||1    )||(    1|(\\    [\\(||||(",
        "}\\||||\\[    |||1    )||(    {|(|    [\\(||||}",
        "!\\(|||\\[    \\||)>ii<((|(<ii>)|(\\    [\\(||(\\i",
        " [\\(|||(    _\\\\/tttt\\\\\\\\tttt/\\\\-    )|||(\\[",
        "  )\\(|(\\[     <______________<     [\\||(\\)",
        "   1/(((\\)>                      i)\\|((/1",
        "    _\\\\|(|\\([_<iiiiiiiiiiiiii<_[(\\|(|\\\\-",
        "      [\\\\|(|\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\|(|\\\\[",
        "        -(\\\\|((((((((((((((((((|\\/(-",
        "          l_{|\\\\\\\\||||||||\\\\\\\\|{-l",
        "              l~-}1)(||()1}?~l"
    ]
    POP_ASCII = [
        "              !~_]}{11)1{}[_~!",
        "          i-}|\\\\\\||||()))((((()}-i",
        "       !?)\\\\1->I   I<](|)))))))(||)]!",
        "     !{|\\)_            -|))))))))))(|}!",
        "    [|)(?      -~       ~|)))))))))))(|[",
        "  l)())|>      ||(~      }()(|))(|())))()!",
        " I()))))(!     i|)|>     -|){I   i}))))))|I",
        " 1())))))|i     i)\\_     1)|!     !|)))))(1",
        "_|))))))))|>      I     {())      1)))))))(_",
        "1))))))))))|<         -(()([     1())))))))1",
        "))))))))))))|~     i)(|)))|-    )())))))))))",
        "1))))))))))))|_     {())))|~  !(())))))))))1",
        "_|))))))))))))|]     )))))|{;_|)))))))))))(_",
        " )())))))))))))|}    I()))}-}|))))))))))))1",
        " l|)))))))))))))()l   1)))   1)))))))))))|l",
        "  !(()))))||((((((|{]1|(((}_[(((|()))))((!",
        "    }|())(<                      -()))|}",
        "     i{|((l                      ~((|{i",
        "       !](\\()111111111111111111)|\\)]!",
        "          >?{(|||(((())((((|||({?>",
        "              i+-[{1))))1{[-+i"
    ]
    MANJARO_ASCII = [
        "{\\|||||||||||||||||||||||||\\   </|||||||||\\1",
        "1\\|\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\||\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\\\\\|||||||||||||||\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\\\|\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\/   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|/_                  </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t>                  </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\||||||||||\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\\\\\\\\\\\\\\\\\\\\\\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\||||||||||\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\|\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\|\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\|\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\|\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\|\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\|\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\|\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\|\\\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|\\\\\\\\\\\\\\|t<   \\||\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "1\\|\\\\\\\\\\\\\\|t<   \\||\\\\\\\\\\\\\\|\\   </|\\\\\\\\\\\\\\|\\1",
        "{\\|||||||||/<   \\||||||||||\\   </|||||||||\\1"
    ]
    OPENSUSE_ASCII = [
        "              l~?{)||||||){?~l",
        "          l-1||1[-~i!ll!i~-[1||1-l",
        "        -(/)-!                l_1\\(-",
        "      [\\\\?                        -|\\]",
        "    _||-   i[_+>!                   -\\|_",
        "   {|))]_~I]\\|||||()1[-~iI            1\\{",
        "  )|)))||||())))))))((//(1}[[_I        }\\1",
        " [|)))))))))))))))))()~   I  ~()i       1|[",
        "i|)))))))))))))))))(1  _1{?--  }/+      !||i",
        "}())))))))))))())))|> [\\(>  ?|  |\\i      1|}",
        "))))))))))))()1\\|()(_ i||\\||\\_ >|)(      ]|)",
        ")))))))))))))(> -1||\\_  i+_<  i)))\\}     ]|)",
        "}()))))))))))()    i-)(?<i!i_)/\\|)]i     1|}",
        "i|))))))))))))(|1?i    I<-][[?~i        i||i",
        " [|)))))))))))))(|\\|)}_i;      !_}\\i    1|[",
        "  )())))((((())))))))(|\\\\|||\\\\/|{_     }\\1",
        "   {|)))11111))(|||||(()1{}]_i        1\\{",
        "    _||1I                           -\\|_",
        "      ]||-                        -|\\]",
        "        -(/)-!                l_)\\(-",
        "          l-1||1[-~i!ll!i~-[1||1-l",
        "              l~?{)||||||){?~l"
    ]
    ELEMENTARY_ASCII = [
        "               !<+-?????--+<!",
        "           <-][[[[[[[[[[[[[[[[]-<",
        "        ~[{{}}}{1{}[]]]][}{11}}}{{[~",
        "      -111{{)1[+il!!iiiii!li+[1)1{111-",
        "    +1)111({~Il>?{}]--__?}{-<lI~{(111))+",
        "   }()))((> <[|/[ii~-??-<;>(|(}> >(()))(}",
        "  )()()|} !)||{  ?)|((((|(  )1(\\)! }|)()()",
        " }|(|(|[ -/)|? l||))))))1|{ [|))(/_ [|(|(|}",
        "i/(|||( +t)|[ !/()((()(()\\- )|((()t_ (|||(/i",
        "1\\|||/> /(||  \\((|||((((/{ _\\(||(|/> ~/|||\\1",
        "/\\\\\\|/ !t|\\{ i/(||||(|/\\~ ?/(|||/( l! /|\\\\\\/",
        "/\\\\\\\\t lt|\\( !t||||\\/\\? !(/|||//_ <r> t\\\\\\\\/",
        ")/\\\\\\f~ t\\|t> }f/t\\1~;!{t\\|/t/? ;1ft ~f\\\\\\t)",
        "ij\\//// <j/fr< ~{_ii-|jftf/1~ l}f/j+ ////\\ji",
        " 1j/t/f( <}_>i    ![){[?+iII~)ft/j_ )f/t/j1",
        "  /j/t/f\\  l[1\\f|[<lIl!>+[(fjffj|l \\f/t/j/",
        "   |rtttfj]l~)tjrxxrjjjrrrjjjt{> -jftttr|",
        "    ?rjtttrf[i!<?{(\\/tt/\\(1?<!>[frtttjr?",
        "      1jrftfrrt1?~<>>>>>><~?1trrftfrj1",
        "        ]/rrjfjrxxrjffffjrxxrjfjrr/]",
        "          !?(tjrjjjjjjjjjjjjjjt(?!",
        "              !+[1|/tttt/|1]+l"
    ]
    KALI_ASCII = [
        "        I!<~+?[{))1[+l",
        "        I!<+-??][{)/xzXY",
        "   !<~___~i!Ili+]1\\jnXYZ\\",
        "           ~[)|()}?+>!l tx>>!",
        "      I+[}?~I          ]0*CzcXYYJnt]",
        "     I                0a~       <(nQbu",
        "                     1$             jqJ_",
        "                     {$+              l\\",
        "                      c$r",
        "                       >YZLzxxxxrf|}i",
        "                           !i<~_[(xCZQj]]",
        "                                     irr!)1",
        "                                       }n i)",
        "                                        ?t",
        "                                         }",
        ""
    ]
    MX_ASCII = [
        "              ?uZkahbqwmmZOJn}",
        "           \\p$$mx[!        ~)vLQjI",
        "        <C$$w}                 ixdO<",
        "       C$$m!                      )$U",
        "     _$$$|                        c$$$<",
        "    ?$$$}       Lhi             /$$$dm$+",
        "   ;$$$c        1$$X          +d$$$n  *$",
        "   C$$$           x$$)       U$$$Ol   )$X",
        "   $$$h       +bY   m$bi   \\$$$o}     i$$",
        "  !$$$a      J$$$$(  ]$$v_d$$$u       <$$I",
        "   $$$$i   t$$$$$$$q>  X$$$$0i        j$$",
        "   p$$$Z _k$$$$$$$$$$v(o$$$$!   ]p)   $$m",
        "   ]$$$$d$$$$$$$$$$$$$$$$j[$$z!L$$$Z<d$$_",
        "    x$$$$$$$$$$$$$$$$$$$ol  n$$$$$$$$$$f",
        "    -$$$$$$$$$$$$$$$$$$$$$c_m$$$$$$$$$$]",
        "  iZ$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$q>",
        "  1x\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\|r)"
    ]
    ARTIX_ASCII = [
        "                     ??",
        "                    ~xx~",
        "                   <nttx~",
        "                  inj\\/fx>",
        "                 !xxt(\\/fxi",
        "                lxrr|)|\\/fx!",
        "                rrrj}{(|\\/frI",
        "              Iuvnnuj(1)|\\/fj;",
        "               _|nXYXcx/)(\\/jj",
        "                  i}jzUUvf||/jf",
        "            >         -\\cJUn/\\ff",
        "           tnj\\{_l       >)uYzxj/",
        "          /xffffjrj\\}~       ]fucj",
        "         \\xfft/\\||\\fxunf(?>     i1)",
        "        |xfftt/\\\\|())(/jxnnr/1+",
        "       (nffft/\\|||(){}})jxxnvzXzn(i",
        "      )nffft//\\|()11(tnczXXcx|]>     l",
        "     1nffft//|()(/xcYUXut}<       <{/x1",
        "    {nfjft\\||/xcYUzr)_I        _(jxt\\/x{",
        "   }nfft/fxvXXu/]!         l{rczvu\\{1|/x}",
        "  ]njrnvcuf1~               l~](jvXXuj/\\r]",
        " ]cxrt1_I                         l_)fnuxv[",
        "~|-!                                   I+[/+"
    ]
    CACHYOS_ASCII = [
        "         |vnnxrrrrrrrrrrrrrrru-",
        "        [txjtrxnnxxrrxxxxxxxn~      _<",
        "       1)/xr/1)\\tjrxrrrrrjxrl       ~>",
        "     l))1/xrxf((|txuuuuunuf",
        "    >()11/xrru1>+_+++++++_",
        "   +(11)|xxru]                 i?]~",
        "  ?((\\frrcun+                 !(11|_",
        " )jjxnnxrcx!                   I>>!",
        "[j/t///fjc?",
        " >(1(\\fjrrx_                          }(||}I",
        "  <vunnxrrru[                        [1}}{)1",
        "   !xuxnnnxju(                        ~+__~;",
        "     tnjrxx((t|??_~<<<<~<<<<<<<<<<~~",
        "      |urxr)1|xuuuxjt|(((((((((((||!",
        "       {uxr1\\xrrrrrxxrf/(1111111){",
        "        -nr/xxxxxxxrrxxxxjf\\()1([",
        "         ~nrrrrrrrrrrrjjjrrrjt/]"
    ]
    CHIMERA_ASCII = [
        "jjjjjjjjjjjjjjjjjj   fYcU[",
        "jjjjjjjjjjjjjjjjjj   fYcU[",
        "jjjjjjjjjjjjjjjjjr   fYcU[",
        "jjjjjjjjjjjjjrxxj\\   fYcU[",
        "jjjjjjjjjjjxx\\?!     fYcU[",
        "jjjjjjjjjrx1l    l_})vXcU[",
        "jjjjjjjjx/l   i\\vYJLLJUUL}",
        "jjjjjjjx|    fUYUYn\\}]??[l",
        "jjjjjjrt   !XUzYj>",
        "ffffffr>   vYcU|             |ftt///////////",
        "          ~UzXc              cUYYCCCCCCCCCCC",
        "          ~UzXc              cXcY1<+~<<<<<<<",
        "{1111{)l   vYcU|            |YcYc",
        "111111)}   !XUzYj>        >jYzUX!   runuuuuu",
        "1111111)]    fUYUYn\\}??}\\nYUYUf    tcuvuuuvu",
        "11111111)}    i\\vYJLLLLLLJYv\\>   !rcnuuuuuuu",
        "111111111))-     l_}(||)}_l    !|cvuuuuuuuuu",
        "11111111111))[~             i}jccuuuuuuuuuuu",
        "1111111111111)()1[?_    1\\juczvuuuuuuuuuuuuu",
        "11111111111111111)))    ccvuunuuuuuuuuuuuuuu",
        "11111111111111111111    nuuuuuuuuuuuuuuuuuuu",
        "11111111111111111111    uuuuuuuuuuuuuuuuuuuu"
    ]
    NIXOS_ASCII = [
        "          1cvx      !}[[[I    ?[[>",
        "          \\Yvcul     !{}[}!  ]}[{+",
        "           ?cvcc~      ?}[}+[}[{>",
        "       -___~fcuvc}+___++_}[}[[}l",
        "     <zJUUUJXzzzcUUUUUJY1-{[[}l     ~n!",
        "     ((111){||||\\)11111)|i<{[[?    ?Xcz_",
        "            ---]l          >{[}}  1Xvcc~",
        "          !{}}{!            l}}[~\\Xvcj",
        " !iii!ii!~}[}[               ;?~fXuvc(?}[[]",
        "+)111)1{{}[}?I                !nzuzXXUJUUUC\\",
        " !iii!~[[[}+[u~              <vcvX(][]]]][?",
        "      -}[{~)XcX?            ?XccX-",
        "    I}}[{< ~ccvX1          [cnnni",
        "    l}}}!   lxcvX\\I~~<<<<<~[-??_i~<<<~~",
        "      ];     _XvuXj_})11111[[}[})1111}",
        "            -cvvzuzx~ lIIIi}[[}- IIIl",
        "           }Xvcv\\Xvcvi      }}[[!",
        "          \\Xvcul ?zvcX?      ]}[{+",
        "          {vvx    +vvvX[      ?[[>"
    ]
    WIN11_ASCII = [
        "I-]]??]]]]]]][[[[[[}[  }{1111))(((|||\\\\//t\\~",
        "]]???]]]]]]]][[[[[[}[  }11111))((||||\\\\//tfj",
        "???]]]]]]]]]][[[[[}}[  }11111))((|||\\\\///ttf",
        "]]]]]]]]]]]][[[[[}}}[  }1111)))((|||\\\\///tff",
        "]]]]]]]]]][[[[[[}}}{[  }1111))((|||\\\\\\//ttff",
        "]]]]]]]][[[[[[[}}}}{}  {111)))((|||\\\\///tfff",
        "]]]][[[[[[[[[[}}}}{{}  {)1)))((|||\\\\///ttffj",
        "[[[[[[[[[[[}}}}}{{{1}  {))))((|||\\\\\\//ttffjj",
        "[[[[[[[[[}}}}}}{{{{1}  {)))(((|||\\\\///ttffjj",
        "{{{{{{{11111111))))(1  )\\|\\\\\\///ttffjjjrxxnn",
        "~~+~~+++++++++++____+  +___-----????]]][[[[}",
        "+++_______________--_  _------?????]][[[[}}}",
        "))))))))))))(((((|||(  |////ttfffjjrrxxxnnuu",
        "1111111111111)))))(()  )||\\\\\\///ttfffjjjrrxx",
        "1111111))))))(((((||(  (\\\\////ttfffjjjrrxnnn",
        "))))))))((((((|||||\\|  |////ttfffjjjrrxxnnuu",
        "((((((((||||||||\\\\\\\\|  |t/ttfffjjjrrxxxnnuuv",
        "||||||||||||\\\\\\\\\\///\\  \\ftfffjjjrrxxxnnuuvvv",
        "\\||\\\\\\\\\\\\\\\\\\\\//////t/  /ffjjjjrrrxxnnuuvvvcc",
        "\\\\\\\\\\///////////tttf/  tjjjjrrxxxnnuuvvvcccz",
        "tt//////ttttttfffffjf  frrrrxxnnnuuvvvccczXY",
        ">|tttttttffffffffjjjf  fxxxxnnnuuvvvcczzzXv]"
    ]
    WIN10_ASCII = [
        "                                  I!><+-?[}}",
        "                   I!i<~_-?]}}{1))))))))))){",
        "    I!i<+_?][}{1([ |((((())))11111111111111{",
        "})))((((()))))11)? )11111111111111111111111{",
        "})11111111111111)? )11111111111111111111111{",
        "})11111111111111)? )11111111111111111111111{",
        "})11111111111111)? )11111111111111111111111{",
        "}111111111111111)? )11111111111111111111111}",
        "})))))))))))))))(] |))))))))))))))))))))))(1",
        "-[]]]]]]]]]]]]]][+ [?]?????????????????????-",
        "-[]]]]]]]]]]]]]?]+ ]????????????????????--?-",
        "})))))))))))))))(] |))))))))))))))))))))))(1",
        "}111111111111111)? )11111111111111111111111}",
        "})11111111111111)? )11111111111111111111111{",
        "})11111111111111)? )11111111111111111111111{",
        "})11111111111111)? )11111111111111111111111{",
        "})))((((()))))11)? )11111111111111111111111{",
        "    l!><+_?][}{1(] |((((()))))1111111111111{",
        "                   Ili<~_-?][}{11)))))))))){",
        "                                  I!i<+-?[}}"
    ]
    WINDOWS_ASCII = [
        "             I-)trnuuxrj/|1[+!",
        "          ?jXUYcnrjttt//tttfff/)?!",
        "       ~n00Ynftttffffffffffffffjrj\\];",
        "     ~YqQcxrxnnnnnnnnnnnnnnnnnnnnnnxf{I",
        "    ndOzvczzzzXXXXzccczXzzzzzzzzzzzzcnt?",
        "  I0dCYJJJJJJUUYXcvunxrxUJJCJJJJJJJJJJcj(",
        "  mqQQ000000Cccunxrft/|xOUzJCLLLLLCUC0OJj\\",
        " UpZwwwwwmwmcnxrjf/\\|))OmxxvXYYYYYYYmwmqLf1",
        "1pmbddddddkU\\\\|)1{}}{-coc(jxuzYYYYXZbdddkXt<",
        "JmbahhhhhadrncXYYzx\\_{aw{)\\trncYYXChhhhhaqt)",
        "ZOhahhhhhadmZQJYXYLwmm$r<-[1|/jncXqahhhhakj/",
        "0QhahhhhadJUznf\\1[-~r$mQLzunucYCLwahhhhhakj/",
        "zLdahhhhaQYJJUzuj/(]0o_l[|jxxxj/|dahhhhhoqt)",
        "]C0ahhhaqUJUUJUXux\\v$n !l!i<+-[[X*hhhhhh*Y/<",
        " rYZbdddCUUUUUUUYvnqw<>+-]}1)|(/pdddddpbOf1",
        "  uc0wm0JLQQ00QLCYCq\\<?[}1((|(1YwZmmmmwQj\\",
        "   fuYQQQQ0QQQ0QQQQC|{{1))))(|jQQQQQQQYj(",
        "    [fuXUUUUUUUUUUUUJYcunnnucXUUUUUUXnt?",
        "     ;}fnvvccccccccccczzzzzzzccccvvnf{I",
        "       ;]\\rxxxxxxxxxxxxxxxxrrxxxxr\\];",
        "          !?)/fjffftttttffffjf/)?!",
        "              !+[1(\\////\\(1[+!"
    ]
    ALPINE_ASCII = [
        "          /mOOOOOOOOOOOOOOOOOOOOm\\",
        "         jwOOOOOOOOOOOOOOOOOOOOOOwj",
        "        cw0OOOOOOOOOOOOOOOOOOOOOO0wc",
        "       Jw0OOOOOO00O0OOOOOOOOOOOOOO0wJ",
        "     >0m0OOOOOO0ZwZwO0OOO0ZO0OOOOOO0m0>",
        "    ?ZZ0OOOO00ZwJ]lrZw00ZwCLqO0OOOOO0ZZ?",
        "   )wO0OOO00ZwU[    !xmwJ1  \\0wO0OOOO0Ow)",
        "  fw0OOO00mwU]        >/I     |0wO0OOOO0wf",
        " nq0OO00mwY?    ~cL)    I!~i    |0wO0OOO0qn",
        "vpQOOOmqY?    -/OmOwL)    <xj!    \\0qZOOOQpv",
        " nq0OOv~    ~1i CO00OwL)    !/\\     {JOO0qu",
        "  fw0Ot<!l_cm\\!>QOOOO0OwL1!l!}0Zt>l!_cZ0wj",
        "   )wOmqZZwmOwwZOOOOOOO0ZwZZwqOOwmOmqZOw)",
        "    ?ZO0OO00O00OOOOOOOOOO0OO00OO00OOQOm?",
        "     >0m0OOOOOOOOOOOOOOOOOOOOOOOOOO0m0>",
        "       Jw0OOOOOOOOOOOOOOOOOOOOOOOO0wJ",
        "        zw0OOOOOOOOOOOOOOOOOOOOOO0wz",
        "         jwOOOOOOOOOOOOOOOOOOOOOOwr",
        "          /m0OOOOOOOOOOOOOOOOOOOm/"
    ]
    ENDEAVOUROS_ASCII = [
        "                \"}MU[,",
        "                _WB$Bkc],",
        "               -a@W&%@@Mmx_",
        "              ?q@%8W%88%8*qU(;",
        "             [08%%%M8%%%%8MkwQr!",
        "            {LoB8%%WW%%%%%8&*qZZni",
        "           )Lq@8%%%WM8%%%%%8WWk0ZZxI",
        "          (LQB%%%%%&MW%%%%%%%MW*ZQmO\\",
        "         |QUWB%%%%%&MM8%%%%%%%MMMwQ0mJ~",
        "        \\QYh@8%%%%%8MMW%%%%%%%8MMWwQQOm/",
        "       tQYm@8%%%%%%8MMM8%%%%%%%8MMMZ00Qwz\"",
        "      fQYL%%%%%%%%%8MMM&%%%%%%%%WMWo000QmJ,",
        "     jQUU*B8%%%%%%%8MMMW%%%%%%%%8MM&wQ00QmX",
        "    xQUUd@8%%%%%%%%8MMMM%%%%%%%%%W#&pL000Qmt",
        "   nLUU0B%%%%%%%%%%8MMMM8%%%%%%8%&W8OCO0000Q",
        "  uLYUJW%8%%%%%%%%%&#MMM8%8%%%BB@8aOUC000QZC",
        ";zOLQCo$BBBBBBBBBBB8W&&&B@BB8&#adOUUUCQ0ZwUi",
        "-()||YMo#####M####*kbdpqdpqmZO0QQJUUJ0wOc?",
        "   \":QQQ0000000000JUUUUJQLQQQQ0O0LQLCz)l",
        "    XZQ000000000QCUUJJCOZZmmwmZLzj1+:",
        "   \\w0OOOZZZZZZ0LLLCJJLJXvr/1-i,",
        "  <OCCUYXcuxj\\){]-+>!I,",
    ]
    GARUDA_ASCII = [
        "                   -trjt\\){[?_++_l",
        "                I[txxxuvvvuxjfjf/|_",
        "              <1tfffrxncLwqwZUcunrr\\<",
        "            ?|ttfjxnvczXUCQnmbaZCzuux/{_",
        "          +|rxxuvczXYYYYUYYuuOmLXvuntur/\\<",
        "       ~1/jjfjxxnuvcXYYUUUUJUzcvvunxft/\\|\\}",
        "     <\\///tfjxnvvvvufjrrnunuvf\\//////ttfrxx1",
        "    !|\\\\tfjxnnnxjjjr){(|\\fffc+           \\/+",
        "   -\\\\/tffjf/\\\\/fffx\\)\\/ffrfu)           f?",
        " !1\\(||||()1)|/ttftx/(\\/frxxxf",
        " !1]11111{{1|\\\\\\f//xf|/tjrnvvx",
        "   _)1{{}}1(|||f/)/xj|tfrxnucU~",
        "  !_ ?{}}{)))|/f1)/rx|jjxnvvXvI",
        "      {}{1{1(\\f(}(/rx\\jxxuuXn",
        "      i)[})\\/ft}{)\\jn\\fnxvJ/",
        "       l  l-(/?]{(txvfjvXj1",
        "                 I+{j[_{/l"
    ]
    BLACKARCH_ASCII = [
        "                  rUOUn!",
        "                  i/*z[I",
        "                   _*/",
        "                   ]*r",
        "                   )*z",
        "                !trmhpuj-",
        "                 l!q$h{I",
        "                   k$#?",
        "                  Y$*$wI",
        "                 x$#$#$0",
        "                \\$*$$$*$C",
        "                d$$$$$$*$X",
        "              {U\\vp#$$$$*$X",
        "             }$$$pOh$$$$$*$c",
        "            )$$*$$$$$$$$$$*$Y",
        "           1$$#$$$#$$$$$$$$*$U",
        "          \\$$$$$$#$$$$$#$$$$*$C",
        "         f$#$$$$$$bd*dq$$$$$$*$0",
        "        u$*$$$$$$zIf#X \\*$$$$$*$O",
        "       Y$*$$$$#$Y; \\$X  )$*$$$$*$d!",
        "      C$*$$$$#$*-  \\#v   w$*$$#bmpZ-",
        "     O$*$##$$$$$?  1$u   q$$$$**k0z1",
        "   Iw$*$$$$$ap0Y_  1#x   xCmh$$$$$$dY+",
        "  >h$$$amX/-!      }*f       _)u0k$$$${  <>",
        " 1$o0u1<           -*f           I_tCh$f  !",
        "~n1<               -o\\                -c}",
        "                   Ip}",
        "                    |!"
    ]
    ZORIN_ASCII = [
        "          ?fttttttttttttttttttttf_",
        "         1nrrrrrrrrrrrrrrrrrrrrrrn}",
        "        <}]]]]]]]]]]]]]]]]]]]]]]]]}>",
        "",
        "",
        "",
        "   -fffffffffffffftfjrf)+           ~)tf~",
        "  }rfffffffffffffjxj(+           +)jrjffr?",
        " )xfffffffffffjrf)~           _(jrjffffffx}",
        ")xtffffffffjrf)~           _(jrjffffffffftn[",
        " {xfffffrrf1~           _(jrjftffffffffffx}",
        "  [xjrrf1<          I?\\xnxjjjjjjjjjjjjjjr-",
        "   +({<           i[(|()1)))))))))))))1(~",
        "",
        "",
        "",
        "        }t|\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\|t?",
        "         }xjjjjjjjjjjjjjjjjjjjjjjx?",
        "          ?f///tttttttttttttttt/f~"
    ]
    DEEPIN_ASCII = [
        "               i+-][}}}}[}[-~!",
        "          l+]{11111{{{{11?ii~?[[-!",
        "       ;?1]]1{{{{{{{}11_        >]}-I",
        "     I})_  ~1{{{{{{{)?            <1)[l",
        "    ?(_    ?1{{{{{{1>        ;<-}1{}}{1-",
        "   11      ?1{{{{{{;     i~-}{}}}{11)11){",
        "  1{       -1{{{{1    i?!l-?        l>_?11",
        " [)        <1}{{1i  !{]  +(~ i~         l)[",
        ">)_         1{{{}  Ii  i1)i  1 i>        -)>",
        "])l         >){{}  ]+-))_   )~ !)        l)?",
        "})           i111i  ~<    >(_  _(!        )[",
        "]1+            -1)_    I_11i  I11!       l)?",
        ">111]<           >?}{{{}-!   l{{1        _)i",
        " [1}1)1}?<I                I?1{)i        )[",
        "  1{}{{{1)11[?+>!I    I!~?}1111!        {1",
        "   {1}{{{{{{{11)))1111)11111{_        I1{",
        "    -)1{{{{{{}}}}}}}}{{111]<         _(-",
        "     I]11{{{{1)))))11}]+!          +)[I",
        "       I-{)1[+>ilI              <[1?",
        "          l+]]-<!         Ii+?[[_l",
        "              l~-][}}}}}}[]-<I"
    ]
    PARROT_ASCII = [
        "             ,!~-[{11))1{]-~!,`",
        "         ,>?)|\\//\\\\\\\\\\\\\\\\\\\\\\\\|1]>,",
        "      `>}\\//\\|||(||\\||||||||||\\//\\1<\"",
        "     <)/\\||||||\\t\\((((||||\\\\||||||\\/|-^",
        "   ;1/\\||||\\(j#B$WpLcrt|(((||||||||||/|<",
        "  i\\\\(||||||(c$kk$$$$$BMkXrf/||||||||||/[`",
        " !\\\\|\\||||||(xX)(rb$B@$$$$qUUXvxjt/\\|||(/{",
        "\"(\\|||||||||||(\\|((Z$@@B@@$dYUYXzcunrft/\\/?",
        "_\\||||||||||||\\||\\\\(0$$$$@$$oUzzcvuunxrjft/I",
        ")||||||||||||||||||\\(uU0&$@@$WUczvunxxrjftt]",
        ")|||||||||||||||||||\\((1C$@$@$@Qucvnxxrjftt{",
        "}|||||||||||||||||||||\\(z$@$$M*$wuuuxxrjftt}",
        ">\\|||||||||||||||||||||(x$@@$bcJhqvnxxrjftt+",
        " }/(||||||||||||||||||||tB$@$dXzvYznxxrjtf(`",
        " \")/|||||||||||||||||||||W&0@qzXcvuuxxrfffl",
        "  \"1/||||||||||||||||||\\(baXZOzzccuuxrjrf>",
        "   `-\\/|(||||||||||||||\\(QwUUYYzzcunxxn\\I",
        "     ;[\\/\\||||||||||||||(n0JUYXzcvuvvr_",
        "       :_)//\\\\||||||||||||jJJYXXXYv/_^",
        "          I+}(|\\/\\\\\\\\\\\\\\\\\\|tzJYu/?;",
        "             ^;>_]{1)((()1}?+_i^",
    ]
    NOBARA_ASCII = [
        "  <fYQ0QUr_   +1fuYUCJUJYXnt}~",
        " uwqwmZZmwmXz0ZmmZO0000Q000OOQCc\\<",
        "YdZZZZZOOOOmmO0000QQQQQQLLLLCCLQ00Y\\!",
        "wZmmZZZOOOO00O0000QQQQQQLLLLLCCCJJC0Ljl",
        "mmmmZZZOOOOOOO0000QQQLLLLLLLLLCCCCJJJQL|",
        "mmmmZZZOOOOOOO00QQ0OZZZO0QLCCLCCCCCCCJC0c",
        "mmmmZZZOOOOOOO0OmZJvf/tfuU0OLCLCCCCCCCCJ0Y",
        "mmmmZZZOOOOOO0mQ\\>        i|C0CLLLCCCCCLCOn",
        "mmmmmZZZZOOO0mn              rOLLCCCLLLLLLO?",
        "mmmmmZZZZOOOmu    <vCQQCn>    rOOmZO0LLLLL0c",
        "wmmmmmZZZZOOw<   imZ00Q0OO!     i?1fcLQQQQQJ",
        "wmmmmmZZZZZOZI   <wO0000OZ!     l+}/cQQQQQ0C",
        "wwmmmmmZZZZZZ;    _X0ZZ0z~     0ZmmmOQQQQQ0Q",
        "wwwmmmmmmZZZw>       !!       IOQQQQQ0000000",
        "wwwwmmmmmmZZmJi               lO000000000OO0",
        "mwwwwwmmmmmmZwwYj/|}<         lZO0OOOOOOOOO0",
        "mqwwwwwmmmmmmZZwqqqqwC{       lZOOOOOOOOOOOO",
        "mqwwwwwwwmmmmZZZZZOOOZdr      IZOOOOOOOOOOOO",
        "wqqwwwwwwwwmmqdqmZZwpwOmI     !mOZZZZZZZZZOO",
        "JkwwwwwwwmmqpX1>   i[uwqI      0wOZZZZZZOOpY",
        " cddpqqqqpdL~         !J!      >Lqwmmmmmqqc",
        "  -xLwwwOc{                      {c0mmZCx_"
    ]
    REDSTAR_ASCII = [
        "                            {YO",
        "                         _nQm0w_",
        "                      lfOwZ0QQOI",
        "                    -XOc1QmmmqJ",
        "                  -zU1   rxrjn-           l~",
        "     I~?})|/frxxcYO0XuzYYzzcccczcccczYUC0Lx+",
        "    zZmwmwpqmZqpJvxncXYYXzvunvzULQO00LUn}",
        "    QOL0wQnuOmX- i}|fjrucczzcnf\\||(|\\/(",
        "    <mwO|_f00/[v0~ I-|nruYXunvYCLLQCv)!",
        "     ~c~}LqY/cmZOQ[ +UZUj(jLOCXcvn)",
        "      +Yq0vcOm000Ow0mZ0OOU1 -||(]l",
        "     xmqLXQO0000000000000Oq",
        "   +LmOz <OmQ00000000000Qw|",
        "  \\wOQmj1t_uw0Q00000000QZY",
        " nwQ00QZmqL-10wO000000QZO",
        "CqOZZmmmZ0Lv  \\CmZ0000mLi",
        "/nvvnj/1-!      ]nQOO0f"
    ]
    VOID_ASCII = [
        "                  ░░░░░░░░",
        "             ░░░░░░░░░░░░░░░░░░",
        "              ░░░░░░    ░░░░░░░░░░",
        "                             ░░░░░░░",
        "      ░█░                      ░░░░░░",
        "     ░█░██░                      ░░░░░",
        "     █░░░█░         ░░            ░░░░░",
        "░█████░░░░  ░░░░█████████░ ░███░░██████████░",
        " ██████░██░░░█████░░░████░░████░████░░░█████",
        "  ░██████░  ░████░░░██████████░████░░░█████",
        "   ░████░░   ░████████░░░████ ██████████░░",
        "     █░░░█░                       ░░░░░",
        "     ░█░░░█░                      ░░░░",
        "      ░██░░█░░                      ░",
        "        ░██░░█░░░          ░░",
        "         ░░███░███░░░░░░░░████░",
        "            ░░░██████████████░░░",
        "                ░░░░░░░░░░░░",
    ]
    SLACKWARE_ASCII = [
        "             ~?)\\tfjjjjfft/|{?i",
        "         ~1/jf/\\|)1{}}}}{1)(|/jf/}i",
        "      i(xxt|11)1[?-?][[]??+_?-?1|fnr}",
        "    !fvj|((|\\(?-1trjjffjjrjfnn-[|((/nv(",
        "   )Xr\\\\////(_(XUx)111111{\\YUL)-////\\/vz_",
        "  rXttjfffff[}ZQXi[/fjjrjf}(cc)1ffffff/rC)",
        " fUjxxxxxxxx\\]UqpYt|))111))11\\jxxxxxxxxrrQ[",
        "?Lnnnnnnnnnnuj|nUZpppqqwwm0Un\\)junnnnnnnxcCI",
        "vCXzzcccvvvvnt/(/ffjxnuczYQ*$*J}jcccczzXYYL\\",
        "UJJJJJUUUUUv1Lkw)tYUYXXzzv\\_h$$c(UUUJJJJJJCv",
        "YJUJJJJJYYzv[$$$at\\fxnnnxf|x$$$txJJJJJJJJULv",
        "rLUJJJJUjb}c[p$$$$$dm000md$$$OjxUUUJJJJJJU0\\",
        ">LCUJJJUfa{YxvdduxLZqddpqZCcuvULCCCJJJJJUQU!",
        " }OCUUJJt*[xcnjjnuxrjfffjrxvczcvvvvYJJUUQQ?",
        "  }Q0JUJtqYzXXYYXXXYYYYYYYXXXXXXXXYnYUCOC]",
        "   ~cO0CYcYYYYYYYYYYYYYYYYYYYYYYYYYYC00n>",
        "     [c0O0CJUUJJJJJJJJJJJJJJJJUJJL0OQu?",
        "       _tY0O0QLCJJJUUUUUJJJCCL0OOQX/~",
        "          ~)rzJQ000000000000LJzj1~",
        "              l+[)\\fjrrjf\\)]~!"
    ]
    FREEBSD_ASCII = [
        "n#&*pU/< ^   \"\" ^!_{|tft\\1?i^ \"  `\"^`~/Uwkbn",
        "*@%B@@@@&CI !(Xq*8B@@@@@@@B%8aC? i/QoB@@@B@B",
        "|$8%8B$on|vdB$$@BB%%%%%%%%%Bz1cQkB$$B%%%%8$f",
        "`U$&$Wt?YW$@%88%%%%%%%%%%%B8 (BB@%8%%%%%8$C",
        "  0$L>vB$B8%%%%%%%%%%%%%%%%@J?B@8%%%%%%8$O",
        "  `[~o$%8%%%%%%%%%%%%%%%%%%%$Q)d@@B%88%$X`",
        "  ^~@@8%%%%%%%%%%%%%%%%%%%%%8$#unw&@$$@fur^",
        "  iBB8%%%%%%%%%%%%%%%%%%%%%%%8B$oYffxr;`&$[^",
        "  w@8%%%%%%%%%%%%%%%%%%%%%%%%%%%@$%kJrfZ%Bo`",
        "^<@%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%@$$$@%8@\\",
        "\"\\$8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%88%%%@C",
        ",f$8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%@O",
        "\"{$8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%@z",
        " \"WB%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%B+",
        " ^r$8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%8$L^",
        "   Z$8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%8@o^",
        "    Z$%8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%8$h:",
        "     nB@%8%%%%%%%%%%%%%%%%%%%%%%%%%%8@$C",
        "     \">Z@$B88%%%%%%%%%%%%%%%%%%%%8B@$b]^",
        "      ` +C&$$@B%%%%%%%%%%%%%%%%B@$%Z[ ^",
        "        ^^,)Ca%@@@@BB%%%BB@@@@B*0/I`^",
        "           \"^ >(v0do&%BB&*kZz\\+^^\"",
    ]
    GHOSTBSD_ASCII = [
        "          ^ ,+|vLwbaaohbwCv(~,",
        "       ^ <j0a&%B%88&&&&&8%%%&aQti",
        "     ^\"/q8@B&WMMMWWWWWWW&&&&&8@$8m(^ ^",
        "     fo@%WMMWWWWWWWW&8&MokbddddkM%Bh|  ,",
        "  `<d@&MMWWWWWWWW&8ModwwwqbhoopwkWM8@wl :",
        " `{8%MWWWWWWWWW8&opmmwb*&%8Wodpd*WWWMBM_ ;",
        "`?BWMWWWWWWWW8WkwZmd*&Wdbkdpqbo&&WWWWM&&< ;",
        ",o8MWWWWWWW&&kZOmkW8&&#dpqwqo8&WWWWWWWM%k ^:",
        "uBMWWWWWWW&#mOZkW8WMW&&MbwqkMWWWWWWWWWWM@|`I",
        "d8WWWWWWW8aOOwW&MW&8Mhpmmd#8WWWWWWWWWWWMBL`:",
        "*WWWWWWW&o0Od&&&8&odwmmq*&&WWWWWWWWWWWWM%q ,",
        "b8WWWWWW8m0m8&Mopmmwwwdbb*WWWWWWWWWWWWWMBQ :",
        "vBMWWWWW&w0OmmZOwbdwZwqdoWWWWWWWWWWWWWWM@\\`l",
        ":*&MWWWW&WbqwpaMhmZmqkM8&WWWWWWWWWWWWWM8a ^I",
        "`}@WMWWWWW&8B8omOmb*&8&WWWWWWWWWWWWWWM&%+ !^",
        "``(%8MWWW&8#dZOZkW8&WWWWWWWWWWWWWWWWM%&] l\"",
        "  `_h@&MM#qOOObW8WWWWWWWWWWWWWWWWMM&@di l\"",
        "  ` ^x#@%h0ZdM8WWWWWWWWWWWWWWWMMW8@*t  l^",
        "      ;jb%$B%WMMMMWWWWWMMMMMM&%@8p/, ;:",
        "        `_uw#%@@B%%8888%%B@@%*mx+  ,:",
        "            I?\\vCmpbkkbpZCv\\-;  `,\"",
        "                  `\"\"\"\"^     ^\"^",
    ]
    OPENBSD_ASCII = [
        "               \" !\" ^! I{ul     ^",
        "               1 Y|I[qj/QO/r0 ^^(",
        "          \";I\"\"C0vOxQwbOnjCo%0cY0,\"",
        "         :+^rtuQq0\\Utt|/Zt|fLzCzm&n  :!",
        "       \"  00tdjnf11xX))\\x/f|/Zntzd0LUJ<",
        "       _U1x$hj)fX\\)n{{z/}1v|1fu\\\\Yvv$}",
        "        <*x1nf{|c)1f{t{11}(({|u/XnLcwZ\"",
        " \"   \",Cvqu(/Jf{n/}{1{{|{}){(|}bQ<XaO**:",
        "~X0v/~,iaojtr1v|}(}1)}{1}{1{11{xv(nLOW*/\"",
        ":ivkUcz(pxnt1)(11{}1[)[{{{{1}1)(|/LmvJY&f;",
        "  ,+pctx\\tn/rz11(}tf\\j/1{}){){{/\\1apUUCQM/\"\"",
        "   \"Ibv(ck\\xX)|z{xQ{)uJ)}(}()(f1/zmU(tLbWLJ{",
        "    :|MJxzdqt1zjupYuzt1)t}{n(|f(jx/*cxdQj/X}",
        "     ?J}\"/wq(xu{/rjL1}u(1|x1)tUjrOJXh%x\"\" ,^",
        "      \"\"` rkrmCxfX)}ffr1|/j(xUjjnJC8Z>\"",
        "         !\\,-OjLvUJxxJj)zwu/vZvXoMXfc]",
        "          ^ ;^!wpn%YJXobmJzakJ*w_(Q  ,",
        "               \\ ^(;J$~#|O*-*|]O , `",
        "               ^  ^^??Il\"~zlI,: :",
    ]
    DRAGONFLY_ASCII = [
        "      ``      \"^:1c0qdbbbbdwCr_ ,`      ``",
        "     ,<!, `^\" {0bqLznrftfjxuYOddzi\"^^ `;>i",
        "    !p~[|/\\])ooUj///t//Zc\\/t///xO&0-)\\\\(~fL^",
        "     fr ; :<|YzXcxt\\\\zQ@aCx\\/fnzzXv]!`\";lU<",
        "     ^?c(:,:;: !{xXYnd****CuUzt-:`;;: <rn,^",
        "      ^ ~uQ)+I ^:: !}nhbhw|-,^:, \"!?r0(I^",
        "    ``  Ij$LLCJYzur/\\uzamvr|fncXUJLCb$^^  ^",
        "    <}(\\|vYft/tfrxxrrYU*qYcjxxrjf//txJf||)?l",
        "  ^_d?\" `,;,\",:;:, ;-jZwwL1<^^:;:,\"\":;\"` ;rq",
        "    I)\\)[_+<l<]1tnzXvnMd*wrzXcr\\}-ii~+-}|/]`",
        "     ^ :>_+C$Zcunjt/\\\\hhMJ|//fruvXo@\\++!\" ^",
        "        ``^`|apvt//tt/hd*J\\t///jJaw!\"``",
        "            \"^jpkmUurtkk#UtxcLph0[``",
        "              \" <tUZqw&b#aww0c1:^^",
        "                `\"^ \"\"Qa#)\"` \"\"",
        "                     :v*#!\"",
        "                     \"jMoI",
        "^                    \"|Wh\"",
        "],                   ^]&d",
        "~\"                   `<%m",
        "`                     :BL^",
        "                       %z\"",
        "                      ^q|\"",
    ]
    NETBSD_ASCII = [
        "           \"\"\"\"^\"\"\"\"^  ,<{rJmpqOYxt)]~;",
        "        ftQu/)}[})/xX0poW8Mb0Xnf\\1->;",
        "        lccB@BBBBBBBB8&W&8&*kmJn\\}-+>I",
        "        ^!c\\#&####MM&%B8o0r?: ^\"\"^^",
        "         ^<Y1h8888&*dLj-, \"",
        "          ^+L!!__+!^ \":,",
        ">++   ;++! ^]0:\"^  !i><~^   >~_<\"i>>i>i\"  l;",
        ";Z%b>\" xm ^ ::, ^  f#( th{ mc \"r;f#/\"i[Cv+]?",
        "^Y_cBX ~n |}r_]kX_ }o\\:cZi Jqz[^,)*]\" \"iaO",
        "^UI;+h*UXbp<uf/$1 ^}o{ -OY:\"l|mk!}*]\" \"la0",
        ";d)   f@Y0a(+i}$c; fMt <pXtf\" /d~tMr\";_Uz;",
        "<__,  \"ii -([: ?{i:!i+>~I  __~~ \"~>+>i>,",
        "          ^\"^   ^^-XI:",
        "                   Xh>",
        "                    Xh>^",
        "                     Uh_",
        "                      Lq\"",
    ]
    REACTOS_ASCII = [
        "           I>~~+~<<~-][?<",
        "        >+<I          ;<]))]!",
        "      --l                I<[((]l",
        "    []                   I!!>_}){~",
        "  I/i                 >+< ;i<~+-[{}_I",
        "  fI               +}[1tf/}!<~_-?][}]~I",
        " )(             !_?rffjttQw?i+_-?[}{1]<!",
        " \\/?l            ~(f(}{fJQr<>~_?][}{1()< l",
        " Ifj(]<I            -1()]iI!<+_-][}1))|/~ I",
        "   -\\f/1-i               Ii>~_-?][}1)((tt  ?",
        "     !?(//)[>           I!i<+_??[}{1)|/(l  |",
        "         >}-           ;l!>~_-?][}{)\\)<  i/)",
        "                       l!i<+-?]][1({i   1x}",
        "                      I!i<~_-?]}1?l   1x/!",
        "                    ;l!i<~+-]}[~   i|vf<",
        "                   Il!i<~-]]_    ?rc/>",
        "                  Ili>+--~I   ~/zc)l",
        "~               Ili<~~i    <\\XYr?",
        "\\            I!i>i!     ?jYJv1I",
        "/)     ;IIIlI       +|cLLv)!",
        " vjl          I~}fXQ0Jx}l",
        "  \\Yzj\\||/jnzJQO0Ux)<",
        "    }xYLQ0QCXn|-!"
    ]

    TEMPLEOS_ASCII = [
        r"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        r"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        r"@@@                                     @@@",
        r"@@@                           ++        @@@",
        r"@@@                          ++         @@@",
        r"@@@                         ++          @@@",
        r"@@@                  =    +++           @@@",
        r"@@@             ==========+             @@@",
        r"@@@                     ++              @@@",
        r"@@@                    ++               @@@",
        r"@@@                   ++                @@@",
        r"@@@                  ++                 @@@",
        r"@@@          ==    +++      ==          @@@",
        r"@@@               +++                   @@@",
        r"@@@              +++                    @@@",
        r"@@@             +++                     @@@",
        r"@@@          = +++                      @@@",
        r"@@@          =+++                       @@@",
        r"@@@          ++                         @@@",
        r"@@@         ++                          @@@",
        r"@@@                                     @@@",
        r"@@@                                     @@@",
        r"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    ]

    ILLUMOS_ASCII = [
        r"                                           ",
        r"  ==                                       ",
        r" =+++++=                                   ",
        r"   +++++#                                  ",
        r"    =++++##                                ",
        r"      ==++=##                              ",
        r"       ==++=####                           ",
        r"         =====####                         ",
        r"           =====######           #######   ",
        r"            #======######     ######       ",
        r"               ======#############         ",
        r"                 #======##########         ",
        r"                   ###===########=         ",
        r"                      ##########==         ",
        r"                       ########==          ",
        r"                        #######=           ",
        r"                        ######             ",
        r"                      ######               ",
        r"                   ######                  ",
        r"                #######                    ",
        r"                   ##                      ",
        r"                 ##                        ",
        r"               #                           ",
    ]

    HAIKU_ASCII = [
        r"                                           ",
        r"                                           ",
        r"                                           ",
        r"                                           ",
        r"             ####             ###          ",
        r"             ####             ###          ",
        r"             ####             ###          ",
        r"             ####             ###          ",
        r"             ####             ###==        ",
        r"             ####        =============     ",
        r"             ####    ================      ",
        r"             ####==================        ",
        r"  =======   ======================         ",
        r"    ============================#          ",
        r"             =================###          ",
        r"             ####==========   ###          ",
        r"             ####             ###          ",
        r"             ####             ###          ",
        r"             ####             ###          ",
        r"                                           ",
        r"                                           ",
        r"                                           ",
        r"                                           ",
    ]

    LINUXFROMSCRATCH_ASCII = [
        r"                                           ",
        r"                                           ",
        r"               .+====+:                    ",
        r"               =#######+.                  ",
        r"              .=========:.      .:         ",
        r"       +=+:..  :===#====:....:+=##=:       ",
        r"      +####====+=#==###======###==##+.     ",
        r"     :##=+++===###=#=+:::::==+==###==:.    ",
        r"     ==:    .+====#+.       +==##===#+..   ",
        r"    :#= .+:.  =====   :+::   +#=++++++..   ",
        r"    :=+ ##:+. +#===  :##=+=  .=+::.....    ",
        r"    +#= =#==: +++++. +#=###. .=:..         ",
        r"    :##. +=+::.  .....+===:  +#+:...:+     ",
        r"    .=#=..:........... ...  :#=######:     ",
        r"     +=+:..............  ....+===#===:..   ",
        r"     .+.............  ....:. +#===##+::.   ",
        r"      .:.....::+..........:+:+==#=++::.    ",
        r"       .::::::::..........::::.::+:::..    ",
        r"        .................:::..  .....      ",
        r"                 ..::::::::.               ",
        r"                   ........                ",
        r"                                           ",
        r"                                           ",
    ]

    distro_role_mapping = {
        1521868543799328808: ("Arch Linux", ARCH_ASCII),
        1521870392472502344: ("Manjaro", MANJARO_ASCII),
        1521870674669338654: ("EndeavourOS", ENDEAVOUROS_ASCII),
        1521871074994950295: ("Garuda Linux", GARUDA_ASCII),
        1521871078308184074: ("Artix Linux", ARTIX_ASCII),
        1522137195102867526: ("Black Arch", BLACKARCH_ASCII),
        1522143963904081920: ("CachyOS", CACHYOS_ASCII),
        1521870173861056655: ("Debian", DEBIAN_ASCII),
        1521870110552227910: ("Ubuntu", UBUNTU_ASCII),
        1521868791942742026: ("Linux Mint", MINT_ASCII),
        1521871399403393044: ("Kali Linux", KALI_ASCII),
        1521871613958819860: ("Pop!_OS", POP_ASCII),
        1521871816321404969: ("Zorin OS", ZORIN_ASCII),
        1521871679368986655: ("MX Linux", MX_ASCII),
        1521871896117776468: ("Deepin", DEEPIN_ASCII),
        1521872016901406720: ("Elementary OS", ELEMENTARY_ASCII),
        1522137253856415784: ("Parrot OS", PARROT_ASCII),
        1521870225228955798: ("Gentoo", GENTOO_ASCII),
        1521872173688422420: ("Nobara", NOBARA_ASCII),
        1521872360393670819: ("Fedora", FEDORA_ASCII),
        1521872534117679206: ("Red Star OS", REDSTAR_ASCII),
        1521872635968098344: ("Void Linux", VOID_ASCII),
        1534520300807520379: ("NixOS", NIXOS_ASCII),
        1521872759691542588: ("Alpine Linux", ALPINE_ASCII),
        1521873026776301608: ("openSUSE", OPENSUSE_ASCII),
        1521873129868365964: ("Slackware", SLACKWARE_ASCII),
        1534519999681658941: ("Chimera Linux", CHIMERA_ASCII),
        1538268578497962065: ("Linux From Scratch", LINUXFROMSCRATCH_ASCII)
    }

    win_role_mapping = {
        1521909235594825941: ("Windows 11", WIN11_ASCII),
        1521909403496742973: ("Windows 10", WIN10_ASCII),
        1521909451739893982: ("Windows 8", WINDOWS_ASCII),
        1521909341802725427: ("Windows 7", WINDOWS_ASCII),
        1522212167393214514: ("Windows Vista", WINDOWS_ASCII),
        1522212092663300248: ("Windows XP", WINDOWS_ASCII)
    }

    bsd_role_mapping = {
        1521909235594825999: ("FreeBSD", FREEBSD_ASCII),
        1522211951709519872: ("GhostBSD", GHOSTBSD_ASCII),
        1522211033073324234: ("OpenBSD", OPENBSD_ASCII),
        1522211796532854826: ("DragonFly BSD", DRAGONFLY_ASCII),
        1522211599744499834: ("NetBSD", NETBSD_ASCII)
    }

    apple_role_mapping = {
        1538125479222181888: ("Android", ANDROID_ASCII),
        1538125249315479593: ("MacOS", IOS_ASCII),
        1538125362452496425: ("iOS", IOS_ASCII),
    }

    otheros_role_mapping = {
        1538277203564044348: ("Temple OS", TEMPLEOS_ASCII),
        1538277859263520949: ("Haiku", HAIKU_ASCII),
        1538277539640905849: ("IllumOS", ILLUMOS_ASCII),
    }

    # Merge every OS role (distro / windows / bsd / apple / other) into one map
    # so the neofetch logo + OS name always reflect the HIGHEST-PRIORITY role,
    # and up to 3 extra OSes show under "Other OS" for dual/multiboot users.
    os_role_mapping = {}
    os_role_mapping.update(distro_role_mapping)
    os_role_mapping.update(win_role_mapping)
    os_role_mapping.update(bsd_role_mapping)
    os_role_mapping.update(apple_role_mapping)
    os_role_mapping.update(otheros_role_mapping)

    de_role_mapping = {
        1535969909954183239: "KDE Plasma",
        1535970090724495470: "GNOME",
        1535970501740990494: "XFCE",
        1535970676337418240: "Cinnamon",
        1535970708046356552: "MATE",
    }

    wm_role_mapping = {
        1535970826686431314: "Niri",
        1535971021008543744: "Hyprland",
        1535971133260701716: "i3",
        1535971171260964944: "Sway",
        1535971353801396275: "Mango WM",
    }

    gpu_role_mapping = {
        1521879270530486414: "NVIDIA",
        1521879224951246928: "AMD",
        1521879315648614410: "Intel",
    }

    matched_os = []
    for role in reversed(ctx.author.roles):  # highest role position first
        if role.id in os_role_mapping and role.id not in [m[0] for m in matched_os]:
            matched_os.append((role.id, os_role_mapping[role.id]))
        if len(matched_os) >= 4:
            break

    matched_de = []
    for role in reversed(ctx.author.roles):
        if role.id in de_role_mapping and role.id not in matched_de:
            matched_de.append(de_role_mapping[role.id])

    matched_wm = []
    for role in reversed(ctx.author.roles):
        if role.id in wm_role_mapping and role.id not in matched_wm:
            matched_wm.append(wm_role_mapping[role.id])

    matched_gpu = []
    for role in reversed(ctx.author.roles):
        if role.id in gpu_role_mapping and role.id not in matched_gpu:
            matched_gpu.append(gpu_role_mapping[role.id])

    if matched_os:
        final_os = matched_os[0][1][0]
        final_ascii = matched_os[0][1][1]
    else:
        final_os = "Linux (Tux)"
        final_ascii = TUX_ASCII

    other_os = [entry[1][0] for entry in matched_os[1:4]]

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
        f"Other OS: {', '.join(other_os)}" if other_os else "Other OS: None",
        f"Host: Linux & Beyond",
        f"DE: {', '.join(matched_de)}" if matched_de else "DE: None",
        f"WM: {', '.join(matched_wm)}" if matched_wm else "WM: None",
        f"GPU: {', '.join(matched_gpu)}" if matched_gpu else "GPU: None",
        f"Authority: {auth_level}",
        f"Uptime: {uptime_str}",
        f"Roles: {role_count}",
        f"Shell: adminpingu-bot ?/slash",
        f"Prefix: ? (or use / anywhere)"
    ]

    # Some logos (e.g. Chimera Linux, NixOS, Ubuntu) are much wider than the
    # old fixed 22-char column, so the left column width is now computed per
    # logo to make sure every ASCII art fits fully without getting clipped.
    ascii_width = max((len(line) for line in final_ascii), default=22)
    max_lines = max(len(final_ascii), len(stats_lines))

    def _make_lines():
        for i in range(max_lines):
            left = final_ascii[i].ljust(ascii_width) if i < len(final_ascii) else " " * ascii_width
            right = stats_lines[i] if i < len(stats_lines) else ""
            yield f"{left}  {right}"

    content_lines = list(_make_lines())

    # Pack the lines into chunks so every ansi block stays under Discord's
    # 2000-char message limit, regardless of how wide or tall the logo is.
    chunks = []
    current = []
    current_len = 11  # "```ansi\n" + "\n```\n"
    for line in content_lines:
        if current and current_len + len(line) > 1985:
            chunks.append(current)
            current = []
            current_len = 11
        current.append(line)
        current_len += len(line) + 1
    if current:
        chunks.append(current)

    for chunk in chunks:
        await ctx.send("```ansi\n" + "\n".join(chunk) + "\n```")

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
            "Debian/Ubuntu (apt)": "sudo apt install <paket>",
            "Fedora/RHEL (dnf)": "sudo dnf install <paket>",
            "Arch (pacman)": "sudo pacman -S <paket>",
            "openSUSE (zypper)": "sudo zypper install <paket>",
            "Alpine (apk)": "sudo apk add <paket>"
        },
        "remove": {
            "Debian/Ubuntu (apt)": "sudo apt remove <paket>",
            "Fedora/RHEL (dnf)": "sudo dnf remove <paket>",
            "Arch (pacman)": "sudo pacman -R <paket>",
            "openSUSE (zypper)": "sudo zypper remove <paket>",
            "Alpine (apk)": "sudo apk del <paket>"
        },
        "update": {
            "Debian/Ubuntu (apt)": "sudo apt update && sudo apt upgrade",
            "Fedora/RHEL (dnf)": "sudo dnf upgrade --refresh",
            "Arch (pacman)": "sudo pacman -Syu",
            "openSUSE (zypper)": "sudo zypper refresh && sudo zypper update",
            "Alpine (apk)": "sudo apk update && sudo apk upgrade"
        },
        "search": {
            "Debian/Ubuntu (apt)": "apt search <paket>",
            "Fedora/RHEL (dnf)": "dnf search <paket>",
            "Arch (pacman)": "pacman -Ss <paket>",
            "openSUSE (zypper)": "zypper search <paket>",
            "Alpine (apk)": "apk search <paket>"
        }
    }
    if action not in cheatsheet:
        return await ctx.send(f"❌ Unknown action `{action}`. Try one of: `install`, `remove`, `update`, `search`.")
    table = cheatsheet[action]
    desc = "\n".join([f"**{distro}**\n`{cmd}`" for distro, cmd in table.items()])
    embed = discord.Embed(title=f"📦 Package Manager Cheatsheet — {action}", description=desc, color=discord.Color.blurple())
    await ctx.send(embed=embed)

@bot.hybrid_command(name="distrobattle", aliases=["db", "distrowar"], description="Pits two random Linux distros against each other.")
async def distrobattle(ctx):
    distros = [
        "Arch Linux", "Ubuntu", "Fedora", "Debian", "Gentoo", "NixOS",
        "Void Linux", "Manjaro", "openSUSE", "Alpine Linux", "Slackware", "CachyOS"
    ]
    fighter_a, fighter_b = random.sample(distros, 2)
    winner = random.choice([fighter_a, fighter_b])
    taunts = [
        "compiled its way to victory in record time.",
        "won simply because it didn't need a GUI to fight.",
        "took the crown after the other's package manager crashed mid-battle.",
        "claimed victory using nothing but a rolling release and pure spite.",
        "won because 'I use Arch btw' carries actual combat power.",
        "outlasted the opponent with superior documentation."
    ]
    embed = discord.Embed(
        title="⚔️ Distro Battle Arena",
        description=f"**{fighter_a}** 🆚 **{fighter_b}**\n\n🏆 **{winner}** {random.choice(taunts)}",
        color=discord.Color.dark_gold()
    )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="uptime", aliases=["up"], description="Shows how long the bot has been running.")
async def uptime(ctx):
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, rem = divmod(uptime_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    embed = discord.Embed(title="⏱️ System Uptime", color=discord.Color.dark_teal())
    embed.add_field(name="Process", value="`adminpingu-bot`", inline=True)
    embed.add_field(name="Status", value="`running`", inline=True)
    embed.add_field(name="Uptime", value=f"`{days}d {hours}h {minutes}m {seconds}s`", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="shortcuts", aliases=["sc", "aliases"], description="Lists all command shortcuts.")
async def shortcuts(ctx):
    embed = discord.Embed(
        title="⚡ Command Shortcuts",
        description="Full commands and their short forms. Both `?` prefix and `/` slash work with the full name.\n"
                     "**Bonus:** if you type an unrecognized shortcut like `?ldrst`, the bot will try to guess "
                     "what you meant automatically, as long as it's an unambiguous match.",
        color=discord.Color.teal()
    )
    embed.add_field(
        name="🛡️ Moderation",
        value="`?sudolock` → `lock` | `?sudounlock` → `unlock`\n"
              "`?mute` → `m`, `timeout` | `?unmute` → `um`\n"
              "`?clear` → `purge`, `c`\n"
              "`?undo` → `undohistory`, `cleanbotmsgs`\n"
              "`?warning` → `warn` | `?warnings` → `warns`, `w`\n"
              "`?clearwarnings` → `cw`, `clwarns`\n"
              "`?emojiids` → `eids`\n"
              "`?ban` → `b` | `?unban` → `ub`\n"
              "`?setnewschannel` → `snc` | `?setdistrochannel` → `sdc`, `setdistrovs`",
        inline=False
    )
    embed.add_field(
        name="📊 Stats & Utilities",
        value="`?stats` → `st`, `s`, `sta`, `stat`, `profile`, `rank`, `lvl`\n"
              "`?customize` → `cust`, `customise`\n"
              "`?leaderstats` → `ls`, `lstats`, `top`, `ldrst`, `leaders`\n"
              "`?serverinfo` → `sinfo`, `si`\n"
              "`?help` → `h`, `commands`, `cmds`\n"
              "`?dbstatus` → `dbcheck`, `mongostatus`\n"
              "`?fixlevels` → `recalclevels`, `syncxp`",
        inline=False
    )
    embed.add_field(
        name="🎮 Fun & Random",
        value="`?weather` → `wx` | `?tankfact` → `tank`, `tf`\n"
              "`?pythontip` → `pytip`, `ptip` | `?randomlinux` → `rl`, `linuxtip`\n"
              "`?whoami` → `wa` | `?avatar` → `av`, `pfp` | `?ping` → `latency`, `pg`\n"
              "`?coinflip` → `cf`, `flip` | `?diceroll` → `dice`, `roll`\n"
              "`?neofetch` → `nf`, `sysinfo` | `?cowsay` → `cow` | `?fortune` → `ft`\n"
              "`?packagemap` → `pkg`, `pkgcheat` | `?distrobattle` → `db`, `distrowar`\n"
              "`?uptime` → `up` | `?gif` → `g` | `?joke` → `j`\n"
              "`?terminal` → `term`",
        inline=False
    )
    await ctx.send(embed=embed)

MODERATION_HELP = (
    "`?sudolock` / `?sudounlock` - Locks/Unlocks a text channel\n"
    "`?mute <user> [h]` / `?unmute <user>` - Manages timeouts\n"
    "`?clear` - Mass deletes messages in a channel\n"
    "`?undo [amount]` - Deletes AdminPingu's own recent messages in this channel only, with a report\n"
    "`?warning <user> [reason]` - Gives a user a warning\n"
    "`?warnings <user>` - Shows a user's warning history\n"
    "`?clearwarnings <user>` - Resets a user's warnings to 0\n"
    "`?ban <user> [reason]` / `?unban <id>` - Manages bans\n"
    "`?setnewschannel` - Sets the channel for tech news\n"
    "`?setdistrochannel` - Sets the channel for the AI Distro Showdown (every ~12h)\n"
    "`?setjoinchannel` - Sets the channel for welcome banners\n"
    "`?messagesendadminpingu` - Sets the channel for the automated rules reminder\n"
    "`?fixlevels` - Recalculates everyone's level against the current XP curve\n"
    "`?dbstatus` - Checks MongoDB connectivity and collection counts\n"
    "`?emojiids` - DMs you every custom emoji's name and ID, sorted alphabetically"
)

STATS_HELP = (
    "`?stats [user]` - View a user's level and XP\n"
    "`?customize` - Personalize your stats card font, color and background\n"
    "`?leaderstats` - See the top 15 users in the server\n"
    "`?serverinfo` - Display information about this server\n"
    "`?shortcuts` - See every command's short alias"
)

FUN_HELP = (
    "`?weather <city>` - Get the current weather\n"
    "`?randomlinux` / `?whoami` / `?pythontip` - Tech stuff\n"
    "`?neofetch` / `?cowsay <text>` / `?fortune` - Linux terminal fun\n"
    "`?packagemap <action>` / `?distrobattle` - More Linux nerdery\n"
    "`?uptime` - How long the bot has been running\n"
    "`?tankfact` - Interesting facts\n"
    "`?tea` - Brew some tea for someone\n"
    "`?coinflip` / `?diceroll` / `?8ball` / `?joke` / `?gif` - Minigames\n"
    "`?terminal` - Opens your own private Python sandbox terminal channel"
)

def _help_cover_embed():
    embed = discord.Embed(
        title="🐧 AdminPingu Command List",
        description="Every command works with **both** `?prefix` and `/slash`. Use `?shortcuts` to see every alias, "
                     "and don't worry about typing the full name — a close-enough shortcut usually gets auto-detected too.\n\n"
                     "📖 **Select a section with the buttons below:**\n"
                     "**1** 🛡️ Moderation Commands\n"
                     "**2** 📊 Stats & Utilities\n"
                     "**3** 🎮 Fun & Random",
        color=discord.Color.dark_green()
    )
    embed.set_footer(text="Arguments in [brackets] are optional, <angle brackets> are required. Try /help too!")
    return embed

def _help_section_embed(title, content, color):
    embed = discord.Embed(title=title, description=content, color=color)
    embed.set_footer(text="Select another section with buttons 1, 2 or 3 below.")
    return embed

class HelpSectionButton(discord.ui.Button):
    def __init__(self, label, emoji, custom_id, section_embed):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary, custom_id=custom_id)
        self.section_embed = section_embed

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.section_embed, view=self.view)

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(HelpSectionButton("1", "🛡️", "help_section_mod", _help_section_embed("🛡️ Moderation Commands", MODERATION_HELP, discord.Color.red())))
        self.add_item(HelpSectionButton("2", "📊", "help_section_stats", _help_section_embed("📊 Stats & Utilities", STATS_HELP, discord.Color.blue())))
        self.add_item(HelpSectionButton("3", "🎮", "help_section_fun", _help_section_embed("🎮 Fun & Random", FUN_HELP, discord.Color.gold())))

@bot.hybrid_command(name="help", aliases=["h", "commands", "cmds"], description="Lists all bot commands.")
async def help(ctx):
    if ctx.interaction:
        await ctx.send(embed=_help_cover_embed(), view=HelpView(), ephemeral=True)
    else:
        await ctx.send(embed=_help_cover_embed(), view=HelpView())

@bot.listen()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **Access Denied:** You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Syntax Error:** You are missing some arguments! Check `?help` for usage.")
    else:
        logger.error(
            f"Unhandled command error in '{ctx.command}': {type(error).__name__}: {error}",
            exc_info=error,
        )


@bot.event
async def on_error(event_method, *args, **kwargs):
    """
    Called automatically by discord.py whenever an exception is raised
    inside ANY event handler (on_message, on_ready, on_member_join,
    etc.) and is not caught locally. Previously there was no override
    for this, so discord.py fell back to its own default behaviour of
    just printing a bare traceback to stderr and moving on — easy to
    lose. Now it's always routed through our logger (console + file).
    """
    logger.error(f"Unhandled exception in event '{event_method}':")
    logger.error(traceback.format_exc())


async def on_tree_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """
    Slash commands (the /-prefixed ones) raise through the app command
    tree instead of on_command_error above. There was previously no
    handler registered for this at all, so any exception inside a
    slash command silently vanished into discord.py's own default
    stderr-only handler. This makes sure it's logged the same way as
    every other error path, and gives the user a clean error message
    instead of the interaction just hanging/failing with no feedback.
    """
    logger.error(f"Unhandled slash command error in '{interaction.command}': {error}", exc_info=error)
    try:
        if interaction.response.is_done():
            await interaction.followup.send("❌ Something went wrong while running that command.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Something went wrong while running that command.", ephemeral=True)
    except Exception:
        # If we can't even reply to the interaction (e.g. it already
        # expired), there's nothing more useful we can do here.
        pass


bot.tree.on_error = on_tree_error

# =====================================================================
# DISTRO VS — AI-generated Linux distro showdown poster system
# =====================================================================
# How this works (per admin spec):
#   1. An admin points the feature at a channel with ?setdistrochannel #channel.
#      That channel ID is saved to MongoDB (NOT an env var anymore), so it
#      survives bot restarts/redeploys automatically.
#   2. A background task checks periodically. If 12 hours have passed since
#      the last post (or nothing has ever been posted), it picks 2 random
#      distros out of the top 60, generates an epic "VS" poster with
#      Hugging Face's FLUX.1-schnell model, posts it with ⬅️ / ➡️ voting
#      reactions, and saves the new "last sent" timestamp to MongoDB.
#   3. Because the "last sent" timestamp is also in MongoDB, a bot restart
#      never causes an extra/duplicate post — if a message already went out
#      less than 12h ago, the task just waits out the remainder next tick.
# (The duplicate `from google import genai` import was removed here since
# it's already imported once at the top of the file.)

# --- Hugging Face Inference token setup ---
# Add this env var wherever you configure the bot's environment (Railway/
# Render/.env/etc):
#   HF_TOKEN = <your free Hugging Face access token>
# Get one at https://huggingface.co/settings/tokens (a plain "Read" token is
# enough — no billing/credit card needed). Used to call FLUX.1-schnell via
# HF's free Inference Providers router below.
HF_TOKEN = os.environ.get("HF_TOKEN")
print(f"HF token loaded from env: {'yes, length ' + str(len(HF_TOKEN)) if HF_TOKEN else 'NO — HF_TOKEN is missing/empty!'}", flush=True)

# We use the official huggingface_hub client instead of hand-rolling the raw
# HTTP route, because HF's Inference Providers routing changes over time
# (e.g. FLUX.1-schnell was pulled from the "hf-inference" provider on
# 2026-07-15/16 — see https://discuss.huggingface.co/t/177901). provider="auto"
# means HF picks whichever partner (fal, together, nebius, etc.) currently
# serves the model on your account's free/included credits, and keeps working
# automatically if that changes again in the future.
try:
    from huggingface_hub import InferenceClient
    hf_client = InferenceClient(api_key=HF_TOKEN, provider="auto") if HF_TOKEN else None
except Exception as e:
    hf_client = None
    print(f"HF InferenceClient init error: {e}", flush=True)

# How often the background task WAKES UP to check whether it's time to post.
# This is just the "check interval", not the posting interval — the actual
# posting cadence is controlled by DISTRO_VS_INTERVAL_SECONDS below.
DISTRO_VS_CHECK_INTERVAL_MINUTES = 15

# The real posting cadence: once every 12 hours, per the spec.
DISTRO_VS_INTERVAL_SECONDS = 12 * 60 * 60

# Top 60 most popular/well-known Linux distributions, used to randomly pick
# 2 contenders for each showdown.
TOP_60_DISTROS = [
    "Ubuntu", "Debian", "Fedora", "Arch Linux", "Linux Mint",
    "openSUSE", "Manjaro", "Pop!_OS", "EndeavourOS", "Zorin OS",
    "Kali Linux", "Elementary OS", "MX Linux", "Garuda Linux",
    "Solus", "Void Linux", "Gentoo", "NixOS", "Slackware", "CentOS",
    "Rocky Linux", "AlmaLinux", "Deepin", "Kubuntu", "Xubuntu",
    "Lubuntu", "PCLinuxOS", "Peppermint OS", "antiX", "Puppy Linux",
    "Tails", "Qubes OS", "Parrot OS", "BlackArch", "Artix Linux",
    "CachyOS", "Nobara", "Bazzite", "Clear Linux", "Alpine Linux",
    "OpenMandriva", "Mageia", "Feren OS", "KDE Neon", "Regolith Linux",
    "SparkyLinux", "Bodhi Linux", "Q4OS", "Tiny Core Linux",
    "Redcore Linux", "GhostBSD", "Ubuntu Studio", "Devuan",
    "Vanilla OS", "SteamOS", "ArcoLinux", "Fedora Silverblue",
    "Chimera Linux", "Linux From Scratch", "siduction"
]

# Curated 2-4 word taglines per distro, based on real-world reputation/
# philosophy. Used to draw the "philosophy" caption under each side of the
# poster ourselves (see DISTRO_VS text-overlay code below) instead of asking
# the image model to render text — diffusion models like FLUX.1-schnell are
# notoriously bad at spelling out text, so we draw it with Pillow instead for
# guaranteed-crisp typography.
DISTRO_TAGLINES = {
    "Ubuntu": "MASS ADOPTION", "Debian": "ANCIENT STABILITY",
    "Fedora": "BLEEDING INNOVATION", "Arch Linux": "PURE POWER",
    "Linux Mint": "GENTLE COMFORT", "openSUSE": "ENGINEERED PRECISION",
    "Manjaro": "ROLLING FREEDOM", "Pop!_OS": "MAKER'S FORGE",
    "EndeavourOS": "ARCH SIMPLIFIED", "Zorin OS": "FAMILIAR DISGUISE",
    "Kali Linux": "OFFENSIVE EDGE", "Elementary OS": "DESIGNED ELEGANCE",
    "MX Linux": "LIGHTWEIGHT GRIT", "Garuda Linux": "AGGRESSIVE FLAIR",
    "Solus": "INDEPENDENT VISION", "Void Linux": "MINIMALIST CONTROL",
    "Gentoo": "SOURCE UNBOUND", "NixOS": "PURE SCIENCE",
    "Slackware": "OLD GUARD", "CentOS": "ENTERPRISE LEGACY",
    "Rocky Linux": "COMMUNITY REBUILT", "AlmaLinux": "STEADY FOUNDATION",
    "Deepin": "AESTHETIC HARMONY", "Kubuntu": "PLASMA POLISH",
    "Xubuntu": "XFCE EFFICIENCY", "Lubuntu": "FEATHERWEIGHT SPEED",
    "PCLinuxOS": "VETERAN SIMPLICITY", "Peppermint OS": "CLOUD-LIGHT LIVING",
    "antiX": "SYSTEMD DEFIANCE", "Puppy Linux": "TINY RESILIENCE",
    "Tails": "GHOST PROTOCOL", "Qubes OS": "COMPARTMENTED TRUST",
    "Parrot OS": "SHADOW OPERATIONS", "BlackArch": "ARSENAL OVERLOAD",
    "Artix Linux": "INIT REBELLION", "CachyOS": "PERFORMANCE OBSESSED",
    "Nobara": "GAMER'S EDGE", "Bazzite": "IMMUTABLE PLAYGROUND",
    "Clear Linux": "OPTIMIZED VELOCITY", "Alpine Linux": "MINIMAL FORTRESS",
    "OpenMandriva": "EUROPEAN CRAFT", "Mageia": "COMMUNITY HERITAGE",
    "Feren OS": "POLISHED NEWCOMER", "KDE Neon": "BLEEDING PLASMA",
    "Regolith Linux": "TILING DISCIPLINE", "SparkyLinux": "LIGHTWEIGHT SPARK",
    "Bodhi Linux": "ENLIGHTENED MINIMALISM", "Q4OS": "RETRO EFFICIENCY",
    "Tiny Core Linux": "MICRO ESSENCE", "Redcore Linux": "GENTOO SIMPLIFIED",
    "GhostBSD": "BSD SERENITY", "Ubuntu Studio": "CREATIVE ARSENAL",
    "Devuan": "INIT FREEDOM", "Vanilla OS": "IMMUTABLE FUTURE",
    "SteamOS": "LIVING ROOM CONQUEST", "ArcoLinux": "LEARN BY BUILDING",
    "Fedora Silverblue": "ATOMIC RELIABILITY", "Chimera Linux": "HYBRID EXPERIMENT",
    "Linux From Scratch": "BUILD EVERYTHING", "siduction": "DEBIAN UNLEASHED",
}
DEFAULT_TAGLINE = "UNKNOWN POWER"

# Rotating pool of bottom-banner hook lines (drawn ourselves, see below).
DISTRO_VS_HOOK_LINES = [
    "LINUX EVOLVED: WHICH ONE RULES?",
    "TWO PHILOSOPHIES. ONE THRONE.",
    "DISTROS COLLIDE: PICK YOUR SIDE.",
    "ONLY ONE CAN BOOT SUPREME.",
    "CHOOSE YOUR KERNEL. CHOOSE YOUR FATE.",
    "THE PACKAGE WARS CONTINUE.",
    "WHICH PHILOSOPHY WINS TONIGHT?",
    "ONE ROOTFS TO RULE THEM ALL.",
]

# Contrasting (left-color, right-color) pairs, picked at random per matchup
# for visual variety in the title/tagline text.
DISTRO_VS_COLOR_PAIRS = [
    ("#37e6ff", "#ff3b3b"), ("#a566ff", "#ffd23b"), ("#39ff88", "#ff2079"),
    ("#ffb238", "#3b82ff"), ("#ff5fdb", "#5fffb0"), ("#ffe15f", "#7b5fff"),
]

# ==========================================
# Distro VS persistence helpers (MongoDB)
# ==========================================
async def load_distro_vs_config():
    try:
        return await config_collection.find_one({"_id": "distro_vs_config"})
    except Exception as e:
        print(f"Distro VS config load error: {e}")
        return None

async def set_distro_vs_channel(channel_id):
    try:
        await config_collection.update_one(
            {"_id": "distro_vs_config"},
            {"$set": {"channel_id": channel_id}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Distro VS channel save error: {e}")
        return False

async def update_distro_vs_last_sent(timestamp):
    try:
        await config_collection.update_one(
            {"_id": "distro_vs_config"},
            {"$set": {"last_sent": timestamp}},
            upsert=True
        )
    except Exception as e:
        print(f"Distro VS last_sent save error: {e}")

# --- Image generation via Hugging Face Inference Providers (FLUX.1-schnell) ---
# Switched away from Gemini's gemini-2.5-flash-image model because Google does
# not offer any free quota for image generation (limit: 0 on the free tier,
# confirmed via 429 RESOURCE_EXHAUSTED errors in production logs). Also
# switched away from Pollinations.ai because its "flux" model routing was
# frequently ignoring the prompt and returning unrelated images. FLUX.1-schnell
# through HF's Inference Providers is a proper open-weight model that follows
# the prompt closely, is free, and only needs a no-cost HF access token (see
# HF_TOKEN above) — no credit card. Free tier is rate-limited but comfortably
# covers "1 image every 12 hours".

HF_FLUX_MODEL = "black-forest-labs/FLUX.1-schnell"

def _build_distro_vs_prompt(distro_a, distro_b):
    # IMPORTANT: this prompt intentionally asks for ZERO text/typography.
    # FLUX.1-schnell (like most diffusion models) is unreliable at spelling
    # out words — it tends to render garbled, misspelled pseudo-text. So we
    # only ask the model for the symbolic/emblematic ARTWORK, and draw all
    # titles, taglines and the hook line ourselves with Pillow afterwards
    # (see _compose_distro_vs_poster below) for guaranteed-crisp typography.
    return (
        f"An ultra-epic, jaw-dropping, cinematic dual-emblem battle artwork "
        f"comparing the Linux distributions '{distro_a}' on the left side and "
        f"'{distro_b}' on the right side. Style: dramatic fantasy/sci-fi hybrid "
        f"digital art, moody volumetric lighting, glowing particle effects, "
        f"ultra high detail, poster-quality, vertical composition.\n\n"
        f"LEFT SIDE ('{distro_a}'): a large, ornate emblem/symbol/sigil that "
        f"visually represents this distro's real-world reputation, philosophy or "
        f"community culture (e.g. raw power, punk rebellion, minimalism, military "
        f"precision, ancient wisdom, corporate order, chaotic freedom — pick "
        f"whichever fits '{distro_a}' best). Background and color palette on this "
        f"side should visually reinforce that theme.\n\n"
        f"RIGHT SIDE ('{distro_b}'): a large, equally ornate but thematically "
        f"CONTRASTING emblem/symbol/sigil representing '{distro_b}''s own "
        f"reputation or philosophy, with its own distinct background and color "
        f"palette that visually clashes against the left side.\n\n"
        f"CENTER: a bold glowing cracked energy shockwave/fracture splitting the "
        f"two halves apart, energy bleeding from the fracture line.\n\n"
        f"Overall the artwork must look extremely eye-catching, flashy, and "
        f"shareable at a glance, matching the energy of a movie poster or a "
        f"trading-card-game box art.\n\n"
        f"CRITICAL: do NOT include any text, letters, words, numbers, logos, "
        f"watermarks, or typography anywhere in the image — pure symbolic/"
        f"emblematic artwork only, no writing of any kind. All titles and labels "
        f"will be added separately afterwards."
    )

async def generate_distro_vs_image(distro_a, distro_b):
    """Generates a Distro VS poster via Hugging Face's Inference Providers,
    using the FLUX.1-schnell model with automatic provider selection. Needs
    HF_TOKEN set in the environment (free token, no billing) — see the
    HF_TOKEN comment above. The model only generates the background/emblem
    ARTWORK (no text — see _build_distro_vs_prompt); all titles, taglines and
    the hook line are drawn afterwards with Pillow via
    _compose_distro_vs_poster, so text is always crisp instead of garbled."""
    if not hf_client:
        print("Distro VS image generation error: HF_TOKEN env var is not set "
              "(or the HF client failed to initialize). Get a free token at "
              "https://huggingface.co/settings/tokens.", flush=True)
        return None

    prompt = _build_distro_vs_prompt(distro_a, distro_b)

    try:
        # InferenceClient is a blocking/sync client, so run it in a thread to
        # avoid stalling the bot's event loop. Returns a PIL.Image on success.
        art_image = await asyncio.to_thread(
            hf_client.text_to_image,
            prompt,
            model=HF_FLUX_MODEL,
            width=1024,
            height=1536,
            num_inference_steps=4,  # schnell is distilled for ~4 steps; more doesn't help.
        )
    except Exception as e:
        print(f"Distro VS image generation error: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        sys.stdout.flush()
        return None

    try:
        # Compositing (Pillow text drawing) is CPU-bound, run off the event loop.
        return await asyncio.to_thread(_compose_distro_vs_poster, art_image, distro_a, distro_b)
    except Exception as e:
        print(f"Distro VS poster compositing error: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        sys.stdout.flush()
        return None

# ==========================================
# Distro VS poster text compositing (Pillow)
# ==========================================
# We draw all typography ourselves instead of trusting the image model with
# it, since diffusion models reliably botch rendered text. Reuses the same
# bundled fonts/ directory + get_font_path() helper as the /customize feature
# defined earlier in this file.

def _distro_vs_font(filename, size):
    path = get_font_path(filename)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def _distro_vs_fit_font(text, filename, start_size, max_width, min_size=28):
    """Shrinks the font size until `text` fits within max_width (handles long
    distro names like 'Fedora Silverblue' or 'Tiny Core Linux')."""
    size = start_size
    while size > min_size:
        font = _distro_vs_font(filename, size)
        if font.getlength(text) <= max_width:
            return font
        size -= 4
    return _distro_vs_font(filename, min_size)

def _distro_vs_wrap_text(text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if not current or font.getlength(test) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def _compose_distro_vs_poster(art_image, distro_a, distro_b):
    """Takes the text-free PIL image returned by FLUX.1-schnell and draws the
    distro titles, taglines and bottom hook banner on top with Pillow. Returns
    final PNG bytes ready to send to Discord."""
    img = art_image.convert("RGBA")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    color_a, color_b = random.choice(DISTRO_VS_COLOR_PAIRS)
    tagline_a = DISTRO_TAGLINES.get(distro_a, DEFAULT_TAGLINE)
    tagline_b = DISTRO_TAGLINES.get(distro_b, DEFAULT_TAGLINE)
    hook_line = random.choice(DISTRO_VS_HOOK_LINES)

    side_margin = int(W * 0.045)
    max_title_width = int(W * 0.46)

    # --- Distro name titles, top-left / top-right ---
    title_font_a = _distro_vs_fit_font(distro_a.upper(), "Impacted.ttf", int(W * 0.11), max_title_width)
    title_font_b = _distro_vs_fit_font(distro_b.upper(), "Impacted.ttf", int(W * 0.11), max_title_width)
    title_y = int(H * 0.05)
    draw.text((side_margin, title_y), distro_a.upper(), font=title_font_a,
               fill=color_a, stroke_width=8, stroke_fill="black")
    draw.text((W - side_margin, title_y), distro_b.upper(), font=title_font_b,
               fill=color_b, stroke_width=8, stroke_fill="black", anchor="ra")

    # --- Taglines just below each title ---
    tagline_font_a = _distro_vs_fit_font(tagline_a, "impact.ttf", int(W * 0.042), max_title_width)
    tagline_font_b = _distro_vs_fit_font(tagline_b, "impact.ttf", int(W * 0.042), max_title_width)
    tagline_y = title_y + int(H * 0.10)
    draw.text((side_margin, tagline_y), tagline_a, font=tagline_font_a,
               fill=color_a, stroke_width=5, stroke_fill="black")
    draw.text((W - side_margin, tagline_y), tagline_b, font=tagline_font_b,
               fill=color_b, stroke_width=5, stroke_fill="black", anchor="ra")

    # --- Center "VS" mark ---
    vs_font = _distro_vs_font("Impacted.ttf", int(W * 0.09))
    draw.text((W // 2, int(H * 0.46)), "VS", font=vs_font, fill="white",
               stroke_width=10, stroke_fill="black", anchor="mm")

    # --- Bottom hook banner: dark translucent strip + centered wrapped text ---
    banner_h = int(H * 0.13)
    banner_top = H - banner_h
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle([(0, banner_top), (W, H)], fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    hook_font = _distro_vs_font("impact.ttf", int(W * 0.052))
    hook_lines = _distro_vs_wrap_text(hook_line, hook_font, W * 0.9)
    line_height = int(W * 0.052 * 1.2)
    total_h = line_height * len(hook_lines)
    start_y = banner_top + (banner_h - total_h) // 2 + line_height // 2
    for i, line in enumerate(hook_lines):
        draw.text((W // 2, start_y + i * line_height), line, font=hook_font,
                   fill="white", stroke_width=4, stroke_fill="black", anchor="mm")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()

# --- Core send logic, shared between the recurring task AND the instant
#     first-post triggered by ?setdistrochannel ---
async def send_distro_vs_showdown(channel):
    """Generates one Distro VS poster and posts it to `channel`.
    Returns True on success, False on failure. Always updates last_sent
    on success so the 12h cooldown restarts from this exact post."""
    distro_a, distro_b = random.sample(TOP_60_DISTROS, 2)
    print(f"Distro VS: attempting matchup '{distro_a}' vs '{distro_b}'...", flush=True)

    image_bytes = await generate_distro_vs_image(distro_a, distro_b)
    if not image_bytes:
        print("Distro VS skipped: image generation failed (check HF_TOKEN validity/quota). "
              "See the 'Distro VS image generation error' line above for the exact cause.", flush=True)
        return False

    file = discord.File(io.BytesIO(image_bytes), filename="distro_vs.png")

    embed = discord.Embed(
        title="⚔️ Distro Showdown!",
        description=(
            f"⬅️ **{distro_a}**  🆚  **{distro_b}** ➡️\n\n"
            f"Which one reigns supreme? React ⬅️ for **{distro_a}**, "
            f"➡️ for **{distro_b}**! A new showdown drops every 12 hours."
        ),
        color=discord.Color.purple()
    )
    embed.set_image(url="attachment://distro_vs.png")
    embed.set_footer(text="AdminPingu Distro Showdown")

    msg = await channel.send(embed=embed, file=file)
    await msg.add_reaction("⬅️")
    await msg.add_reaction("➡️")

    # Persist immediately so a restart right after this never causes a re-send.
    await update_distro_vs_last_sent(time.time())
    return True

# --- Background task: checks every 15 minutes, posts every ~12 hours ---
@tasks.loop(minutes=DISTRO_VS_CHECK_INTERVAL_MINUTES)
async def daily_distro_vs():
    # NOTE: send_distro_vs_showdown() can raise (e.g. discord.Forbidden
    # if the bot loses access to the channel, or an HTTPException on a
    # rate limit) and previously nothing here caught that, which would
    # permanently stop this loop. Now caught + logged, with .error()
    # below as a second safety net.
    await bot.wait_until_ready()
    try:
        config = await load_distro_vs_config()
        if not config or not config.get("channel_id"):
            # No channel configured yet — silently wait until an admin runs ?setdistrochannel.
            return

        channel_id = int(config["channel_id"])
        channel = bot.get_channel(channel_id)
        if not channel:
            logger.warning(
                f"Distro VS skipped: channel {channel_id} not found or bot has no access to it. "
                f"Double-check the channel still exists and re-run ?setdistrochannel if needed."
            )
            return

        last_sent = config.get("last_sent")
        now = time.time()
        if last_sent and (now - last_sent) < DISTRO_VS_INTERVAL_SECONDS:
            # Not due yet — this correctly handles the case where the bot just
            # restarted less than 12h after the previous post, so it will NOT
            # send a duplicate right away.
            return

        await send_distro_vs_showdown(channel)
    except Exception as e:
        logger.error(f"daily_distro_vs tick error: {e}", exc_info=True)


@daily_distro_vs.error
async def daily_distro_vs_error(error):
    logger.error(f"daily_distro_vs loop crashed: {error}", exc_info=error)

# ==========================================
# Memory hygiene: keep in-RAM caches bounded
# ==========================================
# user_message_cache / xp_message_counter / last_user_message_time used to be
# plain dicts that grew forever (every user who ever typed kept a row, even
# after leaving the server or stopping to chat), and TERMINAL_STATE leaked an
# entry every time a terminal channel was deleted in any way other than
# ?close. Fix: (1) purge users inactive for over an hour every 30 minutes,
# (2) drop entries immediately when a member leaves, (3) drop terminal state
# whenever its channel is deleted.
CACHE_USER_TTL_SECONDS = 3600


@tasks.loop(minutes=30)
async def clear_memory_caches():
    await bot.wait_until_ready()
    try:
        cutoff = time.time() - CACHE_USER_TTL_SECONDS
        stale = [uid for uid, ts in last_user_message_time.items() if ts < cutoff]
        for uid in stale:
            user_message_cache.pop(uid, None)
            xp_message_counter.pop(uid, None)
            last_user_message_time.pop(uid, None)
        if stale:
            logger.info(f"🧹 Memory cleanup: removed {len(stale)} inactive user cache entr(y/ies).")
    except Exception as e:
        logger.error(f"Memory cleanup error: {e}", exc_info=True)


@clear_memory_caches.error
async def clear_memory_caches_error(error):
    logger.error(f"clear_memory_caches loop crashed: {error}", exc_info=error)

# ==========================================
# Admin command: configure the Distro VS channel
# ==========================================
@bot.hybrid_command(
    name="setdistrochannel",
    aliases=["sdc", "setdistrovs"],
    description="Sets the channel for the recurring AI-generated Distro VS showdown (admin)."
)
@commands.has_permissions(administrator=True)
async def setdistrochannel(ctx, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    saved = await set_distro_vs_channel(target_channel.id)
    if not saved:
        return await ctx.send("❌ Couldn't save that channel to the database. Check `?dbstatus` and try again.")

    embed = discord.Embed(
        title="⚔️ Distro VS Channel Set",
        description=(
            f"{target_channel.mention} is now the official **Distro Showdown** channel.\n\n"
            f"A new AI-generated matchup between 2 random distros (out of the top 60) will be "
            f"posted here roughly **every 12 hours**, complete with ⬅️/➡️ voting reactions. "
            f"This setting is saved permanently, so it survives bot restarts.\n\n"
            f"🎬 Generating your first showdown right now..."
        ),
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

    # FIX: previously the very first showdown only appeared once the
    # background task happened to tick (up to 15 minutes later). Now setting
    # the channel fires an immediate showdown right away, then the recurring
    # task takes over from there and posts every ~12 hours after this one.
    sent = await send_distro_vs_showdown(target_channel)
    if not sent:
        await ctx.send(
            "⚠️ The instant showdown failed to generate (the free Pollinations.ai image service may be "
            "temporarily overloaded or slow — check the Render logs for `Distro VS image generation error: ...`). "
            "The channel is still saved, so it'll keep retrying automatically every 15 minutes."
        )

# =====================================================================
# Final startup
# =====================================================================
# This replaces the old bare `bot.run(os.environ["DISCORD_TOKEN"])`.
# bot.run() is convenient but gives you no hook to (a) catch a missing
# token before it crashes with a confusing KeyError, (b) install a
# handler for exceptions that occur in "fire and forget" asyncio tasks
# that nobody ever awaits, or (c) guarantee that whatever caused the
# process to stop gets logged before it actually exits. main() below
# does the same job as bot.run() internally, plus all of that.


def asyncio_exception_handler(loop, context):
    """
    Installed on the event loop. This is the last line of defense for
    asyncio-specific failures that don't go through on_error or a
    task's own try/except — most commonly an exception raised inside
    a task created with asyncio.create_task(...) that is never awaited
    and whose result/exception is therefore never retrieved. Without
    this handler, asyncio's own default behaviour is to print a short
    message to stderr, which — combined with the buffering issue fixed
    above — was easy to lose entirely.
    """
    exception = context.get("exception")
    message = context.get("message", "Unhandled asyncio error")
    logger.error(f"Unhandled asyncio exception: {message}", exc_info=exception)


async def main():
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logger.critical(
            "DISCORD_TOKEN environment variable is missing or empty! "
            "The bot cannot log in without it — set it in your host's "
            "environment/secrets panel and restart."
        )
        return

    loop = asyncio.get_running_loop()
    loop.set_exception_handler(asyncio_exception_handler)

    logger.info("Starting AdminPingu...")
    try:
        # Using bot.start() inside an `async with bot` block instead of
        # bot.run() gives us a try/except around the entire bot
        # lifetime, so ANY reason it stops — bad token, fatal network
        # error, an uncaught exception anywhere, or a clean shutdown —
        # is always logged with full context before the process exits.
        async with bot:
            await bot.start(token)
    except discord.LoginFailure:
        logger.critical(
            "Login failed: DISCORD_TOKEN is invalid, expired, or was reset "
            "in the Discord Developer Portal. Generate a new token and "
            "update it, then restart the bot."
        )
    except discord.PrivilegedIntentsRequired:
        logger.critical(
            "Login failed: one or more privileged intents (Members / "
            "Message Content) are not enabled for this bot in the "
            "Discord Developer Portal > Bot > Privileged Gateway Intents."
        )
    except Exception:
        logger.critical("The bot crashed with an unhandled exception:")
        logger.critical(traceback.format_exc())
        raise
    finally:
        logger.warning("AdminPingu process is shutting down now.")


if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Shutdown requested via KeyboardInterrupt (Ctrl+C).")
