import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import openai
import requests
import random
from datetime import datetime, timedelta

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix=('!', 'Fiete '), intents=intents)

# Set your OpenAI API key
openai.api_key = ""

# JSON-Datei zum Speichern der Benutzerdaten
user_data = {}

# Helper function to save user data
def save_user_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f, indent=4)

# Load user data from JSON
def load_user_data():
    global user_data
    if os.path.exists('user_data.json'):
        try:
            with open('user_data.json', 'r') as f:
                file_content = f.read().strip()
                if file_content:  # Check if file is not empty
                    user_data = json.loads(file_content)
                else:
                    user_data = {}
        except json.JSONDecodeError:
            print("Warnung: Fehler beim Laden der Benutzerdaten. Die Datei scheint beschädigt zu sein.")
            user_data = {}

# Daten beim Start des Bots laden
load_user_data()

# Function to log actions in user_data.json
def log_action(action, user, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "action": action,
        "user": user,
        "details": details,
        "timestamp": timestamp
    }
    if "logs" not in user_data:
        user_data["logs"] = []
    user_data["logs"].append(log_entry)
    save_user_data()

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

    # Beleidigungsüberprüfung
    insults = ['Penis', 'Hurensohn', 'Idiot', 'Fick deine Mutter']  # Add more insults as needed
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

    # Spam detection and punishment
    if len(msg.content) > 500 or msg.content.lower().count('spam') > 10:
        try:
            timeout_duration = timedelta(minutes=1)
            until = discord.utils.utcnow() + timeout_duration
            await msg.author.timeout(until, reason="Spam detected.")
            log_action("timeout", msg.author.name, "Spam erkannt.")
            await msg.channel.send(f"{msg.author.name} wurde für 1 Minute stummgeschaltet. Grund: Spam.")
        except Exception as e:
            await msg.channel.send(f"Fehler beim Timeout: {str(e)}")
            log_action("timeout_error", msg.author.name, f"Fehler beim Timeout: {str(e)}")

    # Meme Command
    if 'meme' in msg.content.lower():
        response = requests.get("https://meme-api.com/gimme")
        if response.status_code == 200:
            json_data = json.loads(response.text)
            if json_data.get("url"):
                log_action("meme", msg.author.name, f"Meme abgerufen: {json_data.get('url')}")
                await msg.channel.send(json_data.get("url"))
            else:
                await msg.channel.send("Konnte kein Meme abrufen. Keine URL in der Antwort gefunden.")
        else:
            await msg.channel.send("Konnte kein Meme abrufen. Bitte später erneut versuchen.")

    # Chat-GPT Aktivierung
    user_id = str(msg.author.id)
    if user_id in user_data and user_data[user_id].get('gpt', False):
        if not msg.content.startswith(('!', 'Fiete ')):  # Keine Befehle verarbeiten
            try:
                # Use OpenAI API for generating response
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": msg.content}
                    ]
                )
                reply = response['choices'][0]['message']['content']
                await msg.channel.send(reply)
            except Exception as e:
                await msg.channel.send(f"Fehler beim Verarbeiten der Nachricht: {str(e)}")

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
    - Fiete meme: Holt ein zufälliges Meme.
    - Fiete gpt-on: Aktiviert den Chat-GPT Modus.
    - Fiete gpt-off: Deaktiviert den Chat-GPT Modus.
    - Fiete deactivate: Deaktiviert den Bot (nur für Admins).
    - Fiete activate: Aktiviert den Bot.
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

# Chat-GPT Activation commands
@bot.command(name='gpt-on')
async def activate_gpt(ctx):
    user_id = str(ctx.author.id)
    user_data[user_id] = user_data.get(user_id, {})
    user_data[user_id]['gpt'] = True
    save_user_data()
    await ctx.send(f"{ctx.author.name}, GPT-Modus aktiviert.")

@bot.command(name='gpt-off')
async def deactivate_gpt(ctx):
    user_id = str(ctx.author.id)
    user_data[user_id] = user_data.get(user_id, {})
    user_data[user_id]['gpt'] = False
    save_user_data()
    await ctx.send(f"{ctx.author.name}, GPT-Modus deaktiviert.")

# Bot Activation/Deactivation commands (Admin only)
@bot.command(name='activate')
@commands.has_permissions(administrator=True)
async def activate_bot(ctx):
    await ctx.send("Bot wurde aktiviert.")

@bot.command(name='deactivate')
@commands.has_permissions(administrator=True)
async def deactivate_bot(ctx):
    await ctx.send("Bot wird deaktiviert.")
    await bot.close()

# Bot starten
bot.run(#Discord Token hier eingeben))
