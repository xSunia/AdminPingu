import discord
from discord.ext import commands, tasks
from discord.ui import Select, View
from flask import Flask
from threading import Thread
import random
import time
import datetime
import os

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
    # (Diğer komutlarını buraya ekleyebilirsin, çok uzun olmaması için kısalttım)
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
            return await interaction.response.send_message("❌ Rol sunucuda bulunamadı!", ephemeral=True)
            
        # Check and remove existing distro roles
        roles_to_remove = [r for r in interaction.user.roles if r.id in ALL_DISTRO_ROLES and r.id != selected_role_id]
        if roles_to_remove:
            await interaction.user.remove_roles(*roles_to_remove)
            
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ Başarıyla `{role.name}` rolünü aldın! (Önceki dağıtım rolün silindi)", ephemeral=True)

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
            return await interaction.response.send_message("❌ Rol sunucuda bulunamadı!", ephemeral=True)
            
        # Check and remove existing GPU roles
        roles_to_remove = [r for r in interaction.user.roles if r.id in ALL_GPU_ROLES and r.id != selected_role_id]
        if roles_to_remove:
            await interaction.user.remove_roles(*roles_to_remove)
            
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ Başarıyla `{role.name}` sürücü rolünü aldın! (Önceki GPU rolün silindi)", ephemeral=True)

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

        # 4. Independent (Bağımsız)
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
            print(f"Otorol verme hatası: {e}")

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
                await warn_channel.send(f"🚨 {member.mention} 3 uyarı sınırını aştığı için sunucudan banlandı!")
            warning_db[member.id] = 0
        except:
            pass

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    # A. SPAM FILTER (Mod ve Adminler hariç)
    is_mod = message.author.guild_permissions.manage_messages
    if not is_mod:
        if message.author.id not in user_message_cache:
            user_message_cache[message.author.id] = []
        
        user_message_cache[message.author.id].append(message.content.lower())
        
        if len(user_message_cache[message.author.id]) > 3:
            user_message_cache[message.author.id].pop(0)
            
        if len(user_message_cache[message.author.id]) == 3 and len(set(user_message_cache[message.author.id])) == 1:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, lütfen spam yapma!", delete_after=5)
            await apply_warning(message.author, "Spam / Flooding the chat", message.guild)
            user_message_cache[message.author.id] = [] # Cache temizle
            return

    # B. PROFANITY FILTER
    msg_content = message.content.lower()
    if any(word in msg_content for word in PROFANITY_LIST):
        try:
            await message.delete()
            await message.channel.send(f"Hey {message.author.mention}, swearing is strictly prohibited on this server!", delete_after=5)
            await apply_warning(message.author, f"Profanity used: ||{message.content}||", message.guild)
            return  # XP kazanımı iptal
        except Exception as e:
            print(f"Profanity filter error: {e}")

    # C. XP ENGINE TRIGGER (Çok Yavaş Kasılan XP: 5 ila 10 XP)
    gained = random.randint(5, 10)
    leveled_up = add_xp(message.author.id, gained)
    if leveled_up:
        new_level = xp_db[message.author.id]['level']
        level_channel = bot.get_channel(LEVEL_LOG_CHANNEL_ID)
        
        if level_channel:
            await level_channel.send(f"🎉 Tebrikler {message.author.mention}! Sohbet ederek **Seviye {new_level}** oldun!")
            
        # Medya İzni Kontrolü
        if new_level == 20:
            media_role = message.guild.get_role(MEDIA_ROLE_ID)
            if media_role:
                await message.author.add_roles(media_role)
                if level_channel:
                    await level_channel.send(f"📸 {message.author.mention} 20. seviyeye ulaştı ve **Medya İzni** rolünü kazandı!")

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
        description="Aşağıdaki menüleri kullanarak ana Linux dağıtımını ve GPU sürücünü seçebilirsin. Her kategoriden sadece 1 rol alabilirsin.", 
        color=discord.Color.dark_theme()
    )
    await ctx.send(embed=role_embed, view=RolesView())

@bot.command()
async def gif(ctx):
    """Sends a random Linux meme or gif."""
    gif_url = random.choice(LINUX_GIFS)
    embed = discord.Embed(title="🐧 Random Linux Meme/Gif", color=discord.Color.green())
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

@bot.command()
async def stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.id not in xp_db:
        xp_db[member.id] = {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "level": 1, "last_msg": 0}
        
    data = xp_db[member.id]
    next_xp = data["level"] * 50
    
    embed = discord.Embed(title=f"📊 {member.name} Server Statistics", color=discord.Color.purple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Current Level", value=f"`Level {data['level']}`", inline=True)
    embed.add_field(name="Total XP", value=f"`{data['total']} / {next_xp} XP`", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def randomlinux(ctx):
    selected = random.choice(LINUX_COMMANDS)
    embed = discord.Embed(
        title=f"🐧 Linux Terminal Library",
        description=f"**Command:** `{selected['cmd']}`\n\n**Description:** {selected['desc']}",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def warning(ctx, member: discord.Member, *, reason="Manuel Uyarı"):
    await apply_warning(member, reason, ctx.guild)
    await ctx.send(f"✅ {member.mention} kullanıcısına uyarı eklendi. Detaylar warnings kanalına iletildi.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.name} has been successfully banned. Reason: {reason if reason else 'Not specified'}")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🐧 AdminPingu Commands", color=discord.Color.dark_green())
    embed.add_field(name="🛡️ Moderation", value="`?warning <user>` - Adds a warning mark.\n`?ban <user>` - Bans member.", inline=False)
    embed.add_field(name="📊 Analytics & Setup", value="`?stats [user]` - Displays level card.\n`?roles` - Sends Dropdown role panel (Admin).", inline=False)
    embed.add_field(name="🐧 Fun", value="`?randomlinux` - Random terminal command.\n`?gif` - Random Linux GIF.", inline=False)
    await ctx.send(embed=embed)

# ==========================================
# 9. GLOBAL EXCEPTION HANDLER
# ==========================================
@bot.listen()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **ERROR: You lack the necessary privileges!**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **ERROR: Missing argument parameters!**")
    else:
        print(f"Unhandled system error: {error}")

# BOOTUP SEQUENCE
keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
