"""
Module GUI pour l'ERP Gestion - Groupe 3.
Gère l'interface utilisateur, le dashboard, les produits et les commandes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Imports locaux
import auth
import orders

class App(tk.Tk):
    """
    Interface graphique principale de l'ERP Gestion (Groupe 3).

    Cette classe gère le cycle de vie de l'application, de l'authentification 
    utilisateur à l'affichage des différents modules (Dashboard, Commandes, 
    Produits, Administration). Elle hérite de `tk.Tk`.

    Attributes:
        notebook (ttk.Notebook | None): Conteneur d'onglets principal de l'interface.
        current_user (str | None): Nom d'utilisateur de la session active.
        is_admin_session (bool): Indique si l'utilisateur connecté a des droits admin.
        editing_order_id (int | None): ID de la commande en cours de modification.
        bg_color (str): Code hexadécimal de la couleur d'arrière-plan de l'application.
    """
    def __init__(self):
        super().__init__()
        self.title("ERP Gestion - Groupe 3")
        self.geometry("1200x850")
        # --- INITIALISATION DES ATTRIBUTS (Correctif W0201) ---
        self.notebook = None
        self.current_user = None
        self.is_admin_session = False
        self.editing_order_id = None
        # ------------------------------------------------------
        style = ttk.Style()
        style.theme_use('clam')
        self.bg_color = "#f0f2f5"
        self.configure(bg=self.bg_color)
        self.show_login()

    def clear_window(self):
        """Nettoie tous les widgets de la fenêtre principale."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        """Affiche l'écran de connexion."""
        self.clear_window()
        frame = tk.Frame(self, bg="white", padx=40, pady=40, relief="raised")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="GROUPE3 ERP", font=("Arial", 18, "bold"), bg="white").pack(pady=20)

        self.inputs["user"] = ttk.Entry(frame, width=30)
        self.inputs["user"].pack(pady=5)
        self.inputs["pass"] = ttk.Entry(frame, width=30, show="*")
        self.inputs["pass"].pack(pady=5)

        tk.Button(frame, text="CONNEXION", bg="#2c3e50", fg="white",
                  command=self.perform_login).pack(pady=15, fill="x")

    def perform_login(self):
        """Exécute la logique de connexion."""
        user = self.inputs["user"].get()
        pwd = self.inputs["pass"].get()
        status, is_admin, _ = auth.authenticate_user(user, pwd)

        if status in ["SUCCESS", "WARNING"]:
            if status == "WARNING":
                messagebox.showwarning("Sécurité", "Mot de passe compromis !")
            self.session["user"] = user
            self.session["is_admin"] = is_admin
            self.show_main_interface()
        else:
            messagebox.showerror("Erreur", "Identifiants invalides")

    def show_main_interface(self):
        """Affiche l'interface principale avec les onglets."""
        self.clear_window()
        header = tk.Frame(self, bg="#2c3e50", height=60)
        header.pack(fill="x")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Initialisation des onglets dans le dictionnaire
        tab_names = ["Dashboard", "Commandes", "Produits", "Profil"]
        if self.session["is_admin"]:
            tab_names.append("ADMINISTRATION")

        for name in tab_names:
            self.tabs[name] = ttk.Frame(self.notebook)
            self.notebook.add(self.tabs[name], text=name)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self.load_dashboard_view()

    def _on_tab_change(self, _event):
        """Gère le rafraîchissement des données lors du changement d'onglet."""
        name = self.notebook.tab(self.notebook.select(), "text")
        loaders = {
            "Dashboard": self.load_dashboard_view,
            "Commandes": self.load_orders_view,
            "Produits": self.load_products_view,
            "ADMINISTRATION": self.load_admin_view
        }
        if name in loaders:
            loaders[name]()

    def load_dashboard_view(self):
        """Génère la vue Dashboard avec KPI et graphiques."""
        container = self.tabs["Dashboard"]
        for w in container.winfo_children():
            w.destroy()

        df = orders.load_orders()
        gf = tk.Frame(container, bg=self.ui_styles["bg"])
        gf.pack(fill="both", expand=True)

        if not df.empty and "Date" in df.columns:
            try:
                df['DateObj'] = pd.to_datetime(df['Date'], format="%d/%m/%Y", errors='coerce')
                df = df.dropna(subset=['DateObj']).sort_values(by="DateObj")
                fig, ax = plt.subplots(figsize=(5, 3))
                ax.plot(df['DateObj'], df['Prix Total'], marker='o')
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                canvas = FigureCanvasTkAgg(fig, master=gf)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
                plt.close(fig)
            except (ValueError, RuntimeError) as err:
                tk.Label(gf, text=f"Erreur d'affichage : {err}").pack()

    def load_orders_view(self):
        """Affiche la liste des commandes."""
        container = self.tabs["Commandes"]
        for w in container.winfo_children():
            w.destroy()

        cols = ("ID", "Produit", "Quantité", "Total")
        self.trees["orders"] = ttk.Treeview(container, columns=cols, show="headings")
        for c in cols:
            self.trees["orders"].heading(c, text=c)
        self.trees["orders"].pack(fill="both", expand=True)

        df = orders.load_orders()
        for _, r in df.iterrows():
            self.trees["orders"].insert("", "end", values=(r["ID"], r["Produit"],
                                                           r["Quantité"], r["Prix Total"]))

    def load_products_view(self):
        """Affiche la liste des produits avec toolbar."""
        container = self.tabs["Produits"]
        for w in container.winfo_children():
            w.destroy()

        toolbar = tk.Frame(container)
        toolbar.pack(fill="x")
        tk.Button(toolbar, text="Ajouter", command=self.pop_prod_add).pack(side="left")

        cols = ("Nom", "Prix", "Quantité")
        self.trees["prods"] = ttk.Treeview(container, columns=cols, show="headings")
        for c in cols:
            self.trees["prods"].heading(c, text=c)
        self.trees["prods"].pack(fill="both", expand=True)

    def pop_prod_add(self):
        """Ouvre la popup d'ajout."""
        self._open_prod_popup("Ajouter un produit", None)

    def _open_prod_popup(self, title, data_item):
        """Popup de gestion de produit."""
        win = tk.Toplevel(self)
        win.title(title)
        tk.Label(win, text=f"Saisie pour : {data_item if data_item else 'Nouveau'}").pack()

        def _save():
            win.destroy()
            self.load_products_view()

        tk.Button(win, text="Enregistrer", command=_save).pack()

    def load_admin_view(self):
        """Vue administration."""
        container = self.tabs["ADMINISTRATION"]
        for w in container.winfo_children():
            w.destroy()
        tk.Label(container, text="Gestion des utilisateurs").pack()

if __name__ == "__main__":
    App().mainloop()
