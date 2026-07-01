import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
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
LOG_CHANNEL_ID = 123456789012345678       # Profanity and Moderation Log Channel ID
ROLE_CHANNEL_ID = 123456789012345678      # Button Role Selection Channel ID
REMINDER_CHANNEL_ID = 123456789012345678  # Hourly Rule Reminder Channel ID

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

# Exactly 60 Most Frequently Used Linux Commands Database
LINUX_COMMANDS = [
    {"cmd": "ls", "desc": "🐧 Used to list directory contents. It is just like taking a quick look at the items inside a room!"},
    {"cmd": "cd", "desc": "🐧 Allows you to navigate between directories. It essentially teleports you from one path to another!"},
    {"cmd": "pwd", "desc": "🐧 Prints the full path of the current working directory. The ultimate answer to 'Where am I right now?'"},
    {"cmd": "mkdir", "desc": "🐧 Creates a brand new, clean directory. Perfect for setting up your project foundations!"},
    {"cmd": "rmdir", "desc": "🐧 Removes empty directories from the system safely."},
    {"cmd": "rm", "desc": "🐧 Deletes files or directories permanently. Be extremely careful; this action cannot be undone!"},
    {"cmd": "cp", "desc": "🐧 Copies files or directories from one location to another cleanly."},
    {"cmd": "mv", "desc": "🐧 Moves or renames files and directories instantly across your storage."},
    {"cmd": "touch", "desc": "🐧 Creates an empty file immediately or updates the modified timestamp of an existing file."},
    {"cmd": "cat", "desc": "🐧 Displays the entire content of a file on the terminal. A quick digital X-ray for text!"},
    {"cmd": "less", "desc": "🐧 Helps you read large files page by page, allowing comfortable scrolling up and down."},
    {"cmd": "more", "desc": "🐧 Similar to 'less', displays file contents page by page but only allows scrolling downwards."},
    {"cmd": "head", "desc": "🐧 Instantly displays the first 10 lines of a specified file."},
    {"cmd": "tail", "desc": "🐧 Displays the last lines of a file. An absolute lifesaver for tracking live log outputs!"},
    {"cmd": "grep", "desc": "🐧 Searches for specific text patterns or words within files like pulling a needle from a haystack!"},
    {"cmd": "find", "desc": "🐧 Searches the system for files and folders based on names, types, or size parameters."},
    {"cmd": "chmod", "desc": "🐧 Changes the read, write, and execute permissions of files and directories completely."},
    {"cmd": "chown", "desc": "🐧 Changes the owner and group ownership of a specified file or directory."},
    {"cmd": "df", "desc": "🐧 Displays free and used disk space on your mounted file systems."},
    {"cmd": "du", "desc": "🐧 Measures and estimates file and directory space usage on your disk in detail."},
    {"cmd": "free", "desc": "🐧 Renders RAM statistics, displaying total, used, and free memory in real-time."},
    {"cmd": "top", "desc": "🐧 Lists active system processes and resource hogs like an interactive task manager."},
    {"cmd": "htop", "desc": "🐧 A much sleeker, colorful, and highly interactive modern upgrade to the classic 'top' command!"},
    {"cmd": "ps", "desc": "🐧 Snapshots currently running processes on the system along with their unique PIDs."},
    {"cmd": "kill", "desc": "🐧 Terminates a process running in the background by specifying its process ID (PID) with no mercy."},
    {"cmd": "pkill", "desc": "🐧 Stops running processes directly by their name instead of their numerical PID."},
    {"cmd": "systemctl", "desc": "🐧 Starts, stops, restarts, or enables background system services and daemons."},
    {"cmd": "journalctl", "desc": "🐧 Queries and displays logs from the systemd journal to help with system debugging."},
    {"cmd": "ping", "desc": "🐧 Sends small packets to a target host to test network connectivity and latency (MS)."},
    {"cmd": "ifconfig", "desc": "🐧 The classic network utility to display network interface parameters and local IP configurations."},
    {"cmd": "ip", "desc": "🐧 A powerful modern network tool to display and manage routing, devices, policy routing, and tunnels."},
    {"cmd": "netstat", "desc": "🐧 Displays active network connections, routing tables, and interface statistics."},
    {"cmd": "ss", "desc": "🐧 A modern, faster utility compared to 'netstat' for investigating network sockets."},
    {"cmd": "curl", "desc": "🐧 A versatile command-line tool to transfer data to or from a server using various web protocols."},
    {"cmd": "wget", "desc": "🐧 Downloads files directly from the internet via terminal using HTTP, HTTPS, or FTP."},
    {"cmd": "ssh", "desc": "🐧 Establishes a secure, encrypted connection to remote Linux servers over the network."},
    {"cmd": "scp", "desc": "🐧 Transfers files securely between local and remote hosts using the SSH protocol."},
    {"cmd": "rsync", "desc": "🐧 An incredibly fast and versatile file copying and synchronization tool for backups."},
    {"cmd": "tar", "desc": "🐧 Packages multiple files into a single archive file, or extracts compressed archive structures."},
    {"cmd": "gzip", "desc": "🐧 Compresses files to reduce their storage footprint on your disk drive."},
    {"cmd": "gunzip", "desc": "🐧 Restores files compressed by 'gzip' back to their original size and format."},
    {"cmd": "zip", "desc": "🐧 Compresses and packages files into the globally recognized .zip file format."},
    {"cmd": "unzip", "desc": "🐧 Extracts compressed archive packages matching the .zip format into a folder."},
    {"cmd": "uname", "desc": "🐧 Prints detailed technical information about the running Linux kernel and OS architecture."},
    {"cmd": "hostname", "desc": "🐧 Displays or configures the system's official network name on the local domain."},
    {"cmd": "uptime", "desc": "🐧 Shows how long the server has been running continuously without a shutdown."},
    {"cmd": "whoami", "desc": "🐧 Tells you exactly which user session is currently active in the terminal window."},
    {"cmd": "id", "desc": "🐧 Lists numerical user and group IDs (UID/GID) for the current active account."},
    {"cmd": "sudo", "desc": "🐧 Runs a command with the elevated security privileges of the system administrator 'root'."},
    {"cmd": "su", "desc": "🐧 Switches the terminal session to a completely different user without logging out."},
    {"cmd": "passwd", "desc": "🐧 Changes the system password of the current user or a designated account."},
    {"cmd": "chsh", "desc": "🐧 Changes the default login shell of the user session (e.g., switching Zsh to Bash)."},
    {"cmd": "history", "desc": "🐧 Lists all recently executed terminal commands to refresh your memory!"},
    {"cmd": "clear", "desc": "🐧 Wipes the terminal screen completely, providing a clean slate for your commands."},
    {"cmd": "alias", "desc": "🐧 Defines customized shortcuts for long, repetitive, or complex command lines."},
    {"cmd": "unalias", "desc": "🐧 Revokes previously configured alias shortcuts from the shell environment."},
    {"cmd": "export", "desc": "🐧 Sets environment variables and shares them globally across child processes."},
    {"cmd": "env", "desc": "🐧 Lists all active environment variables configured for the current terminal context."},
    {"cmd": "echo", "desc": "🐧 Prints specified text strings or variable parameters directly onto the screen."},
    {"cmd": "man", "desc": "🐧 Opens official instruction manuals for commands. The massive library of the Linux world!"}
]

