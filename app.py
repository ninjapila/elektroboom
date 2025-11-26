import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Elektroboom ⚡", page_icon="⚡", layout="centered")

# --- CSS (Wygląd) ---
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- NAGŁÓWEK ---
st.title("⚡ Elektroboom")
st.markdown("### Zamień prąd na paliwo ⛽")
st.write("System automatycznie wykrywa, kiedy prąd jest najtańszy i przelicza oszczędności na zasięg Twojego samochodu.")

# --- PASEK BOCZNY ---
with st.sidebar:
    # 1. SEKCJA CHARYTATYWNA
    st.image("https://cdn-icons-png.flaticon.com/512/2913/2913008.png", width=100)
    st.header("🧸 Misja: Kolor")
    st.info("Oszczędzasz na prądzie? Wrzuć połowę zysku do puszki. Kupujemy fototapety do Domów Dziecka!")
    
    # LINK DO TWOJEJ ZRZUTKI
    link_do_zrzutki = "https://zrzutka.pl/" 
    st.link_button("🎨 WPŁAĆ NA TAPETY", link_do_zrzutki)
    
    st.divider()
    
    # 2. SEKCJA TECHNICZNA
    st.header("⚙️ Ustawienia Domowe")
    moc_pralki = st.slider("Moc urządzenia (kW)", 0.5, 5.0, 2.0, step=0.1)
    czas_trwania = st.slider("Czas pracy (h)", 1, 5, 3)
    
    st.divider()

    # 3. SEKCJA PALIWOWA
    st.header("🚗 Przelicznik Męża")
    cena_paliwa = st.number_input("Cena paliwa (PLN)", value=6.40)
    spalanie = st.number_input("Spalanie auta (L/100km)", value=8.0)

# --- POBIERANIE DANYCH ---
@st.cache_data(ttl=900)
def get_prices():
    url = "https://api.energy-charts.info/price?bzn=PL"
    try:
        r = requests.get(url, timeout=10).json()
        return r
    except:
        return None

# --- LOGIKA BIZNESOWA ---
data = get_prices()

if not data:
    st.error("⚠️ Błąd łączności z giełdą energii. Spróbuj później.")
else:
    # Przetwarzanie JSON -> DataFrame
    ceny = []
    KURS_EUR = 4.30 
    
    for ts, price in zip(data['unix_seconds'], data['price']):
        dt = datetime.fromtimestamp(ts)
        if dt.date() == datetime.now().date():
            cena_pln = (price * KURS_EUR) / 1000
            ceny.append({"Godzina": dt.hour, "Cena": cena_pln})
            
    df = pd.DataFrame(ceny)

    if df.empty:
        st.warning("💤 Serwery giełdowe jeszcze śpią. Brak danych na dziś.")
    else:
        # Obliczenia
        obecna_godzina = datetime.now().hour
        
        # Koszt TERAZ
        window_now = df[(df['Godzina'] >= obecna_godzina) & (df['Godzina'] < obecna_godzina + czas_trwania)]
        avg_now = window_now['Cena'].mean() if not window_now.empty else 0.50
        koszt_teraz = avg_now * moc_pralki * czas_trwania
        
        # Koszt NAJTANIEJ
        min_koszt = 100.0
        najlepsza_h = obecna_godzina
        limit_h = 24 - czas_trwania
        for h in range(obecna_godzina, limit_h):
            window = df[(df['Godzina'] >= h) & (df['Godzina'] < h + czas_trwania)]
            koszt = (window['Cena'].mean() * moc_pralki * czas_trwania)
            if koszt < min_koszt:
                min_koszt = koszt
                najlepsza_h = h
        
        # WYNIKI
        oszczednosc = koszt_teraz - min_koszt
        litry = oszczednosc / cena_paliwa
        km = (litry / spalanie) * 100
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔴 Koszt TERAZ", f"{koszt_teraz:.2f} PLN")
        with col2:
            st.metric(f"🟢 Koszt o {najlepsza_h}:00", f"{min_koszt:.2f} PLN", delta=f"Zysk: {oszczednosc:.2f} PLN")

        if oszczednosc > 0.10:
            st.success(f"🚀 **WERDYKT: CZEKAJ!**")
            st.markdown(f"""
            Jeśli włączysz sprzęt o **{najlepsza_h}:00**, zyskasz:
            * ⛽ **{litry:.2f} L** paliwa
            * 🚗 **{km:.1f} km** darmowej jazdy
            """)
        else:
            st.info("😐 **WERDYKT:** Ceny są płaskie. Możesz prać teraz.")
            
        st.subheader("📉 Wykres Cen Prądu (Dziś)")
        df['Kolor'] = df['Cena']
        fig = px.bar(df, x='Godzina', y='Cena', color='Cena', 
                     color_continuous_scale='RdYlGn_r',
                     labels={'Cena': 'Cena (PLN/kWh)'})
        fig.add_vline(x=obecna_godzina, line_dash="dash", line_color="black", annotation_text="TERAZ")
        st.plotly_chart(fig, use_container_width=True)
