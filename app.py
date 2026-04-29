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

# --- CSS : DESIGN PROFESSIONNEL ---
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
    conn = sqlite3.connect('ges_projets.db', check_same_thread=False)
    c = conn.cursor()
    # Table Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                phone TEXT, password TEXT, sex TEXT, pays TEXT)''')
    # Table Projets (Collecte de données)
    c.execute('''CREATE TABLE IF NOT EXISTS projets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, 
                date TEXT, nom_projet TEXT, langage TEXT, heures REAL, 
                statut TEXT, notes TEXT)''')
    conn.commit()
    return conn, c

conn, c = init_db()

def hash_pwd(pwd): return hashlib.sha256(str.encode(pwd)).hexdigest()

# --- GESTION DE LA SESSION ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None
    st.session_state.page = "login_signup"

# --- INTERFACE DE CONNEXION / INSCRIPTION ---
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
                            st.success("🎉 Compte créé avec succès !")
                            st.info("Cliquez sur 'Se Connecter' ci-dessus pour entrer.")
                        except: st.error("Cet email est déjà enregistré.")
                    else: st.error(f"Le format du numéro pour le {s_pa} est invalide.")

    else:
        # --- INTERFACE APPLICATION APRÈS CONNEXION ---
        u_email = st.session_state.user[0]
        st.sidebar.title(f"🚀 Ges-Projets")
        st.sidebar.write(f"Utilisateur : **{st.session_state.user[2]}**")
        
        menu = st.sidebar.selectbox("Menu", ["Collecte de Données", "Mon Profil", "Déconnexion"])

        if menu == "Déconnexion":
            st.session_state.auth = False
            st.rerun()

        elif menu == "Mon Profil":
            st.header("👤 Mes Informations Personnelles")
            with st.form("edit_profile"):
                new_nom = st.text_input("Nom", value=st.session_state.user[1])
                new_pre = st.text_input("Prénom", value=st.session_state.user[2])
                new_em = st.text_input("Email (identifiant)", value=st.session_state.user[0], disabled=True)
                new_ph = st.text_input("Téléphone", value=st.session_state.user[3])
                if st.form_submit_button("Mettre à jour le profil"):
                    c.execute('UPDATE users SET nom=?, prenom=?, phone=? WHERE email=?', (new_nom, new_pre, new_ph, u_email))
                    conn.commit()
                    st.success("Profil mis à jour !")

        elif menu == "Collecte de Données":
            st.header("📊 Gestion des Projets")
            t_saisie, t_analyse, t_modif = st.tabs(["📥 Nouvelle Donnée", "🥧 Analyse Graphique", "🛠️ Modifier/Supprimer"])

            with t_saisie:
                with st.form("saisie_projet"):
                    p_nom = st.text_input("Nom du Projet")
                    p_lang = st.selectbox("Langage principal", ["Python", "JavaScript", "HTML/CSS", "Java", "C++", "PHP", "SQL"])
                    col_h, col_s = st.columns(2)
                    p_heure = col_h.number_input("Heures de travail", 0.1)
                    p_statut = col_s.selectbox("Statut", ["En cours", "Terminé", "En pause"])
                    p_note = st.text_area("Notes additionnelles")
                    if st.form_submit_button("Enregistrer le projet"):
                        c.execute('INSERT INTO projets (user_email, date, nom_projet, langage, heures, statut, notes) VALUES (?,?,?,?,?,?,?)',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), p_nom, p_lang, p_heure, p_statut, p_note))
                        conn.commit()
                        st.success("Donnée enregistrée !")

            with t_analyse:
                c.execute('SELECT date, nom_projet, langage, heures, statut FROM projets WHERE user_email=?', (u_email,))
                data = c.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=["Date", "Projet", "Langage", "Heures", "Statut"])
                    st.subheader("Visualisation de l'effort par Langage")
                    fig = px.pie(df, values='Heures', names='Langage', hole=0.4, title="Répartition du temps (Heures)")
                    st.plotly_chart(fig, use_container_width=True)
                    st.subheader("Historique des saisies")
                    st.dataframe(df, use_container_width=True)
                else: st.info("Aucune donnée enregistrée.")

            with t_modif:
                c.execute('SELECT id, nom_projet, date FROM projets WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                if rows:
                    options = {f"{r[1]} (le {r[2]})": r[0] for r in rows}
                    sel_nom = st.selectbox("Sélectionner une donnée à modifier", list(options.keys()))
                    sel_id = options[sel_nom]

                    # Récupérer les données actuelles
                    c.execute('SELECT * FROM projets WHERE id=?', (sel_id,))
                    curr = c.fetchone()

                    with st.form("edit_data"):
                        st.subheader("Modifier tous les paramètres")
                        e_nom = st.text_input("Nom du projet", value=curr[3])
                        e_lang = st.selectbox("Langage", ["Python", "JavaScript", "HTML/CSS", "Java", "C++", "PHP", "SQL"], index=0)
                        e_heure = st.number_input("Heures", value=curr[5])
                        e_statut = st.selectbox("Statut", ["En cours", "Terminé", "En pause"], index=0)
                        e_note = st.text_area("Notes", value=curr[7])
                        
                        if st.form_submit_button("Mettre à jour cette donnée"):
                            c.execute('''UPDATE projets SET nom_projet=?, langage=?, heures=?, statut=?, notes=? 
                                         WHERE id=?''', (e_nom, e_lang, e_heure, e_statut, e_note, sel_id))
                            conn.commit()
                            st.success("Donnée mise à jour !")
                            st.rerun()
                    
                    if st.button("🗑️ Supprimer définitivement"):
                        c.execute('DELETE FROM projets WHERE id=?', (sel_id,))
                        conn.commit()
                        st.rerun()

if __name__ == '__main__':
    main()