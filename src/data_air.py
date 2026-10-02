"""Загрузка данных о качестве воздуха из Open-Meteo Air Quality API."""

import requests
import pandas as pd

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Загрязнители, которые запрашиваем
POLLUTANTS = [
    "pm10", "pm2_5", "carbon_monoxide",
    "nitrogen_dioxide", "sulphur_dioxide", "ozone",
]


def fetch_city_air(city, lat, lon, past_days=7, forecast_days=3):
    """Скачивает данные о качестве воздуха для одного города."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(POLLUTANTS),
        "timezone": "auto",
        "past_days": past_days,
        "forecast_days": forecast_days,
    }

    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df["city"] = city
    df["latitude"] = lat
    df["longitude"] = lon

    return df


def fetch_cities(cities_df, past_days=7, forecast_days=0, progress_callback=None):
    """
    Скачивает данные для списка городов.

    Parameters
    ----------
    cities_df : pd.DataFrame
        Должен содержать колонки: city, lat, lon.
    past_days : int
        Сколько дней истории.
    forecast_days : int
        Сколько дней прогноза.
    progress_callback : callable, optional
        Функция, которая вызывается после каждого города
        (например, для обновления прогресс-бара в Streamlit).

    Returns
    -------
    pd.DataFrame
        Объединённые данные по всем городам.
    """
    all_data = []
    total = len(cities_df)

    for i, (_, row) in enumerate(cities_df.iterrows(), start=1):
        try:
            df = fetch_city_air(
                row["city"], row["lat"], row["lon"],
                past_days=past_days, forecast_days=forecast_days,
            )
            all_data.append(df)
        except Exception as e:
            print(f"Ошибка для {row['city']}: {e}")

        if progress_callback:
            progress_callback(i, total)

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)