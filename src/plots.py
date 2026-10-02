"""Функции визуализации для проекта качества воздуха."""

import folium
import pandas as pd
import plotly.express as px
import plotly.io as pio

from src.labels import (
    get_pollutant_label,
    get_pollutant_unit,
    get_standards,
)

# Тёмная тема Plotly по умолчанию
pio.templates.default = "plotly_dark"


# Цветовая шкала для AQI (упрощённая)
AQI_COLORS = {
    "good":           "#00e400",
    "moderate":       "#ffff00",
    "unhealthy_sg":   "#ff7e00",
    "unhealthy":      "#ff0000",
    "very_unhealthy": "#8f3f97",
    "hazardous":      "#7e0023",
}


def get_aqi_color(pm25):
    """Возвращает цвет маркера по значению PM2.5 (мкг/м³)."""
    if pm25 is None or pd.isna(pm25):
        return "#808080"
    if pm25 <= 12:
        return AQI_COLORS["good"]
    if pm25 <= 35.4:
        return AQI_COLORS["moderate"]
    if pm25 <= 55.4:
        return AQI_COLORS["unhealthy_sg"]
    if pm25 <= 150.4:
        return AQI_COLORS["unhealthy"]
    if pm25 <= 250.4:
        return AQI_COLORS["very_unhealthy"]
    return AQI_COLORS["hazardous"]


def create_map(df, pollutant="pm2_5"):
    """Создаёт интерактивную карту с точками городов."""
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="OpenStreetMap",
    )

    label = get_pollutant_label(pollutant)
    unit = get_pollutant_unit(pollutant)

    for _, row in df.iterrows():
        value = row.get(pollutant)
        if value is None or pd.isna(value):
            continue

        color = get_aqi_color(value)

        popup_text = f"""
        <div style="font-family: sans-serif; font-size: 13px;">
            <b>{row['city']}</b><br>
            {label}: <b>{value:.1f} {unit}</b><br>
            <span style="color: #888;">{row['time'].strftime('%d.%m.%Y %H:%M')}</span>
        </div>
        """

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=10,
            popup=popup_text,
            tooltip=f"{row['city']}: {value:.1f} {unit}",
            color=color,
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
        ).add_to(m)

    return m


def plot_timeseries(df, pollutant="pm2_5", cities=None):
    """Строит график динамики загрязнителя с линиями норм."""
    if cities:
        df = df[df["city"].isin(cities)]

    label = get_pollutant_label(pollutant)
    unit = get_pollutant_unit(pollutant)
    standards = get_standards(pollutant)

    fig = px.line(
        df,
        x="time",
        y=pollutant,
        color="city",
        title=f"Динамика {label} по городам",
        labels={
            "time": "Дата",
            pollutant: f"{label}, {unit}",
            "city": "Город",
        },
    )

    if standards:
        who_val = standards.get("who")
        ru_val = standards.get("ru")

        if who_val:
            fig.add_hline(
                y=who_val,
                line_dash="dot",
                line_color="orange",
                annotation_text=f"Норма ВОЗ: {who_val} {unit}",
                annotation_position="top right",
            )
        if ru_val:
            fig.add_hline(
                y=ru_val,
                line_dash="dash",
                line_color="red",
                annotation_text=f"ПДК России: {ru_val} {unit}",
                annotation_position="bottom right",
            )

    fig.update_layout(hovermode="x unified", height=500)
    return fig


def plot_bar_avg(df, pollutant="pm2_5"):
    """Строит столбчатую диаграмму средних значений по городам."""
    label = get_pollutant_label(pollutant)
    unit = get_pollutant_unit(pollutant)

    avg = df.groupby("city")[pollutant].mean().sort_values(ascending=False).reset_index()

    fig = px.bar(
        avg,
        x="city",
        y=pollutant,
        title=f"Средний уровень {label} по городам",
        labels={"city": "Город", pollutant: f"{label}, {unit}"},
        color=pollutant,
        color_continuous_scale="RdYlGn_r",
    )
    fig.update_layout(height=500)
    return fig


def plot_distribution(df, pollutant="pm2_5"):
    """Строит гистограмму распределения загрязнителя."""
    label = get_pollutant_label(pollutant)
    unit = get_pollutant_unit(pollutant)

    fig = px.histogram(
        df,
        x=pollutant,
        nbins=50,
        title=f"Распределение {label}",
        labels={pollutant: f"{label}, {unit}"},
    )
    fig.update_layout(height=400)
    return fig