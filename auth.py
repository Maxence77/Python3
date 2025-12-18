"""
Module d'authentification.

Gère la vérification des compromissions de mots de passe (HaveIBeenPwned)
et l'authentification des administrateurs via variables d'environnement.
"""

import hashlib
import os
import requests
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis le fichier .env
load_dotenv()

def check_pwned_api(password_clear):
    """
    Vérifie si un mot de passe a été compromis via l'API HaveIBeenPwned.

    Args:
        password_clear (str): Le mot de passe en clair à vérifier.

    Returns:
        int: Le nombre de fois que le mot de passe a été vu dans des fuites de données.
    """
    # Hachage en SHA-1 requis par l'API (ignorer l'alerte de sécurité B324)
    sha1password = hashlib.sha1(password_clear.encode('utf-8')).hexdigest().upper()  # nosec
    first5_char, tail = sha1password[:5], sha1password[5:]
    url = f"https://api.pwnedpasswords.com/range/{first5_char}"
    try:
        # Timeout ajouté pour éviter que le programme ne bloque indéfiniment
        res = requests.get(url, timeout=5)
        res.raise_for_status()
    except requests.RequestException:
        # En cas d'erreur réseau, on assume 0 fuite pour ne pas bloquer l'app
        return 0

    hashes = (line.split(':') for line in res.text.splitlines())
    for h, count in hashes:
        if h == tail:
            return int(count)
    return 0


def authenticate_user(username, password_clear):
    """
    Authentifie un utilisateur ou un administrateur.

    Args:
        username (str): Le nom d'utilisateur.
        password_clear (str): Le mot de passe en clair.

    Returns:
        str: "OK" si authentifié, sinon None ou message d'erreur.
    """
    # 1. Vérification Administrateur (Sécurisée via .env)
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")

    # On s'assure que les variables existent avant de comparer
    if admin_user and admin_pass:
        if username == admin_user and password_clear == admin_pass:
            return "OK"
    return None
