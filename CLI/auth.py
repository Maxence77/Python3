# auth.py
import hashlib
import os
import requests # Nécessite le module 'requests' [cite: 26]

# Taille du sel recommandée
SALT_SIZE = 16

def hash_password(password, salt=None):
    """
    Génère un hachage salé du mot de passe.
    Utilise SHA-256 et un sel aléatoire pour prévenir les attaques par force brute. [cite: 33, 38]
    """
    if salt is None:
        # Générer un sel aléatoire (bytes)
        salt = os.urandom(SALT_SIZE)
    elif isinstance(salt, str):
        # Convertir le sel en bytes s'il est fourni en tant que chaîne
        salt = bytes.fromhex(salt)

    # Le hachage est basé sur le sel + le mot de passe encodé
    hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()

    # Retourne le sel (en hexadécimal) et le hachage
    return salt.hex(), hashed_password

def verify_password(stored_salt, stored_hash, provided_password):
    """Vérifie si le mot de passe fourni correspond au hachage stocké."""
    # Re-hacher le mot de passe fourni avec le sel stocké
    _, provided_hash = hash_password(provided_password, stored_salt)
    return provided_hash == stored_hash

def check_pwned_password(password):
    """
    Vérifie si un mot de passe a été compromis en utilisant l'API HIBP. [cite: 15]
    Utilise le k-Anonymity (seul le préfixe du hachage est envoyé).
    """
    # 1. Hacher le mot de passe en SHA-1 (requis par l'API HIBP)
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1_password[:5] # Les 5 premiers caractères (préfixe)
    suffix = sha1_password[5:] # Le reste du hachage (suffixe)

    # 2. Requête à l'API HIBP
    HIBP_API_URL = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        response = requests.get(HIBP_API_URL)
        response.raise_for_status() # Lève une exception pour les codes d'état 4xx/5xx

        # 3. Analyser la réponse
        for line in response.text.splitlines():
            # Le format est "SUFFIXE:COMPTEUR"
            line_suffix, count = line.split(':')
            if line_suffix == suffix:
                return int(count) # Nombre de fois où le mot de passe a été vu
        
        return 0 # Non trouvé dans les fuites

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'accès à l'API HIBP : {e}")
        return -1 # Indicateur d'erreur

# --- Exemple d'utilisation (pour les tests) ---
# if __name__ == '__main__':
#     print("--- Test de Hachage ---")
#     salt, hashed = hash_password("MotDePasseTest123!")
#     print(f"Sel: {salt}\nHachage: {hashed}")
#     
#     is_valid = verify_password(salt, hashed, "MotDePasseTest123!")
#     print(f"Vérification réussie: {is_valid}") # Devrait être True
#
#     is_compromised = check_pwned_password("password")
#     print(f"\n--- Test HIBP ---")
#     print(f"Le mot de passe 'password' a été vu {is_compromised} fois.")