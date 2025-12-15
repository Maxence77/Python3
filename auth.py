import pandas as pd
import os
import hashlib
import requests
import secrets

# --- CONFIGURATION ---
CSV_FOLDER = "csv"
USERS_FILE = os.path.join(CSV_FOLDER, "users.csv")

if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)

# --- 1. OUTILS DE HACHAGE ---

def generate_salt():
    """Génère un sel de 32 caractères hexadécimaux."""
    return secrets.token_hex(16)

def compute_storage_hash(password_clear, salt):
    """
    Crée le hash pour le stockage (SHA-256).
    Algo : SHA-256( Salt + Password )
    """
    combined = salt + password_clear
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def compute_api_hash(password_clear):
    """
    Crée le hash pour l'API (SHA-1).
    Requis par l'API.
    """
    return hashlib.sha1(password_clear.encode('utf-8')).hexdigest().upper()

def check_pwned_api(password_clear):
    """
    Interroge l'API avec le préfixe SHA-1.
    """
    sha1 = compute_api_hash(password_clear)
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        r = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
        if r.status_code == 200:
            hashes = (line.split(':') for line in r.text.splitlines())
            for h, count in hashes:
                if h == suffix: return int(count)
    except:
        pass
    return 0

# --- 2. GESTION UTILISATEURS ---

def load_users():
    if not os.path.exists(USERS_FILE):
        # Toujours 3 colonnes : Password contient Salt+Hash
        df = pd.DataFrame(columns=["Username", "Password", "Compromised"])
        df.to_csv(USERS_FILE, index=False)
        return df
    return pd.read_csv(USERS_FILE)

def create_user(username, password_clear):
    df = load_users()
    if username in df["Username"].values or username == "admin":
        return "EXIST"

    # --- ÉTAPE 1 : HACHAGE POUR LE STOCKAGE (Ta demande) ---
    # On prépare d'abord ce qu'on va écrire dans la base de données
    salt = generate_salt()
    storage_hash = compute_storage_hash(password_clear, salt)
    
    # On colle le Salt et le Hash (32 chars + 64 chars)
    final_password_string = salt + storage_hash

    # --- ÉTAPE 2 : VÉRIFICATION API ---
    # On vérifie si ce mot de passe est connu des pirates
    pwned_count = check_pwned_api(password_clear)
    is_compromised = "Oui" if pwned_count > 0 else "Non"

    # --- ÉTAPE 3 : SAUVEGARDE ---
    new_row = pd.DataFrame([{
        "Username": username, 
        "Password": final_password_string, # On utilise le résultat de l'étape 1
        "Compromised": is_compromised
    }])
    
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USERS_FILE, index=False)
    
    return pwned_count

def check_login(username, password_clear):
    # Backdoor Admin
    if username == "admin" and password_clear == "admin":
        return "OK"

    df = load_users()
    if username in df["Username"].values:
        record = df[df["Username"] == username].iloc[0]
        stored_value = str(record["Password"])

        # Vérification format (32+64 = 96 min)
        if len(stored_value) < 96:
            return "FAIL"

        # 1. On récupère le sel qui est au début de la chaîne stockée
        extracted_salt = stored_value[:32]
        # 2. On récupère le hash qui est à la fin
        extracted_hash = stored_value[32:]

        # 3. On calcule le hash avec le mot de passe que l'utilisateur vient de taper
        calculated_hash = compute_storage_hash(password_clear, extracted_salt)

        # 4. Comparaison
        if calculated_hash == extracted_hash:
            # Le mot de passe est bon !
            
            # Maintenant, on vérifie l'API pour mettre à jour le statut
            pwned_count = check_pwned_api(password_clear)
            status = "Oui" if pwned_count > 0 else "Non"
            
            # Mise à jour CSV si le statut change
            idx = df.index[df["Username"] == username].tolist()[0]
            if df.at[idx, "Compromised"] != status:
                df.at[idx, "Compromised"] = status
                df.to_csv(USERS_FILE, index=False)

            if pwned_count > 0:
                return "COMPROMISED"
            return "OK"

    return "FAIL"

def change_password(username, new_password_clear):
    df = load_users()
    idx = df.index[df["Username"] == username].tolist()
    
    if idx:
        i = idx[0]
        
        # 1. Hachage Stockage
        new_salt = generate_salt()
        new_hash = compute_storage_hash(new_password_clear, new_salt)
        final_string = new_salt + new_hash
        
        # 2. Vérif API
        pwned_count = check_pwned_api(new_password_clear)
        
        # 3. Mise à jour
        df.at[i, "Password"] = final_string
        df.at[i, "Compromised"] = "Oui" if pwned_count > 0 else "Non"
        df.to_csv(USERS_FILE, index=False)
        return pwned_count
    return -1

def delete_user(username):
    df = load_users()
    if username != "admin":
        df = df[df["Username"] != username]
        df.to_csv(USERS_FILE, index=False)
