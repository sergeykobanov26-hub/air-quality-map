"""Визуализация данных о речном стоке."""

import json
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import plotly.io as pio

pio.templates.default = "plotly_dark"

# Путь к файлу с геометрией рек (Natural Earth)
RIVERS_GEOJSON = Path("data/natural_earth/ne_10m_rivers_lake_centerlines.geojson")


def get_discharge_color(value, min_val, max_val):
    """Возвращает цвет маркера по величине стока."""
    if value is None or pd.isna(value):
        return "#808080"
    if max_val == min_val:
        return "#2196F3"
    ratio = (value - min_val) / (max_val - min_val)
    r = int(179 + (13 - 179) * ratio)
    g = int(229 + (71 - 229) * ratio)
    b = int(252 + (161 - 252) * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


def create_river_map(df, metric="river_discharge"):
    """
    Создаёт карту с линиями рек (Natural Earth) и точками расчёта стока.
    """
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="OpenStreetMap",
    )

    # --- Слой с линиями рек (только в границах России) ---
    if RIVERS_GEOJSON.exists():
        with open(RIVERS_GEOJSON, "r", encoding="utf-8") as f:
            rivers_geojson = json.load(f)

        # Оставляем только фичи, попадающие в границы России
        filtered_features = []
        for feature in rivers_geojson.get("features", []):
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [])
            if not coords:
                continue

            # Для LineString: coords = [[lon, lat], [lon, lat], ...]
            # Для MultiLineString: coords = [[[lon, lat], ...], ...]
            first_point = None
            if geom.get("type") == "LineString" and len(coords) > 0:
                first_point = coords[0]
            elif geom.get("type") == "MultiLineString" and len(coords) > 0:
                if len(coords[0]) > 0:
                    first_point = coords[0][0]

            if first_point and len(first_point) >= 2:
                lon, lat = first_point[0], first_point[1]
                if 19 <= lon <= 190 and 41 <= lat <= 82:
                    filtered_features.append(feature)

        filtered_geojson = {
            "type": "FeatureCollection",
            "features": filtered_features,
        }

        folium.GeoJson(
            filtered_geojson,
            name="Речная сеть (Natural Earth)",
            style_function=lambda x: {
                "color": "#1E88E5",
                "weight": 1.5,
                "opacity": 0.5,
            },
        ).add_to(m)

    # --- Слой с точками расчёта стока ---
    values = df[metric].fillna(0)
    min_val = values.min()
    max_val = values.max()

    for _, row in df.iterrows():
        value = row.get(metric)
        if value is None or pd.isna(value):
            continue

        color = get_discharge_color(value, min_val, max_val)

        popup_text = f"""
        <div style="font-family: sans-serif; font-size: 13px;">
            <b>{row['river']}</b><br>
             Регион: {row.get('region', '—')}<br>
            Ближайший город: {row.get('nearest_city', '—')}<br>
            Сток: <b>{value:.0f} м³/с</b><br>
            <span style="color: #888;">{row['time'].strftime('%d.%m.%Y')}</span>
        </div>
        """

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=8,
            popup=popup_text,
            tooltip=f"{row['river']}: {value:.0f} м³/с",
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
        ).add_to(m)

    folium.LayerControl().add_to(m)

    return m


def plot_discharge_timeseries(df):
    """График динамики стока по рекам."""
    fig = px.line(
        df,
        x="time",
        y="river_discharge",
        color="river",
        title="Динамика речного стока",
        labels={
            "time": "Дата",
            "river_discharge": "Сток, м³/с",
            "river": "Река",
        },
    )
    fig.update_layout(hovermode="x unified", height=500)
    return fig


def plot_discharge_bar(df):
    """Столбчатая диаграмма среднего стока по рекам."""
    avg = (
        df.groupby("river")["river_discharge"]
          .mean()
          .sort_values(ascending=False)
          .reset_index()
    )

    fig = px.bar(
        avg,
        x="river",
        y="river_discharge",
        title="Средний сток по рекам",
        labels={"river": "Река", "river_discharge": "Сток, м³/с"},
        color="river_discharge",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=500, showlegend=False)
    return fig