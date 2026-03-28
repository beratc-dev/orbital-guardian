from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="AETHRA – Orbital Guardian AI", layout="wide")

st.title("AETHRA – Orbital Guardian AI")
st.caption("Türk uyduları için uzay çöpü yakınlaşma analizi ve risk sıralaması")

csv_path = Path("outputs/conjunction_events.csv")
if not csv_path.exists():
    st.warning("Önce `python main.py --targets ...` komutunu çalıştır.")
    st.stop()

df = pd.read_csv(csv_path)
if df.empty:
    st.info("Henüz olay bulunamadı.")
    st.stop()

st.metric("Toplam olay", len(df))
st.metric("En yüksek risk", round(float(df['risk_score'].max()), 2))

top_n = st.slider("Gösterilecek olay sayısı", min_value=5, max_value=min(50, len(df)), value=min(15, len(df)))
filtered = df.sort_values("risk_score", ascending=False).head(top_n)

st.subheader("Top Risk Olayları")
st.dataframe(
    filtered[
        [
            "target_name",
            "object_name",
            "object_source",
            "risk_score",
            "tca_utc",
            "miss_distance_km",
            "relative_speed_kms",
        ]
    ],
    use_container_width=True,
)

selected_index = st.selectbox("Detay görmek için olay seç", options=filtered.index.tolist())
selected = df.loc[selected_index]

st.subheader("Olay Detayı")
col1, col2, col3 = st.columns(3)
col1.metric("Risk Skoru", round(float(selected["risk_score"]), 2))
col2.metric("Minimum Mesafe (km)", round(float(selected["miss_distance_km"]), 3))
col3.metric("Göreli Hız (km/s)", round(float(selected["relative_speed_kms"]), 3))

st.write("**Hedef Uydu:**", selected["target_name"])
st.write("**Karşı Nesne:**", selected["object_name"])
st.write("**Kaynak Grup:**", selected["object_source"])
st.write("**En Yakın Yaklaşma Zamanı:**", selected["tca_utc"])

st.subheader("Karar Destek Notu")
risk = float(selected["risk_score"])
if risk >= 80:
    st.error("Kritik olay: Operatör incelemesi ve kaçınma değerlendirmesi önerilir.")
elif risk >= 50:
    st.warning("Orta-yüksek risk: Yakın takip ve yeni TLE güncellemesi ile doğrulama önerilir.")
else:
    st.success("Düşük-orta risk: İzleme modunda kalınabilir.")
