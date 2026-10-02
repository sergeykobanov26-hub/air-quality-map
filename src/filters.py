"""Функции фильтрации и агрегации данных о качестве воздуха."""

import pandas as pd

from src.labels import STATS_LABELS


def filter_by_cities(df, cities):
    """Оставляет только выбранные города."""
    if not cities:
        return df
    return df[df["city"].isin(cities)].copy()


def filter_by_pollutant(df, pollutant):
    """Оставляет только строки, где есть значение выбранного загрязнителя."""
    if pollutant not in df.columns:
        raise ValueError(f"Загрязнитель '{pollutant}' не найден в данных")
    return df.dropna(subset=[pollutant]).copy()


def filter_by_date_range(df, start_date, end_date):
    """Фильтрует по диапазону дат (включительно)."""
    mask = (df["time"] >= pd.to_datetime(start_date)) & \
           (df["time"] <= pd.to_datetime(end_date))
    return df[mask].copy()


def get_city_current(df):
    """Возвращает последнее значение по каждому городу."""
    return (
        df.sort_values("time")
          .groupby("city", as_index=False)
          .tail(1)
          .reset_index(drop=True)
    )


def get_city_stats(df):
    """
    Возвращает средние, мин и макс по каждому городу
    для всех загрязнителей.
    """
    pollutants = [c for c in df.columns
                  if c not in ("time", "city", "latitude", "longitude")]

    stats = df.groupby("city")[pollutants].agg(["mean", "min", "max"]).round(2)

    # Переводим названия статистических колонок на русский
    stats.columns = [
        f"{col[0]} — {STATS_LABELS.get(col[1], col[1])}"
        for col in stats.columns
    ]

    return stats


from src.labels import get_standards, get_pollutant_label


def analyze_data(df, pollutant, past_days):
    """
    Формирует выводы по данным: превышения норм, лидеры, статистика.
    
    Returns
    -------
    dict с ключами:
        - total_cities, total_records
        - mean_value, max_value, max_city
        - min_value, min_city
        - who_exceed_count, ru_exceed_count
        - exceed_ratio_who, exceed_ratio_ru
    """
    standards = get_standards(pollutant)
    who_norm = standards.get("who")
    ru_norm = standards.get("ru")

    result = {
        "total_cities": df["city"].nunique(),
        "total_records": len(df),
        "mean_value": df[pollutant].mean(),
        "max_value": df[pollutant].max(),
        "min_value": df[pollutant].min(),
        "who_norm": who_norm,
        "ru_norm": ru_norm,
    }

    # Город с максимумом и минимумом
    max_row = df.loc[df[pollutant].idxmax()]
    min_row = df.loc[df[pollutant].idxmin()]
    result["max_city"] = max_row["city"]
    result["min_city"] = min_row["city"]

    # Превышения норм по каждому городу (по среднему значению)
    city_avg = df.groupby("city")[pollutant].mean()

    if who_norm:
        exceed_who = city_avg[city_avg > who_norm]
        result["who_exceed_count"] = len(exceed_who)
        result["who_exceed_cities"] = exceed_who.sort_values(ascending=False).index.tolist()
    else:
        result["who_exceed_count"] = None

    if ru_norm:
        exceed_ru = city_avg[city_avg > ru_norm]
        result["ru_exceed_count"] = len(exceed_ru)
        result["ru_exceed_cities"] = exceed_ru.sort_values(ascending=False).index.tolist()
    else:
        result["ru_exceed_count"] = None

    return result