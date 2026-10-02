"""Загрузка данных о речном стоке из Open-Meteo Flood API."""

import requests
import pandas as pd

API_URL = "https://flood-api.open-meteo.com/v1/flood"


def fetch_river_discharge(river, lat, lon, past_days=30, forecast_days=30):
    """
    Скачивает данные о речном стоке для одной реки.

    Parameters
    ----------
    river : str
        Название реки.
    lat, lon : float
        Координаты точки на реке.
    past_days : int
        Сколько дней истории (максимум 92).
    forecast_days : int
        Сколько дней прогноза (максимум 210).

    Returns
    -------
    pd.DataFrame
        Колонки: time, river_discharge, river, latitude, longitude.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "river_discharge,river_discharge_mean,river_discharge_max,river_discharge_min",
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "auto",
    }

    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data["daily"])
    df["time"] = pd.to_datetime(df["time"])
    df["river"] = river
    df["latitude"] = lat
    df["longitude"] = lon

    return df


def fetch_rivers(rivers_df, past_days=30, forecast_days=30, delay=0.5):
    """
    Скачивает данные для списка рек с паузой между запросами.
    Добавляет колонки region и nearest_city.
    """
    import time

    all_data = []
    total = len(rivers_df)

    for i, (_, row) in enumerate(rivers_df.iterrows(), start=1):
        try:
            df = fetch_river_discharge(
                row["river"], row["lat"], row["lon"],
                past_days=past_days, forecast_days=forecast_days,
            )
            # Добавляем регион и город из справочника
            df["region"] = row.get("region", "")
            df["nearest_city"] = row.get("nearest_city", "")
            all_data.append(df)
        except Exception as e:
            print(f"Ошибка для {row['river']}: {e}")

        if i < total:
            time.sleep(delay)

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)


if __name__ == "__main__":
    # Тестовый запуск: 3 реки, 7 дней истории, 7 прогноза
    test_rivers = pd.DataFrame([
        {"river": "Волга", "lat": 48.7080, "lon": 44.5133},
        {"river": "Обь",   "lat": 55.0084, "lon": 82.9357},
        {"river": "Лена",  "lat": 62.0281, "lon": 129.7326},
    ])

    df = fetch_rivers(test_rivers, past_days=7, forecast_days=7)

    print(f"\nВсего записей: {len(df)}")
    print(f"Колонки: {list(df.columns)}")
    print(f"\nПервые строки:")
    print(df.head(10).to_string(index=False))

    print(f"\nСредний сток по рекам:")
    print(df.groupby("river")["river_discharge"].mean().round(1))