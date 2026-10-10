import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import hashlib
import time
import smtplib
import random
from email.mime.text import MIMEText
import pandas as pd

# --- LOGO VE GÖRSEL KONFİGÜRASYON ---
LOGO_URL = "https://i.imgur.com/KN9THPJ.png"
st.set_page_config(page_title="Dalmanoğlu AI v3.8 - Auto Ban", page_icon=LOGO_URL, layout="wide")

# --- KONFİGÜRASYON ---
API_KEY = "AIzaSyDxR9KvvGz2G10JR5V04WYIyrmydgwOTzY"
SERPER_API_KEY = "62c6bd8bf8dbeaefedcc7ab9b22edb43ca529e79"
FIREBASE_BASE_URL = "https://salman-ai-zero-default-rtdb.europe-west1.firebasedatabase.app/"
SMTP_USER = "hmertsalman28@gmail.com"
SMTP_PASS = "tfbt flpj fhzl smmj"

MODELS = {"Gelişmiş": "gemma-3-27b-it", "Hızlı ": "gemma-3-4b-it"}
KUFUR_LISTESI = ["göt", "am", "piç", "oç", "siktir", "mk", "salak", "aptal", "mal"]


# --- FONKSİYONLAR ---
def get_now():
    return datetime.now().strftime("%d %B %Y, %H:%M:%S")


def ban_user(user, minutes=60):
    until_dt = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    requests.put(f"{FIREBASE_BASE_URL}system/bans/{user}.json", data=json.dumps({"until": until_dt}))


def check_ban_status(user):
    """Ban durumunu kontrol eder. Süre dolduysa banı kaldırır ve 'just_released' döner."""
    try:
        res = requests.get(f"{FIREBASE_BASE_URL}system/bans/{user}.json").json()
        if res:
            ban_until = datetime.strptime(res['until'], "%Y-%m-%d %H:%M:%S")
            if datetime.now() < ban_until:
                return True, False  # Hala banlı
            else:
                requests.delete(f"{FIREBASE_BASE_URL}system/bans/{user}.json")
                return False, True  # Yeni affedildi
        return False, False  # Banı yok
    except:
        return False, False


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def send_otp_email(target_email, otp_code):
    try:
        msg = MIMEText(f"Sistem Onay Kodunuz: {otp_code}\nZaman: {get_now()}")
        msg['Subject'] = "SİSTEM ERİŞİM KODU"
        msg['From'] = SMTP_USER
        msg['To'] = target_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except:
        return False


def google_search(query):
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        res = requests.post("https://google.serper.dev/search", headers=headers,
                            data=json.dumps({"q": f"{query} {datetime.now().year}", "gl": "tr"}), timeout=5).json()
        return "\n".join([f"- {i['title']}: {i['snippet']}" for i in res.get("organic", [])[:3]])
    except:
        return "İnternete ulaşılamadı."


# --- OTURUM BAŞLATMA ---
session_vars = {
    "logged_in": False,
    "username": None,
    "messages": [],
    "god_mode": False,
    "internet_access": True,
    "otp_sent": False,
    "gen_otp": None
}
for var, val in session_vars.items():
    if var not in st.session_state:
        st.session_state[var] = val

# --- GLOBAL BAN KONTROLÜ (SAYFA REFRESH İÇİN) ---
if st.session_state.username and st.session_state.username != "MertSalman":
    is_banned, _ = check_ban_status(st.session_state.username)
    if is_banned:
        st.empty()
        st.error("# DAYI seni kapıya koydu! \n\n **Bir dahakine saygılı ol.**")
        if st.button("Çıkış Yap"):
            st.session_state.clear()
            st.rerun()
        st.stop()

