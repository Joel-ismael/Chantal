import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Ges-Projets Pro", page_icon="💻", layout="wide")

# --- LISTE DES LANGAGES ---
LANGAGES_LIST = ["Python", "JavaScript", "C++", "Java", "PHP", "Swift", "Kotlin", "Rust", "Go", "TypeScript", "C#", "Ruby", "AUTRE"]

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('ges_projets_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                phone TEXT, password TEXT, sex TEXT, pays TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, date TEXT, 
                nom_projet TEXT, langage TEXT, heures REAL, statut TEXT, 
                priorite TEXT, client TEXT, budget REAL, plateforme TEXT, 
                difficulte TEXT, deadline TEXT, notes TEXT)''')
    conn.commit()
    return conn, c

conn, c = init_db()

def hash_pwd(pwd): return hashlib.sha256(str.encode(pwd)).hexdigest()

if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

def main():
    if not st.session_state.auth:
        st.title("💻 Ges-Projets")
        tab1, tab2 = st.tabs(["Connexion", "Inscription"])
        with tab1:
            with st.form("login"):
                l_nom = st.text_input("Nom")
                l_pre = st.text_input("Prénom")
                l_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Se connecter"):
                    c.execute('SELECT * FROM users WHERE nom=? AND prenom=? AND password=?', (l_nom, l_pre, hash_pwd(l_pw)))
                    user = c.fetchone()
                    if user:
                        st.session_state.auth, st.session_state.user = True, list(user)
                        st.rerun()
                    else: st.error("Identifiants incorrects.")
    else:
        u_email = st.session_state.user[0]
        st.sidebar.title("🚀 KERIANE")
        st.sidebar.caption("Ges-Projets (Suivi de Projets & Productivité)")
        
        menu = st.sidebar.selectbox("Menu", ["Collecte de Données", "Déconnexion"])

        if menu == "Déconnexion":
            st.session_state.auth = False
            st.rerun()

        elif menu == "Collecte de Données":
            t_s, t_a, t_g = st.tabs(["📥 Saisie", "🥧 Analyse", "🛠️ Gestion"])

            with t_s:
                with st.form("saisie_p"):
                    p_nom = st.text_input("Nom du Projet")
                    col_l1, col_l2 = st.columns(2)
                    p_opt = col_l1.selectbox("Langage", LANGAGES_LIST)
                    p_custom = col_l2.text_input("Si AUTRE, spécifiez")
                    p_lang = p_custom if p_opt == "AUTRE" else p_opt
                    
                    c1, c2 = st.columns(2)
                    # Protection NumberBounds : min_value et conversion float
                    p_h = c1.number_input("Heures", min_value=0.0, value=0.0, step=0.1)
                    p_st = c2.selectbox("Statut", ["En attente", "En cours", "Terminé"])
                    
                    p_bud = st.number_input("Budget (FCFA)", min_value=0.0, value=0.0)
                    
                    if st.form_submit_button("Enregistrer"):
                        c.execute('''INSERT INTO projets (user_email, date, nom_projet, langage, heures, statut, budget) 
                                     VALUES (?,?,?,?,?,?,?)''',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), p_nom, p_lang, float(p_h), p_st, float(p_bud)))
                        conn.commit()
                        st.success("Projet enregistré !")

            with t_a:
                c.execute('SELECT langage, heures FROM projets WHERE user_email=?', (u_email,))
                df = pd.DataFrame(c.fetchall(), columns=["Langage", "Heures"])
                if not df.empty:
                    st.plotly_chart(px.pie(df, values='Heures', names='Langage', hole=0.4), use_container_width=True)
                else: st.info("Aucune donnée.")

            with t_g:
                c.execute('SELECT id, nom_projet FROM projets WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                if rows:
                    opt = {f"{r[1]}": r[0] for r in rows}
                    sel_id = opt[st.selectbox("Choisir un projet", list(opt.keys()))]
                    if st.button("Supprimer le projet"):
                        c.execute('DELETE FROM projets WHERE id=?', (sel_id,))
                        conn.commit()
                        st.rerun()

if __name__ == '__main__':
    main()