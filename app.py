import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Ges-Projets Pro", page_icon="💻", layout="wide")

# --- DONNÉES PAYS & VALIDATION ---
PAYS_DATA = {
    "Cameroun": {"code": "+237", "regex": r"^\d{9}$"},
    "France": {"code": "+33", "regex": r"^\d{9}$"},
    "Côte d'Ivoire": {"code": "+225", "regex": r"^\d{10}$"},
    "Sénégal": {"code": "+221", "regex": r"^\d{9}$"},
    "Canada": {"code": "+1", "regex": r"^\d{10}$"}
}

# --- LISTE DES LANGAGES ---
LANGAGES_LIST = ["Python", "JavaScript", "C++", "Java", "PHP", "Swift", "Kotlin", "Rust", "Go", "TypeScript", "C#", "Ruby", "AUTRE (Saisir manuellement)"]

# --- CSS : DESIGN ---
st.markdown("""
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1498050108023-c5249f4df085?q=80&w=2072&auto=format&fit=crop");
        background-attachment: fixed; background-size: cover;
    }
    .stTabs, .stForm, .stDataFrame {
        background-color: rgba(255, 255, 255, 0.95) !important;
        padding: 20px; border-radius: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('ges_projets_v3.db', check_same_thread=False)
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
            with st.form("login_form"):
                l_nom = st.text_input("Nom")
                l_prenom = st.text_input("Prénom")
                l_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Connexion"):
                    c.execute('SELECT * FROM users WHERE nom=? AND prenom=? AND password=?', (l_nom, l_prenom, hash_pwd(l_pw)))
                    user = c.fetchone()
                    if user:
                        st.session_state.auth, st.session_state.user = True, list(user)
                        st.rerun()
                    else: st.error("Identifiants incorrects.")

        with tab_signup:
            with st.form("signup_form"):
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
                            st.success("🎉 Compte créé ! Connectez-vous.")
                        except: st.error("Email déjà utilisé.")
                    else: st.error("Format de numéro invalide.")

    else:
        u_email = st.session_state.user[0]
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
            t_saisie, t_analyse, t_modif = st.tabs(["📥 Saisie", "🥧 Analyse", "🛠️ Gestion"])

            with t_saisie:
                with st.form("saisie_p"):
                    p_nom = st.text_input("Nom du Projet")
                    
                    # Gestion du langage
                    col_l1, col_l2 = st.columns(2)
                    p_lang_opt = col_l1.selectbox("Choisir le langage", LANGAGES_LIST)
                    p_lang_custom = col_l2.text_input("Ou saisir le langage manuellement")
                    p_lang_final = p_lang_custom if p_lang_opt == "AUTRE (Saisir manuellement)" else p_lang_opt
                    
                    colA, colB = st.columns(2)
                    p_h = colA.number_input("Heures passées", 0.1)
                    p_st = colB.selectbox("Statut actuel", ["En attente", "En cours", "Terminé", "En pause"])
                    
                    st.write("---")
                    st.subheader("Informations Complémentaires")
                    c1, c2, c3 = st.columns(3)
                    p_prio = c1.select_slider("Priorité", options=["Basse", "Moyenne", "Haute", "Urgente"])
                    p_client = c2.text_input("Client / Organisation")
                    p_budget = c3.number_input("Budget estimé (FCFA / €)", 0.0)
                    
                    c4, c5, c6 = st.columns(3)
                    p_plat = c4.selectbox("Plateforme cible", ["Web", "Mobile Android", "iOS", "Desktop", "API/Backend"])
                    p_diff = c5.selectbox("Difficulté", ["Facile", "Intermédiaire", "Complexe"])
                    p_dead = c6.date_input("Deadline prévue")
                    
                    p_note = st.text_area("Notes détaillées")
                    
                    if st.form_submit_button("Enregistrer la donnée"):
                        c.execute('''INSERT INTO projets (user_email, date, nom_projet, langage, heures, statut, priorite, client, budget, plateforme, difficulte, deadline, notes) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), p_nom, p_lang_final, p_h, p_st, p_prio, p_client, p_budget, p_plat, p_diff, str(p_dead), p_note))
                        conn.commit()
                        st.success("Projet enregistré !")

            with t_analyse:
                c.execute('SELECT langage, heures, nom_projet, statut, priorite FROM projets WHERE user_email=?', (u_email,))
                data = c.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=["Langage", "Heures", "Projet", "Statut", "Priorité"])
                    st.plotly_chart(px.pie(df, values='Heures', names='Langage', hole=0.4, title="Répartition par Langage"), use_container_width=True)
                    st.dataframe(df, use_container_width=True)
                else: st.info("Aucune donnée.")

            with t_modif:
                c.execute('SELECT id, nom_projet, date FROM projets WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                if rows:
                    opt = {f"ID:{r[0]} | {r[1]} ({r[2]})": r[0] for r in rows}
                    sel_id = opt[st.selectbox("Choisir le projet à modifier", list(opt.keys()))]
                    
                    c.execute('SELECT * FROM projets WHERE id=?', (sel_id,))
                    curr = list(c.fetchone())
                    
                    st.write("---")
                    with st.form("edit_f"):
                        st.subheader(f"Modification de : {curr[3]}")
                        e_nom = st.text_input("Nom du projet", value=curr[3])
                        e_lang = st.text_input("Langage utilisé", value=curr[4])
                        
                        col1, col2, col3 = st.columns(3)
                        e_h = col1.number_input("Heures", value=curr[5])
                        e_st = col2.selectbox("Statut", ["En attente", "En cours", "Terminé", "En pause"], index=0)
                        e_bud = col3.number_input("Budget", value=curr[8])
                        
                        e_note = st.text_area("Notes", value=curr[13])
                        
                        if st.form_submit_button("💾 Mettre à jour tous les paramètres"):
                            c.execute('''UPDATE projets SET nom_projet=?, langage=?, heures=?, statut=?, budget=?, notes=? 
                                         WHERE id=?''', (e_nom, e_lang, e_h, e_st, e_bud, e_note, sel_id))
                            conn.commit()
                            st.success("Données mises à jour !")
                            st.rerun()
                    
                    if st.button("🗑️ Supprimer ce projet définitivement"):
                        c.execute('DELETE FROM projets WHERE id=?', (sel_id,))
                        conn.commit()
                        st.warning("Projet supprimé.")
                        st.rerun()
                else: st.info("Rien à modifier.")

if __name__ == '__main__':
    main()