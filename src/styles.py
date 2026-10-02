"""Общие стили для всех страниц приложения."""

import streamlit as st


def apply_custom_css():
    """Применяет общий CSS ко всей странице."""
    st.markdown("""
    <style>
        /* ---------- Общие цвета ---------- */
        :root {
            --bg: #1E1E1E;
            --bg-secondary: #2A2A2A;
            --bg-card: #333333;
            --text: #E8E8E8;
            --text-muted: #A0A0A0;
            --accent: #1E88E5;
            --border: rgba(255, 255, 255, 0.1);
        }

        /* ---------- Заголовки ---------- */
        h1 {
            font-weight: 600;
            letter-spacing: -0.5px;
            color: var(--text);
        }
        h2 {
            font-weight: 500;
            margin-top: 2rem;
            color: var(--text);
            border-bottom: 2px solid var(--accent);
            padding-bottom: 0.5rem;
        }
        h3 {
            font-weight: 500;
            color: var(--text);
        }

        /* ---------- Сайдбар ---------- */
        [data-testid="stSidebar"] {
            background-color: var(--bg-secondary) !important;
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] * {
            color: var(--text) !important;
        }
        
        /* Убираем подчёркивание у заголовков внутри сайдбара */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            border-bottom: none !important;
            padding-bottom: 0 !important;
            margin-bottom: 0.5rem !important;
        }

        /* ---------- Мультиселект ---------- */
        [data-baseweb="select"] > div {
            background-color: var(--bg-card) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
        }
        [data-baseweb="select"] * {
            color: var(--text) !important;
        }
        [data-baseweb="popover"] {
            background-color: var(--bg-card) !important;
        }
        [data-baseweb="popover"] * {
            color: var(--text) !important;
        }
        [data-baseweb="menu"] {
            background-color: var(--bg-card) !important;
        }
        [data-baseweb="menu"] li:hover {
            background-color: var(--bg-secondary) !important;
        }

        /* ---------- Слайдер ---------- */
        [data-testid="stSlider"] * {
            color: var(--text) !important;
        }
        [data-testid="stSliderThumbValue"] {
            color: var(--accent) !important;
            font-weight: 600 !important;
        }
        [data-testid="stSliderTickBarMin"],
        [data-testid="stSliderTickBarMax"] {
            color: #90CAF9 !important;
        }

        /* ---------- Expander ---------- */
        [data-testid="stExpander"] {
            background-color: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
        }
        [data-testid="stExpander"] * {
            color: var(--text) !important;
        }

        /* ---------- Метрики ---------- */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 600;
            color: var(--text) !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted) !important;
        }
        [data-testid="metric-container"] {
            background-color: var(--bg-secondary);
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid var(--border);
        }

        /* ---------- Таблица ---------- */
        [data-testid="stDataFrame"] {
            background-color: var(--bg-secondary) !important;
        }
        [data-testid="stDataFrame"] * {
            color: var(--text) !important;
        }

        /* ---------- Плашки ---------- */
        [data-testid="stAlert"] {
            border-radius: 8px;
        }

        /* ---------- Отступы ---------- */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 1px solid var(--border);
        }
    </style>
    """, unsafe_allow_html=True)