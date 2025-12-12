import pandas as pd
import os

CSV_FOLDER = "csv"
USERS_FILE = os.path.join(CSV_FOLDER, "users.csv")

if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)

def load_users():
    if not os.path.exists(USERS_FILE):
        df = pd.DataFrame(columns=["Username", "Password"])
        df.to_csv(USERS_FILE, index=False)
        return df
    return pd.read_csv(USERS_FILE)

def create_user(username, password):
    df = load_users()
    if username in df["Username"].values or username == "admin":
        return False # Déjà existant
    new_row = pd.DataFrame([[username, password]], columns=["Username", "Password"])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USERS_FILE, index=False)
    return True

def check_login(username, password):
    # Backdoor Admin
    if username == "admin" and password == "admin":
        return True
    
    df = load_users()
    if username in df["Username"].values:
        record = df[df["Username"] == username].iloc[0]
        if str(record["Password"]) == str(password):
            return True
    return False

def delete_user(username):
    df = load_users()
    if username != "admin":
        df = df[df["Username"] != username]
        df.to_csv(USERS_FILE, index=False)