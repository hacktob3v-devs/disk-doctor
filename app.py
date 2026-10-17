"""DiskDoctor — Streamlit entry point. Run: streamlit run app.py"""
import json
import os

import streamlit as st

USE_MOCKS = os.getenv("USE_MOCKS", "1") == "1"

if USE_MOCKS:
    from core import mocks as triage_mod
    from core import mocks as parser_mod
    from core import mocks as model_mod
    from core import mocks as report_mod
else:
    from core import triage as triage_mod          # Kişi 2
    from core import smart_parser as parser_mod    # Kişi 1
    from core import disk_model as model_mod       # Kişi 1
    from core import report as report_mod          # Kişi 2

st.set_page_config(page_title="DiskDoctor", page_icon="💽", layout="wide")

with st.sidebar:
    st.title("DiskDoctor")
    shop = st.text_input("Dükkân adı", "Örnek Bilgisayar")
    st.caption("Mock modu açık" if USE_MOCKS else "Gerçek modeller")

tab_triage, tab_disk = st.tabs(["Ön Teşhis", "Disk Sağlığı"])

with tab_triage:
    complaint = st.text_area("Müşteri şikâyeti")
    if st.button("Ön teşhis koy") and complaint.strip():
        st.json(triage_mod.triage(complaint))   # TODO(Kişi 3): kart tasarımı

with tab_disk:
    uploaded = st.file_uploader("smartctl -j çıktısı", type=["json"])
    if uploaded is not None:
        disk = parser_mod.parse(json.load(uploaded))
        risk = model_mod.predict(disk)          # TODO: NVMe → nvme_rules.score
        st.json(risk)                           # TODO(Kişi 3): risk göstergesi
        st.markdown(report_mod.customer_report(shop, disk, risk, None))
