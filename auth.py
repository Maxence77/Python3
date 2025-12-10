# auth.pyœ
import hashlib
import os
import requests 

SALT_SIZE = 16

def hash_password(password, salt=None):
    """Génère un hachage salé du mot de passe (SHA-256)."""
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    elif isinstance(salt, str):
        salt = bytes.fromhex(salt)

    hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    return salt.hex(), hashed_password

def verify_password(stored_salt, stored_hash, provided_password):
    """Vérifie si le mot de passe fourni correspond au hachage stocké."""
    _, provided_hash = hash_password(provided_password, stored_salt)
    return provided_hash == stored_hash

def check_pwned_password(password):
    """
    Vérifie le mot de passe via l'API Have I Been Pwned (HIBP).
    Utilise k-anonymity (envoi des 5 premiers caractères du hash seulement).
    """
    if not password:
        return 0
        
    sha1password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    first5_char = sha1password[:5]
    tail = sha1password[5:]
    url = 'https://api.pwnedpasswords.com/range/' + first5_char
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return -1 # Erreur API
            
        hashes = (line.split(':') for line in res.text.splitlines())
        for h, count in hashes:
            if h == tail:
                return int(count)
        return 0
    except requests.exceptions.RequestException:
        return -1 # Erreur Connexion