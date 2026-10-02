"""Точка входа: настройка и навигация."""

import streamlit as st

from src.styles import apply_custom_css


st.set_page_config(
    page_title="Аналитическая платформа России",
    page_icon="🌍",
    layout="wide",
)

apply_custom_css()

# --- Определяем страницы с иконками и названиями ---
home_page = st.Page(
    "pages/0_Главная.py",
    title="Главная",
    icon="🏠",
    default=True,
)
air_page = st.Page(
    "pages/1_Качество_воздуха.py",
    title="Качество воздуха",
    icon="🌫️",
)
flood_page = st.Page(
    "pages/2_Паводки_и_наводнения.py",
    title="Паводки и наводнения",
    icon="🌊",
)

# --- Запускаем навигацию ---
pg = st.navigation([home_page, air_page, flood_page])
pg.run()