from __future__ import annotations

import os

import httpx
import streamlit as st

API_URL = os.getenv('UI_API_URL', 'http://127.0.0.1:8000')

st.set_page_config(page_title='CSV Data Agent', layout='wide')
st.title('CSV Data Agent')
st.caption('Paste CSV and get a quick column profile (MVP of repeatable data-agent preprocessing).')

csv_text = st.text_area('CSV', value='city,population
Taipei,2500000
Taichung,2800000
Kaohsiung,2700000
', height=160)

if st.button('Profile'):
    with httpx.Client(base_url=API_URL, timeout=10.0) as client:
        r = client.post('/api/csv/profile', json={'csv_text': csv_text})
        st.json(r.json())