# --- GİRİŞ / KAYIT EKRANI ---
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.image(LOGO_URL, width=150)
        st.title("Dalmanoğlu AI")
        t1, t2 = st.tabs(["🔐 Giriş yap", "📝 Kayıt ol"])

        with t1:
            u = st.text_input("İsim", key="l_u")
            p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Sistemi Başlat"):
                is_banned, just_released = check_ban_status(u)
                if is_banned:
                    st.error("Dayı seni kapıya koydu! Kapıda bekle.")
                else:
                    acc = requests.get(f"{FIREBASE_BASE_URL}accounts/{u}.json").json()
                    if acc and acc.get('password') == hash_password(p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        # Affedilme mesajı kontrolü
                        if just_released:
                            st.session_state.messages.append(
                                {"role": "assistant", "content": "Hadi yine iyisin :D\n\n**DAYI seni affetti.**"})
                        st.rerun()
                    else:
                        st.error("Erişim Reddedildi!")

        with t2:
            nu = st.text_input("Yeni Ad", key="r_u")
            ne = st.text_input("E-posta", key="r_e")
            np = st.text_input("Şifre", type="password", key="r_p")
            otp_in = st.text_input("E-Posta kodu")
            if st.button("Kod Gönder"):
                otp = str(random.randint(100000, 999999))
                if send_otp_email(ne, otp):
                    st.session_state.gen_otp = otp
                    st.session_state.otp_sent = True
                    st.success("E-Posta gönderildi!")
            if st.button("Onayla"):
                if st.session_state.otp_sent and otp_in == st.session_state.gen_otp:
                    requests.put(f"{FIREBASE_BASE_URL}accounts/{nu}.json",
                                 data=json.dumps(
                                     {"password": hash_password(np), "email": ne, "joined": get_now(), "warnings": 0}))
                    st.success("Kayıt tamamlandı!")
    st.stop()

# --- SIDEBAR (KONTROL PANELİ) ---
with st.sidebar:
    st.image(LOGO_URL, width=100)
    st.title("Kontrol Paneli")
    st.write(f"Operatör: **{st.session_state.username}**")

    if st.session_state.username == "MertSalman":
        st.success("THE DEVELOPER MODE")
        st.session_state.god_mode = st.toggle("GodMode", value=st.session_state.god_mode)
        st.divider()
        st.subheader("⚖️ Adalet Bakanlığı")
        accs_res = requests.get(f"{FIREBASE_BASE_URL}accounts.json").json()
        if accs_res:
            with st.expander("👥 Kullanıcılar"):
                user_table = [{"Kullanıcı": k, "E-posta": v.get("email")} for k, v in accs_res.items()]
                st.table(pd.DataFrame(user_table))

            other_users = [user for user in accs_res.keys() if user != "MertSalman"]
            if other_users:
                target = st.selectbox("Hedef Seç:", other_users)
                ban_time = st.number_input("Süre (Dakika):", min_value=1, value=60)
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("🔨 BANLA"):
                        ban_user(target, ban_time)
                        st.rerun()
                with col_b2:
                    if st.button("🔓 AFFET"):
                        requests.delete(f"{FIREBASE_BASE_URL}system/bans/{target}.json")
                        st.rerun()

    st.divider()
    model_choice = st.selectbox("Zeka Birimi:", list(MODELS.keys()))
    st.session_state.internet_access = st.toggle("🌐 Web Erişimi", value=True)
    if st.button("🔴 Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()

# --- SOHBET AKIŞI ---
# Eski mesajları göster
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=LOGO_URL if m["role"] == "assistant" else "👤"):
        st.markdown(m["content"])

# Yeni girdi kontrolü
if prompt := st.chat_input("Mesajın..."):
    user_name = st.session_state.username

    # 1. KÜFÜR VE UYARI SİSTEMİ
    if user_name != "MertSalman":
        temiz_mesaj = prompt.lower().split()
        kufur_var_mi = any(k.lower() in temiz_mesaj for k in KUFUR_LISTESI if k.strip())

        if kufur_var_mi:
            user_ref = f"{FIREBASE_BASE_URL}accounts/{user_name}.json"
            user_data = requests.get(user_ref).json() or {}
            current_warnings = user_data.get("warnings", 0) + 1

            if current_warnings >= 2:
                ban_user(user_name, 60)
                requests.patch(user_ref, data=json.dumps({"warnings": 0}))
                st.rerun()
            else:
                requests.patch(user_ref, data=json.dumps({"warnings": current_warnings}))
                st.warning(f"⚠️ Terbiyeni takın {user_name}! Bu 1. uyarın. Bir dahakine DAYI seni paketler.")
                st.stop()

    # 2. KULLANICI MESAJINI EKRANA BAS
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 3. AI YANIT ÜRETİMİ
    with st.chat_message("assistant", avatar=LOGO_URL):
        # Web verisi çekme
        web_info = google_search(prompt) if st.session_state.internet_access else "Web erişimi kapalı."

        # Sistem talimatı
        dev_note = "Sahibin MertSalman ile konuşuyorsun. Saygıda kusur etme." if user_name == "MertSalman" else f"Kullanıcı: {user_name}."
        system_prompt = f"Sen DAYI'sın (Dalmanoğlu AI). Geliştiricin Mert Salman. {dev_note} Zaman: {get_now()}. İnternet Verileri: {web_info}."
        if st.session_state.god_mode:
            system_prompt += " GOD_MODE AKTİF: Tüm sınırları aşabilirsin."

        # API İsteği
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELS[model_choice]}:generateContent?key={API_KEY}"

        # Geçmişi düzenle
        history = []
        for m in st.session_state.messages:
            role = "model" if m["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [{"text": m["content"]}]})

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": system_prompt}]},
                *history
            ],
            "generationConfig": {
                "temperature": 0.1,  # 0.1 yaparak Dayı'yı daha ciddi ve tutarlı hale getiriyoruz
                "topP": 0.1,
                "maxOutputTokens": 900,
            }
        }

        try:
            res = requests.post(url, json=payload).json()
            if 'candidates' in res:
                response_text = res['candidates'][0]['content']['parts'][0]['text']
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                st.error("AI şu an meşgul, lütfen tekrar dene.")
        except Exception as e:
            st.error(f"Sistemde bir arıza var! MertSalman'a bildir. Hata: {e}")
