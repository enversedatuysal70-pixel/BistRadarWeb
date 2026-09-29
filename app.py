import streamlit as st
import pandas as pd
import numpy as np
from tradingview_screener import Query

# Sayfa Yapılandırması
st.set_page_config(
    page_title="WESS VIP RADAR PRO",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Koyu Tema Arayüz Stili
st.markdown("""
    <style>
    .main { background-color: #121212; }
    .stMetric { background-color: #1e1e1e; padding: 10px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. ŞİFRE VE GİRİŞ EKRANI
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 WESS VIP SYSTEM - GİRİŞ")
    
    with st.form("login_form"):
        username = st.text_input("Kullanıcı Adı", value="wess")
        password = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("SİSTEME GİRİŞ YAP")
        
        if submit:
            if username == "wess" and password == "1234":
                st.session_state["authenticated"] = True
                st.success("Giriş Başarılı!")
                st.rerun()
            else:
                st.error("Hatalı Kullanıcı Adı veya Şifre!")
    st.stop()

# ---------------------------------------------------------
# 2. ANA RADAR UYGULAMASI
# ---------------------------------------------------------
st.title("⚡ WESS BİST MULTI-TIMEFRAME ENDEKS & HİSSE DİP DÖNÜŞÜ ENGINE PRO")

st.sidebar.header("⚙️ Kontrol Paneli")

secili_periyot = st.sidebar.selectbox(
    "Periyot Seçin",
    (
        "5 Dakika (5m)", "10 Dakika (10m)", "15 Dakika (15m)", "30 Dakika (30m)",
        "1 Saatlik (60m)", "2 Saatlik (120m)", "3 Saatlik (180m)", 
        "4 Saatlik (240m)", "Günlük (1D)", "Haftalık (1W)", "Aylık (1M)"
    ),
    index=2
)

secili_sektor = st.sidebar.selectbox(
    "Hisse Sektör Filtresi",
    (
        "TÜM BIST", "SANAYİ (XUSIN)", "BANKACILIK (XBANK)", "GYO (XGMYO)", 
        "HOLDİNG (XHOLD)", "BİLİŞİM (XBLSM)", "İLETİŞİM (XILTM)", "GIDA (XGIDA)", 
        "KİMYA (XKMYA)", "ULAŞTIRMA (XULAS)"
    )
)

search_query = st.sidebar.text_input("🔍 Hisse Ara", "").strip().upper()

if st.sidebar.button("🚪 Çıkış Yap"):
    st.session_state["authenticated"] = False
    st.rerun()

# ---------------------------------------------------------
# VERİ ÇEKME FONKSİYONU
# ---------------------------------------------------------
@st.cache_data(ttl=15)
def canli_bist_tara(periyot_adi):
    results = []
    index_results = []
    
    tf_map = {
        "5 Dakika (5m)": "5", "10 Dakika (10m)": "10", "15 Dakika (15m)": "15", 
        "30 Dakika (30m)": "30", "1 Saatlik (60m)": "60", "2 Saatlik (120m)": "120", 
        "3 Saatlik (180m)": "180", "4 Saatlik (240m)": "240", "Günlük (1D)": "", 
        "Haftalık (1W)": "1W", "Aylık (1M)": "1M"
    }
    
    suffix = tf_map.get(periyot_adi, "")
    
    close_col = f"close|{suffix}" if suffix else "close"
    change_col = f"change|{suffix}" if suffix else "change"
    volume_col = f"volume|{suffix}" if suffix else "volume"
    vol_avg_col = f"average_volume_10d_calc|{suffix}" if suffix else "average_volume_10d_calc"
    vwap_col = f"VWAP|{suffix}" if suffix else "VWAP"
    rsi_col = f"RSI|{suffix}" if suffix else "RSI"
    bb_upper_col = f"BB.upper|{suffix}" if suffix else "BB.upper"
    bb_lower_col = f"BB.lower|{suffix}" if suffix else "BB.lower"

    q = (
        Query()
        .set_markets('turkey')
        .select(
            'name', 'sector', close_col, change_col, volume_col, vol_avg_col, 
            vwap_col, rsi_col, bb_upper_col, bb_lower_col
        )
        .limit(650)
    )
    _, df_data = q.get_scanner_data()

    if df_data is not None and not df_data.empty:
        sector_performance = {}
        if 'sector' in df_data.columns:
            sector_perf = df_data.groupby('sector')[change_col].mean().to_dict()
            sector_performance = {k: round(v, 2) for k, v in sector_perf.items() if k}

        for _, row in df_data.iterrows():
            try:
                hisse = str(row.get('name', '')).strip()
                sektor_adi = str(row.get('sector', 'Diğer')).strip()
                fiyat = float(row.get(close_col, 0) or 0)
                fark = float(row.get(change_col, 0) or 0)
                lot_hacmi = float(row.get(volume_col, 0) or 0)
                avg_lot_10d = float(row.get(vol_avg_col, 0) or 0)
                
                vwap_raw = row.get(vwap_col, None)
                rsi_raw = row.get(rsi_col, None)
                bb_up_raw = row.get(bb_upper_col, None)
                bb_low_raw = row.get(bb_lower_col, None)

                hacim_tl = lot_hacmi * fiyat

                if fiyat <= 0 or not hisse:
                    continue

                sektor_kat = "DİĞER"
                sec_lower = sektor_adi.lower()
                if any(x in sec_lower for x in ["industrial", "producer", "process", "sanayi", "imalat", "imla"]):
                    sektor_kat = "SANAYİ"
                elif any(x in sec_lower for x in ["bank", "finance", "financial", "finans"]):
                    sektor_kat = "BANKACILIK"
                elif any(x in sec_lower for x in ["real estate", "property", "gyo"]):
                    sektor_kat = "GYO"
                elif any(x in sec_lower for x in ["holding", "conglomerates"]):
                    sektor_kat = "HOLDİNG"
                elif any(x in sec_lower for x in ["tech", "software", "electronic", "bilişim", "teknoloji"]):
                    sektor_kat = "BİLİŞİM"
                elif any(x in sec_lower for x in ["transportation", "airline", "ulas", "ulaştırma"]):
                    sektor_kat = "ULAŞTIRMA"
                elif any(x in sec_lower for x in ["food", "beverage", "gıda", "tarım"]):
                    sektor_kat = "GIDA"
                elif any(x in sec_lower for x in ["chemical", "kimya", "petrol", "enerji"]):
                    sektor_kat = "KİMYA"
                elif any(x in sec_lower for x in ["telecom", "communication", "iletişim"]):
                    sektor_kat = "İLETİŞİM"

                rvol = (lot_hacmi / avg_lot_10d) if (avg_lot_10d > 0) else 1.0

                vwap_fark = 0.0
                has_vwap = False
                if vwap_raw is not None and not np.isnan(vwap_raw) and float(vwap_raw) > 0:
                    vwap = float(vwap_raw)
                    vwap_fark = ((fiyat - vwap) / vwap) * 100
                    has_vwap = True

                rsi = float(rsi_raw) if (rsi_raw is not None and not np.isnan(rsi_raw)) else 50.0

                is_tight_band = False
                if (bb_up_raw is not None and bb_low_raw is not None and 
                    not np.isnan(bb_up_raw) and not np.isnan(bb_low_raw)):
                    bb_up = float(bb_up_raw)
                    bb_low = float(bb_low_raw)
                    if bb_low > 0:
                        band_width = ((bb_up - bb_low) / fiyat) * 100
                        if band_width <= 6.0:
                            is_tight_band = True

                is_rsi_dip_reentry = (30.0 <= rsi <= 38.0) and (fark >= -0.2)

                skor = 20

                sektor_ort_degisim = sector_performance.get(sektor_adi, 0.0)
                sektor_etiket = "🔥 POZİTİF" if sektor_ort_degisim >= 0.8 else ("⚠️ ZAYIF" if sektor_ort_degisim < -0.5 else "➡️ NÖTR")

                if sektor_ort_degisim >= 1.0: skor += 15
                elif sektor_ort_degisim < -0.8: skor -= 10

                if rvol >= 2.5: skor += 35
                elif rvol >= 1.5: skor += 25
                elif rvol >= 1.1: skor += 15

                if is_tight_band: skor += 25
                if is_rsi_dip_reentry: skor += 35

                if has_vwap and 0.0 <= vwap_fark <= 2.0: skor += 20
                elif has_vwap and -0.5 <= vwap_fark < 0.0: skor += 10

                if 0.5 <= fark <= 4.0: skor += 20
                elif 4.0 < fark <= 6.0: skor += 10

                if hacim_tl >= 10_000_000: skor += 10

                tag = "IZLE"

                if fark >= 7.0 or rsi > 78.0:
                    sinyal = "⚠️ UZAK DUR (PRİMLENDİ)"
                    tag = "UZAK_DUR"
                elif (skor >= 75 and rvol >= 1.4 and 0.5 <= fark <= 5.5):
                    sinyal = "🚀 ŞU AN GİR (ENDEKS ONAYLI)"
                    tag = "KALKIS"
                elif is_rsi_dip_reentry:
                    sinyal = "🔄 DİP DÖNÜŞÜ WESS"
                    tag = "DIP_DONUS"
                elif skor >= 65 and 0.0 <= vwap_fark <= 2.5:
                    sinyal = "💎 TAM ZAMANI (GÜÇLÜ AL)"
                    tag = "GUC_AL"
                elif (is_tight_band or (abs(vwap_fark) <= 0.8 and rvol >= 1.1)) and -1.0 <= fark <= 2.5:
                    sinyal = "🔥 SIKIŞIYOR (TOPLANIYOR)"
                    tag = "SIKISMA"
                else:
                    sinyal = "👀 İZLEMEKTE KAL"
                    tag = "IZLE"

                results.append({
                    "Hisse": hisse,
                    "Sektör": sektor_adi,
                    "Sektör_Kategori": sektor_kat,
                    "Sektör Gücü": sektor_etiket,
                    "Skor": skor,
                    "Son Fiyat (TL)": round(fiyat, 2),
                    "Hacim (TL)": f"{hacim_tl:,.0f}".replace(",", "."),
                    "Değişim (%)": round(fark, 2),
                    "AOF Farkı (%)": round(vwap_fark, 2),
                    "NET AKSİYON SİNYALİ": sinyal,
                    "Tag": tag,
                    "RSI": rsi,
                    "Band_Tight": is_tight_band
                })
            except Exception:
                continue

    if results:
        df_res = pd.DataFrame(results)
        target_indices = [
            ("XU100", "BIST 100", "TÜM BIST"),
            ("XUSIN", "SANAYİ ENDEKSİ", "SANAYİ"),
            ("XBANK", "BANKACILIK ENDEKSİ", "BANKACILIK"),
            ("XGMYO", "GYO ENDEKSİ", "GYO"),
            ("XHOLD", "HOLDİNG ENDEKSİ", "HOLDİNG"),
            ("XBLSM", "BİLİŞİM ENDEKSİ", "BİLİŞİM"),
            ("XULAS", "ULAŞTIRMA ENDEKSİ", "ULAŞTIRMA"),
            ("XKMYA", "KİMYA ENDEKSİ", "KİMYA"),
            ("XGIDA", "GIDA ENDEKSİ", "GIDA")
        ]

        for code, name, kat in target_indices:
            sub_df = df_res if kat == "TÜM BIST" else df_res[df_res["Sektör_Kategori"] == kat]
            if not sub_df.empty:
                avg_change = sub_df["Değişim (%)"].mean()
                avg_rsi = sub_df["RSI"].mean()
                tight_ratio = sub_df["Band_Tight"].mean()

                sikisma_txt = "🔥 VAR" if tight_ratio >= 0.25 else "HAYIR"

                if avg_rsi <= 38.0 and avg_change >= -0.2:
                    idx_sinyal = "🔄 DİP DÖNÜŞÜ WESS (DİPTE)"
                elif avg_change >= 0.8 and avg_rsi >= 52.0:
                    idx_sinyal = "🚀 ŞU AN GİR (KALKIŞ VAR)"
                elif sikisma_txt == "🔥 VAR":
                    idx_sinyal = "🔥 SIKIŞIYOR (Sıkışma Yüksek)"
                elif avg_change > 0:
                    idx_sinyal = "💎 GÜÇLÜ (Pozitif Trend)"
                else:
                    idx_sinyal = "👀 İZLEMEDE KAL (Nötr)"

                index_results.append({
                    "Endeks Kodu": code,
                    "Endeks Adı": name,
                    "Ort Değişim (%)": round(avg_change, 2),
                    "RSI (14)": round(avg_rsi, 1),
                    "Sıkışma": sikisma_txt,
                    "ENDEKS AKSİYON SİNYALİ": idx_sinyal
                })

    return pd.DataFrame(results), pd.DataFrame(index_results)

# Verileri Çek
with st.spinner("BİST Verileri Taranıyor..."):
    df_hisseler, df_endeksler = canli_bist_tara(secili_periyot)

# ---------------------------------------------------------
# 3. PANELLER VE TABLOLAR
# ---------------------------------------------------------

st.subheader("🏛️ BIST Endeks Canlı Sinyal Paneli")
if not df_endeksler.empty:
    st.dataframe(df_endeksler, use_container_width=True, hide_index=True)

if not df_hisseler.empty:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🚀 ŞU AN GİR", len(df_hisseler[df_hisseler["Tag"] == "KALKIS"]))
    c2.metric("🔄 DİP DÖNÜŞÜ", len(df_hisseler[df_hisseler["Tag"] == "DIP_DONUS"]))
    c3.metric("💎 GÜÇLÜ AL", len(df_hisseler[df_hisseler["Tag"] == "GUC_AL"]))
    c4.metric("🔥 SIKIŞIYOR", len(df_hisseler[df_hisseler["Tag"] == "SIKISMA"]))
    c5.metric("👀 İZLEMEDE KAL", len(df_hisseler[df_hisseler["Tag"] == "IZLE"]))
    c6.metric("⚠️ UZAK DUR", len(df_hisseler[df_hisseler["Tag"] == "UZAK_DUR"]))

filtered_df = df_hisseler.copy()

if secili_sektor != "TÜM BIST":
    sektor_anahtar = secili_sektor.split(" ")[0]
    filtered_df = filtered_df[filtered_df["Sektör_Kategori"] == sektor_anahtar]

if search_query:
    filtered_df = filtered_df[filtered_df["Hisse"].str.contains(search_query, na=False)]

st.subheader("🚀 ŞU AN GİR (Kalkışa Geçen Hacimli Hisseler)")
kalkis_df = filtered_df[filtered_df["Tag"] == "KALKIS"]
if not kalkis_df.empty:
    st.dataframe(
        kalkis_df[["Hisse", "Sektör Gücü", "Skor", "Son Fiyat (TL)", "Hacim (TL)", "Değişim (%)", "AOF Farkı (%)", "NET AKSİYON SİNYALİ"]], 
        use_container_width=True, 
        hide_index=True
    )
else:
    st.info("Şu an 'KALKIŞ' kriterlerine uyan hisse bulunamadı.")

st.subheader("📊 Genel BİST Akümülasyon ve Sinyal Listesi")
if not filtered_df.empty:
    st.dataframe(
        filtered_df[["Hisse", "Sektör Gücü", "Skor", "Son Fiyat (TL)", "Hacim (TL)", "Değişim (%)", "AOF Farkı (%)", "NET AKSİYON SİNYALİ"]], 
        use_container_width=True, 
        hide_index=True
    )
else:
    st.warning("Filtreleme kriterlerinize uygun hisse verisi bulunamadı.")