"""Загрузка справочника рек России из CSV."""

from pathlib import Path
import pandas as pd

RIVERS_FILE = Path("data/russian_rivers.csv")


def load_rivers():
    """Загружает справочник рек из CSV."""
    if not RIVERS_FILE.exists():
        raise FileNotFoundError(
            f"Файл {RIVERS_FILE} не найден. "
            "Положите russian_rivers.csv в папку data/."
        )
    return pd.read_csv(RIVERS_FILE, encoding="utf-8")


def get_default_rivers(df, count=10):
    """Возвращает первые N рек (по умолчанию 10)."""
    return df["river"].head(count).tolist()


if __name__ == "__main__":
    df = load_rivers()
    print(f"Всего рек: {len(df)}")
    print(df.head(10).to_string(index=False))