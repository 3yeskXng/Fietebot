import json
import os
from datetime import datetime

# Log-Datei Pfad
log_file = "/home/user/Fietebot/log.log"

# Benutzerrechte
admins = ['eyesking']  # Owner
moderators = ['juliandergamer']  # Moderator

# Daten für Warnsystem
warnings_file = "/home/user/Fietebot/warnings.json"

# Lade vorhandene Warnungen
if os.path.exists(warnings_file):
    with open(warnings_file, 'r') as f:
        warnings = json.load(f)
else:
    warnings = {}

# Logging-Funktion
def log_action(action, user, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {user}: {action} - {details}\n"
    
    with open(log_file, 'a') as f:
        f.write(log_entry)

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
    
    # Speichern in der Datei
    with open(warnings_file, 'w') as f:
        json.dump(warnings, f, indent=4)
    
    return f"Warnung für {target} wurde erstellt."

# Funktion zum Annehmen oder Ablehnen von Warnungen (nur für den Owner)
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
        with open(warnings_file, 'w') as f:
            json.dump(warnings, f, indent=4)
        return f"Warnung für {target} wurde abgelehnt und gelöscht."
    else:
        return "Ungültige Aktion. Bitte 'annehmen' oder 'ablehnen' verwenden."

# Funktion zum Ansehen eigener Warnungen (für jeden Benutzer)
def view_warnings(user):
    if user in warnings:
        user_warning = warnings[user]
        return f"Warnung: {user_warning['reason']} - Ausgestellt von: {user_warning['issued_by']} am {user_warning['timestamp']}"
    else:
        return f"{user}, du hast keine Warnungen."