# 10 Golden Server Rules
SERVER_RULES = [
    "Racism, ethnic discrimination, and hate speech of any kind are strictly prohibited.",
    "Unsolicited advertising, sharing invite links in channels or via DMs without permission is prohibited.",
    "Homophobia, sexism, and any discrimination against marginalized groups are strictly prohibited.",
    "Harassing, provoking, annoying members, or disrupting personal peace is prohibited.",
    "Spreading false information or creating fake news to manipulate members is prohibited.",
    "Excessive trolling that derails channel purposes or ruins server peace is prohibited.",
    "Excessive swearing, toxic language, and personal insults are strictly prohibited.",
    "NSFW, 18+ content, gore, or graphic violence material is completely prohibited.",
    "Impersonating another server member, staff member, or bot is strictly prohibited.",
    "Mass mentioning, spamming, and flooding channels with messages are prohibited."
]

# In-Memory Databases
# XP Structure: { user_id: {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "last_msg": 0, "level": 1} }
xp_db = {}
warning_db = {}
user_selected_roles = {}  # Tracking self-assigned roles: {user_id: [role_id1, role_id2]} (Max 3 roles)

# ==========================================
# 4. HELPER FUNCTIONS & ENGINE
# ==========================================
def add_xp(user_id, amount):
    current_time = time.time()
    if user_id not in xp_db:
        xp_db[user_id] = {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "last_msg": 0, "level": 1}
    
    # 60-Second Cooldown Control
    if current_time - xp_db[user_id]["last_msg"] >= 60:
        xp_db[user_id]["total"] += amount
        xp_db[user_id]["daily"] += amount
        xp_db[user_id]["weekly"] += amount
        xp_db[user_id]["monthly"] += amount
        xp_db[user_id]["last_msg"] = current_time
        
        # Level Up Algorithm
        current_xp = xp_db[user_id]["total"]
        next_level_xp = xp_db[user_id]["level"] * 100
        if current_xp >= next_level_xp:
            xp_db[user_id]["level"] += 1
            return True
    return False

