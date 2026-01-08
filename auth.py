"""
Module d'authentification et de gestion des utilisateurs pour l'ERP.
Gère le hachage, la vérification des fuites de mots de passe via API et l'admin.
"""

import hashlib
import os

import pandas as pd
import requests
from dotenv import load_dotenv

import re

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-erp")

USER_DB = "csv/users.csv"
MSG_FILE = "csv/messages.csv"


def validate_password_complexity(password):
    """
    Vérifie la sécurité du mot de passe selon des critères stricts.
    Retourne (bool, message).
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r'[A-Z]', password):
        return False, "Le mot de passe doit contenir au moins une majuscule."
    if not re.search(r'[a-z]', password):
        return False, "Le mot de passe doit contenir au moins une minuscule."
    if not re.search(r'[0-9]', password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."
    return True, "OK"


def init_files():
    """Vérifie l'existence des dossiers/fichiers et répare l'Admin si nécessaire."""
    if not os.path.exists("csv"):
        os.makedirs("csv")

    admin_needed = False

    if not os.path.exists(USER_DB):
        admin_needed = True
    else:
        try:
            df = pd.read_csv(USER_DB)
            if "admin" not in df["Username"].values or "Admin" not in df.columns:
                admin_needed = True
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            admin_needed = True

    if admin_needed:
        import secrets
        import string

        # Récupération du mot de passe Admin (depuis .env ou génération aléatoire)
        admin_pw = os.getenv("ADMIN_PASSWORD")
        
        if not admin_pw:
            alphabet = string.ascii_letters + string.digits + "!@#$%"
            admin_pw = "".join(secrets.choice(alphabet) for _ in range(16))
            print(f"\n[SECURITE] Mot de passe Admin généré : {admin_pw}")
            print("[INFO] Configurez ADMIN_PASSWORD dans .env pour le personnaliser.\n")

        h_pw = hashlib.sha256(admin_pw.encode()).hexdigest()
        cols = ["Username", "PasswordHash", "Admin", "Compromised"]
        try:
            old_df = pd.read_csv(USER_DB)
            if "Admin" not in old_df.columns:
                old_df["Admin"] = False
            admin_row = pd.DataFrame([["admin", h_pw, True, "Non"]], columns=cols)
            df = pd.concat([old_df, admin_row], ignore_index=True)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df = pd.DataFrame([["admin", h_pw, True, "Non"]], columns=cols)

        df = df.drop_duplicates(subset=["Username"], keep='last')
        df.to_csv(USER_DB, index=False)

    if not os.path.exists(MSG_FILE):
        pd.DataFrame(columns=["User", "Message"]).to_csv(MSG_FILE, index=False)


def load_users():
    """Charge la base de données utilisateur depuis le fichier CSV."""
    init_files()
    try:
        return pd.read_csv(USER_DB)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["Username", "PasswordHash", "Admin", "Compromised"])


def create_user(username, password):
    """Crée un nouvel utilisateur après vérification de sécurité."""
    df = load_users()
    if username in df["Username"].values:
        return "FAIL", "Utilisateur existe déjà"

    # Vérification de complexité
    is_complex, msg = validate_password_complexity(password)
    if not is_complex:
        return "FAIL", msg

    if check_password_leak_api(password):
        return "FAIL", "Mot de passe COMPROMIS ! Choisissez-en un autre."

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    cols = ["Username", "PasswordHash", "Admin", "Compromised"]
    new_user = pd.DataFrame([[username, hashed_pw, False, "Non"]], columns=cols)

    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_DB, index=False)
    return "SUCCESS", "Compte créé avec succès"


def authenticate_user(username, password):
    """Authentifie l'utilisateur et vérifie si le mot de passe est pwned."""
    df = load_users()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    user_row = df[df["Username"] == username]

    if not user_row.empty:
        stored_pw = str(user_row.iloc[0]["PasswordHash"]).strip()
        if stored_pw == hashed_pw:
            is_admin_val = user_row.iloc[0]["Admin"]
            is_admin = str(is_admin_val).lower() in ['true', '1', 'yes']

            if check_password_leak_api(password):
                return "WARNING", is_admin, JWT_SECRET
            return "SUCCESS", is_admin, JWT_SECRET

    return "FAIL", False, None


def check_password_leak_api(password):
    """Vérifie via l'API HaveIBeenPwned si le mot de passe a fuité."""
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1_password[:5], sha1_password[5:]

    try:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            hashes = (line.split(':') for line in response.text.splitlines())
            for h, _ in hashes:
                if h == suffix:
                    return True
    except (requests.exceptions.RequestException, ValueError):
        pass
    return False


def change_password(username, new_password):
    """Change le mot de passe d'un utilisateur existant."""
    # Vérification de complexité
    is_complex, msg = validate_password_complexity(new_password)
    if not is_complex:
        return "FAIL", msg

    if check_password_leak_api(new_password):
        return "FAIL", "Mot de passe COMPROMIS ! Choisissez plus complexe."

    df = load_users()
    if username in df["Username"].values:
        idx = df.index[df["Username"] == username][0]
        df.at[idx, "PasswordHash"] = hashlib.sha256(new_password.encode()).hexdigest()
        df.at[idx, "Compromised"] = "Non"
        df.to_csv(USER_DB, index=False)
        return "SUCCESS", "Votre mot de passe a été mis à jour."

    return "FAIL", "Utilisateur introuvable"


def toggle_admin_status(username):
    """Inverse le statut administrateur d'un utilisateur."""
    if username == "admin":
        return False, "Impossible de modifier le Super Admin"
    df = load_users()
    if username in df["Username"].values:
        idx = df.index[df["Username"] == username][0]
        current = df.at[idx, "Admin"]
        new_status = str(current).lower() not in ['true', '1', 'yes']
        df.at[idx, "Admin"] = new_status
        df.to_csv(USER_DB, index=False)
        msg = "Promu Admin" if new_status else "Rétrogradé User"
        return True, msg
    return False, "User introuvable"


def delete_user(username):
    """Supprime un utilisateur de la base CSV."""
    if username == "admin":
        return False
    df = load_users()
    if username in df["Username"].values:
        df = df[df["Username"] != username]
        df.to_csv(USER_DB, index=False)
        return True
    return False


def send_message(target_user, message):
    """Envoie un message persistant à un utilisateur."""
    try:
        df = pd.read_csv(MSG_FILE)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df = pd.DataFrame(columns=["User", "Message"])
    new_msg = pd.DataFrame([[target_user, message]], columns=["User", "Message"])
    df = pd.concat([df, new_msg], ignore_index=True)
    df.to_csv(MSG_FILE, index=False)


def get_user_messages(username):
    """Récupère et supprime les messages en attente pour un utilisateur."""
    try:
        df = pd.read_csv(MSG_FILE)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return []
    if df.empty:
        return []
    msgs = df[df["User"] == username]["Message"].tolist()
    if msgs:
        df = df[df["User"] != username]
        df.to_csv(MSG_FILE, index=False)
    return msgs
