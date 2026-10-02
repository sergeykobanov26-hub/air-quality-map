"""Загрузка справочника городов России из CSV-файла."""

from pathlib import Path

import pandas as pd

# Путь к файлу со списком городов
CITIES_FILE = Path("data/russian_cities.csv")


def load_cities():
    """
    Загружает справочник городов России из CSV.

    Returns
    -------
    pd.DataFrame
        Колонки: city, lat, lon, population, federal_district, region_name.
    """
    if not CITIES_FILE.exists():
        raise FileNotFoundError(
            f"Файл {CITIES_FILE} не найден. "
            "Положите russian_cities.csv в папку data/."
        )

    df = pd.read_csv(CITIES_FILE, encoding="utf-8")
    return df


def get_cities_by_district(df, district):
    """Возвращает список городов в выбранном федеральном округе."""
    return df[df["federal_district"] == district]["city"].tolist()


def get_districts(df):
    """Возвращает отсортированный список федеральных округов."""
    return sorted(df["federal_district"].unique().tolist())


def get_default_cities(df, count=10):
    """Возвращает топ-N городов по населению (для значений по умолчанию)."""
    top = df.nlargest(count, "population")
    return top["city"].tolist()


if __name__ == "__main__":
    df = load_cities()
    print(f"Всего городов: {len(df)}")
    print(f"Федеральных округов: {len(get_districts(df))}")
    print("\nТоп-10 по населению:")
    print(df.nlargest(10, "population")[["city", "population", "federal_district"]].to_string(index=False))