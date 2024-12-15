import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from datetime import datetime, timedelta

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix=('!', 'Fiete '), intents=intents)

# Log-Datei Pfad
log_file = "/home/user/Fietebot/log.log"

# JSON-Datei zum Speichern der Benutzerdaten
user_data_file = '/home/user/Fietebot/user_data.json'
user_data = {}

# Verzeichnis für HTML und hochgeladene Dateien
html_directory = "/home/user/Fietebot/odb"

# Benutzerrechte
admins = ['eyesking']  # Owner
moderators = ['juliandergamer']  # Moderator

# Daten für Warnsystem
warnings_file = "/home/user/Fietebot/warnings.json"

# Logging-Funktion
def log_action(action, user, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {user}: {action} - {details}\n"
    
    with open(log_file, 'a') as f:
        f.write(log_entry)

# Lade Benutzerdaten
def load_user_data():
    global user_data
    if os.path.exists(user_data_file):
        with open(user_data_file, 'r') as f:
            user_data = json.load(f)

# Speichern der Benutzerdaten
def save_user_data():
    with open(user_data_file, 'w') as f:
        json.dump(user_data, f, indent=4)

# Lade Warnungen
def load_warnings():
    if os.path.exists(warnings_file):
        with open(warnings_file, 'r') as f:
            return json.load(f)
    else:
        return {}

# Speichern der Warnungen
def save_warnings(warnings):
    with open(warnings_file, 'w') as f:
        json.dump(warnings, f, indent=4)

# Start Logging und Laden der Daten
load_user_data()
warnings = load_warnings()

# Funktion zum Erstellen von Warnungen
def create_warning(issuer, target, reason):
    if issuer not in admins and issuer not in moderators:
        return f"{issuer}, du hast keine Berechtigung, Warnungen zu erstellen."
    
    warnings[target] = {
        "reason": reason,
        "issued_by": issuer,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    log_action("warning_created", issuer, f"Warnung für {target}: {reason}")
    
    save_warnings(warnings)
    return f"Warnung für {target} wurde erstellt."

# Funktion zum Annehmen oder Ablehnen von Warnungen
def manage_warning(issuer, target, action):
    if issuer not in admins:
        return f"{issuer}, nur der Owner kann Warnungen verwalten."
    
    if target not in warnings:
        return f"Keine Warnung gefunden für {target}."
    
    if action == "annehmen":
        log_action("warning_accepted", issuer, f"Warnung für {target}")
        return f"Warnung für {target} akzeptiert."
    elif action == "ablehnen":
        log_action("warning_rejected", issuer, f"Warnung für {target}")
        warnings.pop(target)
        save_warnings(warnings)
        return f"Warnung für {target} wurde abgelehnt und gelöscht."
    else:
        return "Ungültige Aktion. Bitte 'annehmen' oder 'ablehnen' verwenden."

# Funktion zum Ansehen eigener Warnungen
def view_warnings(user):
    if user in warnings:
        user_warning = warnings[user]
        return f"Warnung: {user_warning['reason']} - Ausgestellt von: {user_warning['issued_by']} am {user_warning['timestamp']}"
    else:
        return f"{user}, du hast keine Warnungen."

# !ban Command
@bot.command(name='ban')
async def ban_user(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(f"{ctx.author.mention}, willst du wirklich gebannt werden?")
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send("Zeitüberschreitung. Befehl abgebrochen.")
        return

    if msg.content.lower() == 'ja':
        await ctx.author.kick(reason="User hat sich selbst gebannt für 24 Stunden.")
        log_action("ban", ctx.author.name, "User hat sich selbst gebannt.")
        await ctx.send(f"{ctx.author.name} wurde für 24 Stunden gekickt.")
        await asyncio.sleep(86400)  # 24 Stunden
        await ctx.guild.unban(ctx.author)
    else:
        await ctx.send("Bann abgebrochen.")

# Anti-Beleidigung & Timeout statt Kick
@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return

    insults = ['Penis', 'Hurensohn', 'Idiot', 'Fick deine Mutter']
    if any(insult in msg.content.lower() for insult in insults):
        try:
            timeout_duration = timedelta(minutes=5)
            until = discord.utils.utcnow() + timeout_duration
            await msg.author.timeout(until, reason="Fiete wurde beleidigt.")
            log_action("timeout", msg.author.name, "Beleidigung erkannt.")
            await msg.channel.send(f"{msg.author.name} wurde für 5 Minuten stummgeschaltet. Grund: Fiete wurde beleidigt.")
        except Exception as e:
            await msg.channel.send(f"Fehler beim Timeout: {str(e)}")
            log_action("timeout_error", msg.author.name, f"Fehler beim Timeout: {str(e)}")

    await bot.process_commands(msg)

# Greeting command with memory
@bot.command(name='Hallo')
async def greet_user(ctx):
    user_id = str(ctx.author.id)
    if user_id not in user_data:
        await ctx.send("Hallo, ich bin Fiete. Wie heißt du?")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Zeitüberschreitung. Befehl abgebrochen.")
            return

        user_data[user_id] = {'name': msg.content}
        log_action("greet", ctx.author.name, f"Benutzername gespeichert: {msg.content}")
        save_user_data()
        await ctx.send(f"Hi {msg.content}, mein bester! Wie geht’s dir? Alte Socke!")
    else:
        await ctx.send(f"Hi {user_data[user_id]['name']}, mein bester! Wie geht’s dir? Alte Socke!")

# Help command to list all commands
@bot.command(name='commands')
async def help_command(ctx):
    commands_list = """
    **Verfügbare Befehle:**
    - !ban: Selbstbann für 24 Stunden.
    - Fiete Hallo: Begrüßung und Namenserinnerung.
    - Fiete commands: Zeigt diese Befehlsliste an.
    - Fiete game: Ein Zahlenraten-Spiel.
    - Fiete warn: Verwarnungen erstellen und verwalten.
    """
    await ctx.send(commands_list)

# Number guessing game
@bot.command(name='game')
async def guess_number(ctx):
    number = random.randint(1, 100)
    attempts = 0
    await ctx.send("Willkommen zum Zahlenraten! Ich habe mir eine Zahl zwischen 1 und 100 ausgedacht. Versuche sie zu erraten!")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

    while True:
        try:
            msg = await bot.wait_for('message', check=check, timeout=30.0)
            guess = int(msg.content)
            attempts += 1

            if guess < number:
                await ctx.send("Zu niedrig! Versuche es nochmal.")
            elif guess > number:
                await ctx.send("Zu hoch! Versuche es nochmal.")
            else:
                await ctx.send(f"Glückwunsch! Du hast die Zahl {number} nach {attempts} Versuchen erraten.")
                break
        except asyncio.TimeoutError:
            await ctx.send("Zeitüberschreitung. Spiel beendet.")
            break

# Cloud System: Hochladen und Anzeigen von Dateien
@bot.command(name='einzahlen')
async def upload_file(ctx):
    await ctx.send("Bitte sende die Datei, die du speichern möchtest.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.attachments

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
        file = msg.attachments[0]
        file_path = os.path.join(html_directory, file.filename)
        await file.save(file_path)
        await ctx.send(f"Datei {file.filename} wurde gespeichert. Soll sie privat oder öffentlich sein?")
        
        def check_public(m):
            return m.author == ctx.author and m.channel == ctx.channel

        msg_public = await bot.wait_for('message', check=check_public, timeout=30.0)
        
        if msg_public.content.lower() == "öffentlich":
            await ctx.send(f"Datei {file.filename} ist nun öffentlich zugänglich.")
        else:
            await ctx.send(f"Datei {file.filename} ist privat.")
        
        log_action("file_upload", ctx.author.name, f"{file.filename} wurde hochgeladen.")
        
    except asyncio.TimeoutError:
        await ctx.send("Zeitüberschreitung. Kein Upload erfolgt.")

# Running the bot
bot.run(#Please enter your Discord Token.)

