import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Ges-Projets Pro", page_icon="💻", layout="wide")

# --- DONNÉES PAYS ---
PAYS_DATA = {
    "Cameroun": {"code": "+237", "regex": r"^\d{9}$"},
    "France": {"code": "+33", "regex": r"^\d{9}$"},
    "Côte d'Ivoire": {"code": "+225", "regex": r"^\d{10}$"},
    "Sénégal": {"code": "+221", "regex": r"^\d{9}$"},
    "Canada": {"code": "+1", "regex": r"^\d{10}$"}
}

LANGAGES_LIST = ["Python", "JavaScript", "C++", "Java", "PHP", "Swift", "Kotlin", "Rust", "Go", "TypeScript", "C#", "Ruby", "AUTRE"]

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('ges_projets_final.db', check_same_thread=False)
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
        st.title("💻 Ges-Projets (Suivi de Performance)")
        tab_login, tab_signup = st.tabs(["Se Connecter", "S'inscrire"])

        with tab_login:
            with st.form("login"):
                l_nom = st.text_input("Nom")
                l_pre = st.text_input("Prénom")
                l_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Connexion"):
                    c.execute('SELECT * FROM users WHERE nom=? AND prenom=? AND password=?', (l_nom, l_pre, hash_pwd(l_pw)))
                    user = c.fetchone()
                    if user:
                        st.session_state.auth, st.session_state.user = True, list(user)
                        st.rerun()
                    else: st.error("Identifiants incorrects.")

        with tab_signup:
            with st.form("signup"):
                col1, col2 = st.columns(2)
                with col1:
                    s_nom, s_pre = st.text_input("Nom"), st.text_input("Prénom")
                    s_em, s_sex = st.text_input("Email"), st.selectbox("Sexe", ["Masculin", "Féminin"])
                with col2:
                    s_pa = st.selectbox("Nationalité", list(PAYS_DATA.keys()))
                    s_ph = st.text_input(f"Téléphone ({PAYS_DATA[s_pa]['code']})")
                    s_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Créer mon compte"):
                    if re.match(PAYS_DATA[s_pa]["regex"], s_ph):
                        try:
                            c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', (s_em, s_nom, s_pre, f"{PAYS_DATA[s_pa]['code']} {s_ph}", hash_pwd(s_pw), s_sex, s_pa))
                            conn.commit()
                            st.success("Compte créé ! Connectez-vous.")
                        except: st.error("Email déjà utilisé.")
                    else: st.error("Numéro invalide.")

    else:
        u_email = st.session_state.user[0]
        # MISE À JOUR BARRE LATÉRALE (Image corrig.jpg)
        st.sidebar.title("🚀 KERIANE")
        st.sidebar.caption("Ges-Projets (Suivi de Projets & Productivité)")
        
        menu = st.sidebar.selectbox("Menu", ["Collecte de Données", "Mon Profil", "Déconnexion"])

        if menu == "Déconnexion":
            st.session_state.auth = False
            st.rerun()

        elif menu == "Mon Profil":
            st.header("👤 Mon Profil")
            with st.form("p"):
                n_nom = st.text_input("Nom", value=st.session_state.user[1])
                n_pre = st.text_input("Prénom", value=st.session_state.user[2])
                n_ph = st.text_input("Téléphone", value=st.session_state.user[3])
                if st.form_submit_button("Mettre à jour"):
                    c.execute('UPDATE users SET nom=?, prenom=?, phone=? WHERE email=?', (n_nom, n_pre, n_ph, u_email))
                    conn.commit()
                    st.success("Profil mis à jour !")

        elif menu == "Collecte de Données":
            t_s = st.tabs(["📥 Saisie", "🥧 Analyse", "🛠️ Gestion"])

            with t_s[0]:
                with st.form("saisie"):
                    p_nom = st.text_input("Nom du Projet")
                    col_l1, col_l2 = st.columns(2)
                    p_opt = col_l1.selectbox("Langage", LANGAGES_LIST)
                    p_custom = col_l2.text_input("Si AUTRE, écrivez ici")
                    p_lang = p_custom if p_opt == "AUTRE" else p_opt
                    
                    c1, c2 = st.columns(2)
                    p_h = c1.number_input("Heures", min_value=0.0, value=0.0, step=0.1)
                    p_st = c2.selectbox("Statut", ["En attente", "En cours", "Terminé", "En pause"])
                    
                    st.write("---")
                    st.subheader("Infos importantes")
                    colA, colB, colC = st.columns(3)
                    p_prio = colA.select_slider("Priorité", ["Basse", "Moyenne", "Haute", "Urgente"])
                    p_cli = colB.text_input("Client")
                    p_bud = colC.number_input("Budget", min_value=0.0, value=0.0)
                    
                    colD, colE, colF = st.columns(3)
                    p_plat = colD.selectbox("Plateforme", ["Web", "Mobile", "Desktop", "API"])
                    p_diff = colE.selectbox("Difficulté", ["Facile", "Moyen", "Difficile"])
                    p_dead = colF.date_input("Deadline")
                    
                    p_note = st.text_area("Notes")
                    
                    if st.form_submit_button("Enregistrer"):
                        c.execute('''INSERT INTO projets (user_email, date, nom_projet, langage, heures, statut, priorite, client, budget, plateforme, difficulte, deadline, notes) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), p_nom, p_lang, float(p_h), p_st, p_prio, p_cli, float(p_bud), p_plat, p_diff, str(p_dead), p_note))
                        conn.commit()
                        st.success("Projet enregistré !")

            with t_s[1]:
                c.execute('SELECT langage, heures, nom_projet FROM projets WHERE user_email=?', (u_email,))
                data = c.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=["Langage", "Heures", "Projet"])
                    st.plotly_chart(px.pie(df, values='Heures', names='Langage', hole=0.4), use_container_width=True)
                else: st.info("Aucune donnée.")

            with t_s[2]:
                c.execute('SELECT id, nom_projet FROM projets WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                if rows:
                    opt = {f"ID:{r[0]} | {r[1]}": r[0] for r in rows}
                    sel_id = opt[st.selectbox("Projet à modifier", list(opt.keys()))]
                    c.execute('SELECT * FROM projets WHERE id=?', (sel_id,))
                    curr = c.fetchone()
                    
                    with st.form("edit"):
                        # PROTECTION ANTI-ERREUR JS
                        h_val = float(curr[5]) if curr[5] else 0.0
                        b_val = float(curr[9]) if curr[9] else 0.0
                        
                        e_nom = st.text_input("Nom", value=str(curr[3]))
                        e_h = st.number_input("Heures", min_value=0.0, value=h_val)
                        e_st = st.selectbox("Statut", ["En attente", "En cours", "Terminé", "En pause"])
                        e_bud = st.number_input("Budget", min_value=0.0, value=b_val)
                        if st.form_submit_button("Mettre à jour"):
                            c.execute('UPDATE projets SET nom_projet=?, heures=?, statut=?, budget=? WHERE id=?', (e_nom, float(e_h), e_st, float(e_bud), sel_id))
                            conn.commit()
                            st.success("Mis à jour !")
                            st.rerun()
                    if st.button("Supprimer"):
                        c.execute('DELETE FROM projets WHERE id=?', (sel_id,))
                        conn.commit()
                        st.rerun()

if __name__ == '__main__':
    main()