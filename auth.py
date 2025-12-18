import pandas as pd
import hashlib
import os
import requests
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-erp")

USER_DB = "csv/users.csv"
MSG_FILE = "csv/messages.csv"

def init_files():
    """Vérifie les fichiers et répare l'Admin si manquant."""
    if not os.path.exists("csv"):
        os.makedirs("csv")
    
    # --- GESTION UTILISATEURS ---
    admin_needed = False
    
    if not os.path.exists(USER_DB):
        admin_needed = True
    else:
        try:
            df = pd.read_csv(USER_DB)
            if "admin" not in df["Username"].values:
                admin_needed = True
            if "Admin" not in df.columns:
                admin_needed = True
        except:
            admin_needed = True

    if admin_needed:
        h_pw = hashlib.sha256("Admin@1234".encode()).hexdigest()
        try:
            old_df = pd.read_csv(USER_DB)
            if "Admin" not in old_df.columns: old_df["Admin"] = False
            admin_row = pd.DataFrame([["admin", h_pw, True, "Non"]], columns=["Username", "PasswordHash", "Admin", "Compromised"])
            df = pd.concat([old_df, admin_row], ignore_index=True)
        except:
            df = pd.DataFrame([["admin", h_pw, True, "Non"]], columns=["Username", "PasswordHash", "Admin", "Compromised"])
            
        df = df.drop_duplicates(subset=["Username"], keep='last')
        df.to_csv(USER_DB, index=False)

    # --- GESTION MESSAGES ---
    if not os.path.exists(MSG_FILE):
        pd.DataFrame(columns=["User", "Message"]).to_csv(MSG_FILE, index=False)

def load_users():
    init_files()
    try:
        return pd.read_csv(USER_DB)
    except:
        return pd.DataFrame(columns=["Username", "PasswordHash", "Admin", "Compromised"])

def create_user(username, password):
    df = load_users()
    if username in df["Username"].values:
        return "FAIL", "Utilisateur existe déjà"
    
    # --- AJOUT : Vérification API à la création ---
    if check_password_leak_api(password):
        return "FAIL", "Mot de passe COMPROMIS (détecté par API) ! Choisissez-en un autre."
    # ----------------------------------------------
    
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    new_user = pd.DataFrame([[username, hashed_pw, False, "Non"]], columns=["Username", "PasswordHash", "Admin", "Compromised"])
    
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_DB, index=False)
    return "SUCCESS", "Compte créé avec succès"

def authenticate_user(username, password):
    df = load_users()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    user_row = df[df["Username"] == username]
    
    if not user_row.empty:
        stored_pw = str(user_row.iloc[0]["PasswordHash"]).strip()
        
        if stored_pw == hashed_pw:
            is_admin_val = user_row.iloc[0]["Admin"]
            is_admin = str(is_admin_val).lower() in ['true', '1', 'yes']
            
            # --- AJOUT : Vérification API à la connexion ---
            # On vérifie si le mot de passe est pwned même si le login est bon
            if check_password_leak_api(password):
                # On retourne un statut spécial "WARNING" au lieu de "SUCCESS"
                return "WARNING", is_admin, JWT_SECRET
            # -----------------------------------------------

            return "SUCCESS", is_admin, JWT_SECRET
            
    return "FAIL", False, None

# --- CHECK API ---
def check_password_leak_api(password):
    """Vérifie si le mot de passe est dans la base de données des piratages."""
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1_password[:5], sha1_password[5:]
    
    try:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            hashes = (line.split(':') for line in response.text.splitlines())
            for h, count in hashes:
                if h == suffix:
                    return True # Le mot de passe EST compromis
    except:
        pass # Si pas d'internet, on laisse passer (ou on bloque, au choix)
    return False

def change_password(username, new_password):
    # 1. Vérification API
    if check_password_leak_api(new_password):
        return "FAIL", "Mot de passe COMPROMIS (détecté par API) ! Choisissez plus complexe."
    
    # 2. Modification dans le CSV
    df = load_users()
    if username in df["Username"].values:
        idx = df.index[df["Username"] == username][0]
        
        # On hash le nouveau mdp
        df.at[idx, "PasswordHash"] = hashlib.sha256(new_password.encode()).hexdigest()
        # On remet le statut "Compromised" à "Non" car il vient d'être changé
        df.at[idx, "Compromised"] = "Non"
        
        df.to_csv(USER_DB, index=False)
        return "SUCCESS", "Votre mot de passe a été mis à jour et sécurisé."
        
    return "FAIL", "Utilisateur introuvable"

# --- ADMIN ---

def toggle_admin_status(username):
    if username == "admin": return False, "Impossible de modifier le Super Admin"
    df = load_users()
    if username in df["Username"].values:
        idx = df.index[df["Username"] == username][0]
        current = df.at[idx, "Admin"]
        new_status = not (str(current).lower() in ['true', '1', 'yes'])
        df.at[idx, "Admin"] = new_status
        df.to_csv(USER_DB, index=False)
        msg = "Promu Admin" if new_status else "Rétrogradé User"
        return True, msg
    return False, "User introuvable"

def delete_user(username):
    if username == "admin": return False
    df = load_users()
    if username in df["Username"].values:
        df = df[df["Username"] != username]
        df.to_csv(USER_DB, index=False)
        return True
    return False

def send_message(target_user, message):
    try: df = pd.read_csv(MSG_FILE)
    except: df = pd.DataFrame(columns=["User", "Message"]) 
    new_msg = pd.DataFrame([[target_user, message]], columns=["User", "Message"])
    df = pd.concat([df, new_msg], ignore_index=True)
    df.to_csv(MSG_FILE, index=False)

def get_user_messages(username):
    try: df = pd.read_csv(MSG_FILE)
    except: return []
    if df.empty: return []
    msgs = df[df["User"] == username]["Message"].tolist()
    if msgs:
        df = df[df["User"] != username]
        df.to_csv(MSG_FILE, index=False)
    return msgs