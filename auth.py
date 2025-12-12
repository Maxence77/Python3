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

# --- CRYPTOGRAPHIE ---

def generate_salt():
    """
    Génère un sel de 32 caractères hexadécimaux.
    """
    return secrets.token_hex(16)

def hash_with_salt(password, salt):
    """
    Hache le mélange (Salt + Password).
    """
    # On concatène le sel et le mdp AVANT de hacher
    combined = salt + password
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def check_pwned_api(password):
    """Vérification API HaveIBeenPwned (SHA-1)"""
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
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

# --- GESTION DES UTILISATEURS ---

def load_users():
    # ICI : On définit STRICTEMENT 3 colonnes. Pas de colonne Salt.
    if not os.path.exists(USERS_FILE):
        df = pd.DataFrame(columns=["Username", "Password", "Compromised"])
        df.to_csv(USERS_FILE, index=False)
        return df
    return pd.read_csv(USERS_FILE)

def create_user(username, password):
    df = load_users()
    if username in df["Username"].values or username == "admin":
        return "EXIST"

    # 1. API Check
    pwned_count = check_pwned_api(password)
    is_compromised = "Oui" if pwned_count > 0 else "Non"

    # 2. Préparation Salt + Hash
    salt = generate_salt()                # 32 chars
    hashed_pw = hash_with_salt(password, salt) # 64 chars
    
    # 3. FUSION : On colle tout ensemble
    # La variable 'full_string' contient : [32 chars de sel][64 chars de hash]
    full_string = salt + hashed_pw

    # 4. Sauvegarde dans la colonne 'Password'
    new_row = pd.DataFrame([{
        "Username": username, 
        "Password": full_string,  # <-- C'est ici que Salt et Hash sont collés
        "Compromised": is_compromised
    }])
    
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USERS_FILE, index=False)
    
    return pwned_count

def check_login(username, password):
    if username == "admin" and password == "admin":
        return "OK"

    df = load_users()
    if username in df["Username"].values:
        record = df[df["Username"] == username].iloc[0]
        stored_value = str(record["Password"]) # Contient Salt+Hash collés

        # Vérification longueur mini (32 salt + 64 hash = 96)
        if len(stored_value) < 96:
            return "FAIL"

        # DÉCOUPAGE
        # Les 32 premiers caractères SONT le sel
        extracted_salt = stored_value[:32]
        # Le reste EST le hash
        extracted_hash = stored_value[32:]

        # On re-calcule avec le mdp saisi et le sel qu'on vient d'extraire
        calculated_hash = hash_with_salt(password, extracted_salt)

        if calculated_hash == extracted_hash:
            # Login OK
            pwned_count = check_pwned_api(password)
            status = "Oui" if pwned_count > 0 else "Non"
            
            idx = df.index[df["Username"] == username].tolist()[0]
            if df.at[idx, "Compromised"] != status:
                df.at[idx, "Compromised"] = status
                df.to_csv(USERS_FILE, index=False)

            if pwned_count > 0:
                return "COMPROMISED"
            return "OK"

    return "FAIL"

def change_password(username, new_password):
    df = load_users()
    idx = df.index[df["Username"] == username].tolist()
    
    if idx:
        i = idx[0]
        pwned_count = check_pwned_api(new_password)
        
        # Nouveau Salt + Nouveau Hash
        new_salt = generate_salt()
        new_hashed = hash_with_salt(new_password, new_salt)
        
        # On recolle
        full_string = new_salt + new_hashed
        
        df.at[i, "Password"] = full_string
        df.at[i, "Compromised"] = "Oui" if pwned_count > 0 else "Non"
        df.to_csv(USERS_FILE, index=False)
        return pwned_count
    return -1

def delete_user(username):
    df = load_users()
    if username != "admin":
        df = df[df["Username"] != username]
        df.to_csv(USERS_FILE, index=False)