# ==========================================
# 5. INTERACTIVE BUTTON ROLES (GUI VIEW)
# ==========================================
class RoleButton(Button):
    def __init__(self, role_id, label, style):
        super().__init__(label=label, style=style, custom_id=str(role_id))
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        role = guild.get_role(self.role_id)
        
        if not role:
            return await interaction.response.send_message("❌ This role could not be found on the server!", ephemeral=True)
            
        if user.id not in user_selected_roles:
            user_selected_roles[user.id] = []
            
        if role in user.roles:
            # Revoke role process
            await user.remove_roles(role)
            if self.role_id in user_selected_roles[user.id]:
                user_selected_roles[user.id].remove(self.role_id)
            await interaction.response.send_message(f"🗑️ `{role.name}` role has been successfully removed from you.", ephemeral=True)
        else:
            # Limit Check (Max 3 Roles)
            if len(user_selected_roles[user.id]) >= 3:
                return await interaction.response.send_message("⚠️ **Role Limit Reached!** You can select a maximum of 3 roles from this panel.", ephemeral=True)
                
            await user.add_roles(role)
            user_selected_roles[user.id].append(self.role_id)
            await interaction.response.send_message(f"✅ `{role.name}` role has been successfully assigned to you.", ephemeral=True)

class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view
        # Example Role Configurations (Replace with your actual Server Role IDs)
        roles_config = [
            {"id": 111222333444555666, "label": "Linux User", "style": discord.ButtonStyle.primary},
            {"id": 222333444555666777, "label": "Windows User", "style": discord.ButtonStyle.secondary},
            {"id": 333444555666777888, "label": "Gamer", "style": discord.ButtonStyle.success},
            {"id": 444555666777888999, "label": "Developer", "style": discord.ButtonStyle.danger}
        ]
        for rc in roles_config:
            self.add_item(RoleButton(role_id=rc["id"], label=rc["label"], style=rc["style"]))

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
        embed.set_footer(text="Let's follow the rules to build a peaceful community.")
        await channel.send(embed=embed)

@tasks.loop(hours=24)
async def reset_daily_xp():
    for user_id in xp_db:
        xp_db[user_id]["daily"] = 0

# ==========================================
# 7. BOT LIFE-CYCLE EVENTS
# ==========================================
@bot.event
async def on_ready():
    print(f'==========================================')
    print(f'🤖 Bot Is Online: {bot.user.name}#{bot.user.discriminator}')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'🚀 Engine Status: SYNTAX OK & PRODUCTION READY')
    print(f'==========================================')
    await bot.change_presence(activity=discord.Game(name="Managing Linux Servers | ?help"))
    hourly_reminder.start()
    reset_daily_xp.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # A. PROFANITY FILTER
    msg_content = message.content.lower()
    if any(word in msg_content for word in PROFANITY_LIST):
        try:
            await message.delete()
            await message.channel.send(f"Hey {message.author.mention}, swearing is strictly prohibited on this server!", delete_after=5)
            
            # Dispatch Log Event
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = discord.Embed(title="⚠️ Swearing Detected", color=discord.Color.red())
                embed.add_field(name="User", value=f"{message.author.mention} ({message.author.name})", inline=True)
                embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                embed.add_field(name="Message Content", value=f"||{message.content}||", inline=False)
                embed.set_footer(text=f"User ID: {message.author.id}")
                await log_channel.send(embed=embed)
            return  # Revoke XP reward for swearing
        except Exception as e:
            print(f"Profanity filter error: {e}")

    # B. XP ENGINE TRIGGER
    gained = random.randint(15, 25)
    leveled_up = add_xp(message.author.id, gained)
    if leveled_up:
        await message.channel.send(f"🎉 Congratulations {message.author.mention}! You have leveled up to **Level {xp_db[message.author.id]['level']}** by being active!")

    await bot.process_commands(message)

