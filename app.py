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
    conn = sqlite3.connect('ges_projets_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                phone TEXT, password TEXT, sex TEXT, pays TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, 
                date TEXT, nom_projet TEXT, langage TEXT, heures REAL, 
                statut TEXT, notes TEXT)''')
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
                        st.session_state.auth = True
                        st.session_state.user = list(user)
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
                            c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', 
                                     (s_em, s_nom, s_pre, f"{PAYS_DATA[s_pa]['code']} {s_ph}", hash_pwd(s_pw), s_sex, s_pa))
                            conn.commit()
                            st.success("🎉 Compte créé ! Connectez-vous maintenant.")
                        except: st.error("Cet email existe déjà.")
                    else: st.error("Format de numéro invalide.")

    else:
        u_email = st.session_state.user[0]
        st.sidebar.title(f"🚀 KERIANE")
        menu = st.sidebar.selectbox("Menu", ["Collecte de Données", "Mon Profil", "Déconnexion"])

        if menu == "Déconnexion":
            st.session_state.auth = False
            st.rerun()

        elif menu == "Mon Profil":
            st.header("👤 Modifier mon Profil")
            with st.form("edit_profile"):
                n_nom = st.text_input("Nom", value=st.session_state.user[1])
                n_pre = st.text_input("Prénom", value=st.session_state.user[2])
                n_ph = st.text_input("Téléphone", value=st.session_state.user[3])
                if st.form_submit_button("Sauvegarder"):
                    c.execute('UPDATE users SET nom=?, prenom=?, phone=? WHERE email=?', (n_nom, n_pre, n_ph, u_email))
                    conn.commit()
                    st.success("Profil mis à jour !")

        elif menu == "Collecte de Données":
            t_saisie, t_analyse, t_modif = st.tabs(["📥 Saisie", "🥧 Analyse", "🛠️ Gestion"])

            with t_saisie:
                with st.form("saisie_p"):
                    p_nom = st.text_input("Nom du Projet")
                    p_lang = st.selectbox("Langage", ["Python", "JavaScript", "C++", "Java", "PHP"])
                    p_h = st.number_input("Heures", 0.5)
                    p_st = st.selectbox("Statut", ["En cours", "Terminé"])
                    if st.form_submit_button("Enregistrer"):
                        c.execute('INSERT INTO projets (user_email, date, nom_projet, langage, heures, statut) VALUES (?,?,?,?,?,?)',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), p_nom, p_lang, p_h, p_st))
                        conn.commit()
                        st.success("Donnée ajoutée !")

            with t_analyse:
                c.execute('SELECT langage, heures, nom_projet FROM projets WHERE user_email=?', (u_email,))
                data = c.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=["Langage", "Heures", "Projet"])
                    st.plotly_chart(px.pie(df, values='Heures', names='Langage', hole=0.4), use_container_width=True)
                    st.dataframe(df, use_container_width=True)
                else: st.info("Aucune donnée.")

            with t_modif:
                c.execute('SELECT id, nom_projet, date FROM projets WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                if rows:
                    opt = {f"{r[1]} ({r[2]})": r[0] for r in rows}
                    sel = st.selectbox("Sélectionner", list(opt.keys()))
                    if st.button("Supprimer"):
                        c.execute('DELETE FROM projets WHERE id=?', (opt[sel],))
                        conn.commit()
                        st.rerun()

if __name__ == '__main__':
    main()