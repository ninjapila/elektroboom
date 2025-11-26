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
# --- PASEK BOCZNY ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2913/2913008.png", width=100) # Ikona domu/serca
    st.header("🧸 Operacja: Kolor")
    st.markdown("""
    **Cel:** Zamieniamy szare ściany w Domach Dziecka na bajkowe fototapety.
    
    Używasz apki za darmo? Zaoszczędziłeś dzisiaj 5 zł?
    **Wrzuć to do puszki!** 👇
    """)
    
    # TU WKLEJ SWÓJ LINK DO ZRZUTKI / BUYCOFFEE
    link_do_zrzutki = " https://elektroboom-vbyeg8bnkdmsm4phagnvoy.streamlit.app"
    
    st.link_button("🎨 WPŁAĆ NA TAPETY", link_do_zrzutki)
    st.divider()
    
    st.header("⚙️ Ustawienia Domowe")
    moc_pralki = st.slider("Moc urządzenia (kW)", 0.5, 5.0, 2.0, step=0.1)
    czas_trwania = st.slider("Czas pracy (h)", 1, 5, 3)

# --- POBIERANIE DANYCH ---
@st.cache_data(ttl=900)
def get_prices():
    # API Energy-Charts (Europa/Polska)
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
    KURS_EUR = 4.30 # Sztywny kurs dla uproszczenia
    
    for ts, price in zip(data['unix_seconds'], data['price']):
        dt = datetime.fromtimestamp(ts)
        if dt.date() == datetime.now().date():
            # Zamiana EUR/MWh -> PLN/kWh
            cena_pln = (price * KURS_EUR) / 1000
            ceny.append({"Godzina": dt.hour, "Cena": cena_pln})
            
    df = pd.DataFrame(ceny)

    if df.empty:
        st.warning("💤 Serwery giełdowe jeszcze śpią. Brak danych na dziś.")
    else:
        # 1. Znajdź TERAZ
        obecna_godzina = datetime.now().hour
        
        # Oblicz koszt startu TERAZ
        window_now = df[(df['Godzina'] >= obecna_godzina) & (df['Godzina'] < obecna_godzina + czas_trwania)]
        avg_now = window_now['Cena'].mean() if not window_now.empty else 0.50
        koszt_teraz = avg_now * moc_pralki * czas_trwania
        
        # 2. Znajdź NAJTANIEJ (od teraz do północy)
        min_koszt = 100.0
        najlepsza_h = obecna_godzina
        
        limit_h = 24 - czas_trwania
        for h in range(obecna_godzina, limit_h):
            window = df[(df['Godzina'] >= h) & (df['Godzina'] < h + czas_trwania)]
            koszt = (window['Cena'].mean() * moc_pralki * czas_trwania)
            if koszt < min_koszt:
                min_koszt = koszt
                najlepsza_h = h
        
        # 3. WYNIKI
        oszczędność = koszt_teraz - min_koszt
        litry = oszczednosc / cena_paliwa
        km = (litry / spalanie) * 100
        
        st.divider()
        
        # Kolumny z wynikami
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔴 Koszt TERAZ", f"{koszt_teraz:.2f} PLN")
        with col2:
            st.metric(f"🟢 Koszt o {najlepsza_h}:00", f"{min_koszt:.2f} PLN", delta=f"Zysk: {oszczednosc:.2f} PLN")

        # WERDYKT
        if oszczednosc > 0.10:
            st.success(f"🚀 **WERDYKT: CZEKAJ!**")
            st.markdown(f"""
            Jeśli włączysz sprzęt o **{najlepsza_h}:00**, zyskasz:
            * ⛽ **{litry:.2f} L** paliwa
            * 🚗 **{km:.1f} km** darmowej jazdy
            """)
        else:
            st.info("😐 **WERDYKT:** Ceny są płaskie. Możesz prać teraz, dużej różnicy nie ma.")
            
        # WYKRES
        st.subheader("📉 Wykres Cen Prądu (Dziś)")
        # Kolorowanie słupków
        df['Kolor'] = df['Cena']
        fig = px.bar(df, x='Godzina', y='Cena', color='Cena', 
                     color_continuous_scale='RdYlGn_r',
                     labels={'Cena': 'Cena (PLN/kWh)'})
        # Linia "Teraz"
        fig.add_vline(x=obecna_godzina, line_dash="dash", line_color="black", annotation_text="TERAZ")
        st.plotly_chart(fig, use_container_width=True)