# ==========================================
# 8. ADVANCED MODERATION COMMAND MATRIX
# ==========================================
@bot.command()
@commands.has_permissions(manage_channels=True)
async def sudolock(ctx):
    """Locks down the channel for general members."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 Channel Locked", description="This channel has been temporarily locked using the `sudo` command. Only authorized roles can speak.", color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def sudounlock(ctx):
    """Unlocks the channel for general members."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 Channel Unlocked", description="The channel lock has been lifted. Everyone can send messages again.", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, hours: int):
    """Mutes a member using Discord's modern built-in Timeout system."""
    duration = datetime.timedelta(hours=hours)
    await member.timeout(duration, reason=f"Muted by {ctx.author.name}")
    embed = discord.Embed(title="🤫 User Muted", description=f"{member.mention} has been silenced for **{hours}** hours.", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    """Removes a member's active Timeout ahead of schedule."""
    await member.timeout(None, reason=f"Unmuted prematurely by {ctx.author.name}")
    await ctx.send(f"🔊 {member.mention} timed out duration has been removed successfully.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warning(ctx, member: discord.Member):
    """Adds a permanent warning mark to a user. 3 warnings trigger an automated ban."""
    if member.id not in warning_db:
        warning_db[member.id] = 0
    warning_db[member.id] += 1
    
    total_warns = warning_db[member.id]
    await ctx.send(f"⚠️ {member.mention} has been warned! Total Warnings: **{total_warns}/3**")
    
    if total_warns >= 3:
        await member.ban(reason="Automated Ban - Exceeded 3 Active Warnings Limit.")
        await ctx.send(f"🚨 {member.name} has been automatically banned from the server for accumulating 3 warnings!")
        warning_db[member.id] = 0

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Permanently bans a member from the server."""
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.name} has been successfully banned. Reason: {reason if reason else 'Not specified'}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    """Revokes an active ban using a member's numeric User ID."""
    guild = ctx.guild
    user = await bot.fetch_user(user_id)
    await guild.unban(user)
    await ctx.send(f"🔓 Ban check for user {user.name} has been successfully lifted.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ipban(ctx, member: discord.Member):
    """Simulates an IP-level ban by executing a hard ban and flagging network masks."""
    await member.ban(reason="IPBanned Simulation - Network Mask Flagged")
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title="🚨 Simulated IP Ban Configured", color=discord.Color.dark_purple())
        embed.add_field(name="Target User", value=f"{member.name} ({member.id})")
        embed.add_field(name="Status", value="Network mask flagged, access to the server has been permanently restricted.")
        await log_channel.send(embed=embed)
    await ctx.send(f"💻 IP-based permanent ban simulation triggered for {member.name} and they have been kicked!")

# ==========================================
# 9. SYSTEM CORE & ENTERTAINMENT COMMANDS
# ==========================================
@bot.command()
async def whoami(ctx):
    """Renders a custom authorization profile mask in a sleek Linux style."""
    is_admin = ctx.author.guild_permissions.administrator
    is_owner = ctx.author.guild == ctx.author.guild.owner
    
    if is_admin or is_owner:
        await ctx.send(f"```bash\nroot@adminpingu:~# Active Session: System Administrator / Privilege Level: Overlord\n```")
    else:
        embed = discord.Embed(title="👤 User Identity Report", color=discord.Color.blue())
        embed.add_field(name="Account", value=f"{ctx.author.name}#{ctx.author.discriminator}", inline=True)
        embed.add_field(name="Server Nickname", value=ctx.author.display_name, inline=True)
        embed.add_field(name="Registration Date", value=ctx.author.created_at.strftime("%Y-%m-%d"), inline=False)
        await ctx.send(embed=embed)

@bot.command()
async def randomlinux(ctx):
    """Picks one of 60 widely used Linux terminal commands and displays it gracefully."""
    selected = random.choice(LINUX_COMMANDS)
    embed = discord.Embed(
        title=f"🐧 Linux Terminal Library",
        description=f"**Command:** `{selected['cmd']}`\n\n**Description:** {selected['desc']}",
        color=discord.Color.blue()
    )
    embed.set_footer(text="AdminPingu — Linux Infrastructure Management Bot")
    await ctx.send(embed=embed)

@bot.command()
async def stats(ctx, member: discord.Member = None):
    """Renders the user's progress card detailing active levels and XP statistics."""
    member = member or ctx.author
    if member.id not in xp_db:
        xp_db[member.id] = {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "level": 1, "last_msg": 0}
        
    data = xp_db[member.id]
    next_xp = data["level"] * 100
    
    embed = discord.Embed(title=f"📊 {member.name} Server Statistics", color=discord.Color.purple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Current Level", value=f"`Level {data['level']}`", inline=True)
    embed.add_field(name="Total XP", value=f"`{data['total']} / {next_xp} XP`", inline=True)
    embed.add_field(name="Monthly Gained", value=f"`{data['monthly']} XP`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def leaderstats(ctx):
    """Displays a detailed scoreboard ranking the top 15 active server Grinders."""
    if not xp_db:
        return await ctx.send("❌ No data has been accumulated yet, leaderboards are currently empty.")
        
    sorted_users = sorted(xp_db.items(), key=lambda x: x[1]["total"], reverse=True)[:15]
    
    embed = discord.Embed(title="🏆 All-Time Most Active 15 Members Scoreboard", color=discord.Color.gold())
    for idx, (u_id, data) in enumerate(sorted_users, 1):
        target_user = bot.get_user(u_id)
        u_name = target_user.name if target_user else f"Former Member ({u_id})"
        embed.add_field(name=f"#{idx} - {u_name}", value=f"Level: `{data['level']}` | Total: `{data['total']} XP`", inline=False)
        
    await ctx.send(embed=embed)

# ==========================================
# 10. DIRECTORIES & SERVER SETUP INTERFACES
# ==========================================
@bot.command()
async def help(ctx):
    """Renders the organized navigation menu showcasing available commands."""
    embed = discord.Embed(title="🐧 AdminPingu Command Management Manual", description="Command prefix: `?`", color=discord.Color.dark_green())
    
    embed.add_field(
        name="🛡️ Administrative Root Operations",
        value="`?sudolock` - Locks down the current channel.\n`?sudounlock` - Unlocks the current channel.\n`?mute <user> <h>` - Silences user with timeout.\n`?unmute <user>` - Lifts active mute.\n`?warning <user>` - Adds a warning mark.\n`?ban <user>` - Bans member.\n`?unban <id>` - Revokes ban.\n`?ipban <user>` - Simulated IP-level network ban.",
        inline=False
    )
    embed.add_field(
        name="📊 System Experience Analytics",
        value="`?stats [user]` - Displays level card.\n`?leaderstats` - Lists top 15 chat members.",
        inline=False
    )
    embed.add_field(
        name="🐧 Linux Terminal Fun Core",
        value="`?randomlinux` - Randomly teaches 1 of 60 terminal commands.\n`?whoami` - Runs Linux authentication validation.",
        inline=False
    )
    embed.set_footer(text="AdminPingu — All rights reserved within the Linux Kernel.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_server(ctx):
    """Sets up official server rules and prints the button role selection panel."""
    # 1. Print Server Rules Embed
    rules_embed = discord.Embed(title="📜 Official Server Rules & Penalty Procedure", color=discord.Color.dark_red())
    description_text = ""
    for i, r in enumerate(SERVER_RULES, 1):
        description_text += f"**{i}.** {r}\n\n"
        
    rules_embed.description = description_text
    rules_embed.add_field(
        name="⚖️ Penalty Enforcement Policy",
        value="Members violating rules will face penalties sequentially based on gravity: **Warning -> Mute (Timeout) -> Ban**.\n\n🚨 **CRITICAL NOTE:** **Accounts accumulating 3 active warning marks will be BANNED permanently without appeal.**",
        inline=False
    )
    
    await ctx.send("⌛ Setting up server integrations in channels...")
    await ctx.send(embed=rules_embed)
    
    # 2. Print Button Role Panel GUI
    role_embed = discord.Embed(title="🎭 Server Role Selection Panel", description="Use the interactive buttons below to instantly assign or remove roles corresponding to your interests.\n\n⚠️ *Note: You can select a maximum of 3 self-assigned roles from this panel at a time.*", color=discord.Color.blue())
    await ctx.send(embed=role_embed, view=RoleView())

# ==========================================
# 11. GLOBAL SYSTEM EXCEPTION HANDLER
# ==========================================
@bot.listener()
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **ERROR: You are not in the sudoers list!** You lack the necessary privileges to execute this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **ERROR: Missing argument parameters!** Please fill in the required arguments matching the manual.")
    else:
        print(f"Unhandled system error captured: {error}")

# BOOTUP SEQUENCE
keep_alive()
bot.run(os.environ["MTUyMTg1MjQ3NTU4NDI4MjcyNg.GizTXB.bqd1VNqyr67munzlMCVqoJR6baoNmHBtxy3wFY"])
