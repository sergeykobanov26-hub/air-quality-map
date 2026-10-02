"""Страница: паводки и наводнения в России."""

import pandas as pd
import streamlit as st

from streamlit_folium import st_folium
from src.data_flood import fetch_rivers
from src.plots_flood import (
    create_river_map,
    plot_discharge_bar,
    plot_discharge_timeseries,
)
from src.rivers import get_default_rivers, load_rivers

st.title("Паводки и наводнения")
st.caption("Прогноз речного стока на основе Open-Meteo Flood API")


# ---------- Загрузка справочника рек ----------
@st.cache_data
def get_rivers_df():
    return load_rivers()


rivers_df = get_rivers_df()


# ---------- Загрузка данных о стоке ----------
@st.cache_data(ttl=3600)
def load_flood_data(river_names_tuple, past_days, forecast_days):
    rivers_to_fetch = rivers_df[rivers_df["river"].isin(river_names_tuple)]
    return fetch_rivers(
        rivers_to_fetch, past_days=past_days, forecast_days=forecast_days
    )


# ---------- Боковая панель ----------
st.sidebar.header("Фильтры")

past_days = st.sidebar.slider("История (дней назад)", 7, 92, 30)
forecast_days = st.sidebar.slider("Прогноз (дней вперёд)", 0, 60, 14)

default_rivers = get_default_rivers(rivers_df, count=10)
selected_rivers = st.sidebar.multiselect(
    "Реки",
    options=rivers_df["river"].tolist(),
    default=default_rivers,
)

with st.sidebar.expander("О проекте и данных"):
    st.markdown("""
    **Источники данных:**
    - **Речной сток:** [Open-Meteo Flood API](https://open-meteo.com/en/docs/flood-api) —
      глобальная гидрологическая модель GloFAS (Copernicus Emergency Management Service).
    - **Справочник рек:** координаты ключевых точек на реках России.
    - **Геометрия рек (линии):** [Natural Earth](https://www.naturalearthdata.com/)
      (public domain) — открытые картографические данные.

    **Ограничения:**
    Данные о стоке являются **модельными** и представляют собой оценку для
    конкретной точки на реке (разрешение модели ~5 км), а не измерения с
    реальных гидропостов. Они подходят для общей оценки ситуации и
    выявления тенденций.
    """)


# ---------- Проверка выбора ----------
if not selected_rivers:
    st.warning("Выберите хотя бы одну реку в боковой панели.")
    st.stop()


# ---------- Загрузка ----------
with st.spinner(f"Загрузка данных для {len(selected_rivers)} рек..."):
    df = load_flood_data(tuple(selected_rivers), past_days, forecast_days)


if df.empty:
    st.error("Не удалось загрузить данные. Попробуйте позже.")
    st.stop()


# ---------- KPI ----------
st.header("Ключевые показатели")

today = df["time"].max() - pd.Timedelta(days=forecast_days)
current = (
    df[df["time"] <= today]
    .groupby(["river", "latitude", "longitude"], as_index=False)
    .tail(1)
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Рек", df["river"].nunique())
with col2:
    st.metric("Записей", f"{len(df):,}".replace(",", " "))
with col3:
    st.metric("Средний сток", f"{df['river_discharge'].mean():.0f} м³/с")
with col4:
    max_row = df.loc[df["river_discharge"].idxmax()]
    st.metric(
        "Максимум",
        f"{max_row['river_discharge']:.0f} м³/с",
        help=f"Река: {max_row['river']}",
    )


# ---------- Карта ----------
st.header("Карта речного стока")

map_key = f"flood_map_{len(selected_rivers)}_{past_days}_{forecast_days}"
m = create_river_map(current, metric="river_discharge")
st_folium(m, height=500, width="stretch", returned_objects=[], key=map_key)

# Легенда
st.markdown("**Уровень стока (м³/с):**")
legend_cols = st.columns(4)
legend_items = [
    ("#B3E5FC", "Низкий",      "Межень (минимальный сток)"),
    ("#4FC3F7", "Средний",     "Обычный уровень"),
    ("#1E88E5", "Повышенный",  "Возможен рост воды"),
    ("#0D47A1", "Высокий",     "Риск паводка"),
]
for col, (color, level, desc) in zip(legend_cols, legend_items):
    with col:
        st.markdown(
            f'<div style="font-size: 26px; color: {color}; line-height: 1;">●</div>'
            f'<b>{level}</b><br>{desc}',
            unsafe_allow_html=True,
        )

# Пояснения
st.info(
    "**Что показывает карта?** "
    "Синие линии — это речная сеть России (данные Natural Earth). "
    "Цветные точки — участки рек, для которых модель GloFAS рассчитывает "
    "речной сток. Чем темнее синий цвет точки — тем больше воды проходит "
    "через этот участок. Данные относятся к конкретной точке, а не ко всей реке."
)

st.info(
    "**Что такое паводок и как оценивается риск?** "
    "Паводок — это резкий подъём уровня воды, вызванный дождями, таянием "
    "снегов или заторами льда. В этом приложении риск оценивается по прогнозу "
    "речного стока: если прогнозируемый сток превышает средний уровень на "
    "**20% и более** — возможен рост воды и риск подтопления. "
    "Данные являются модельными (разрешение ~5 км) и подходят для общей "
    "оценки ситуации, но не заменяют данные гидропостов Росгидромета."
)

# ---------- Графики ----------
st.header("Динамика во времени")

fig_ts = plot_discharge_timeseries(df)
st.plotly_chart(fig_ts, use_container_width=True)
st.caption(
    f"История за последние **{past_days}** дней + прогноз на **{forecast_days}** "
    "дней вперёд. Резкие пики на графике могут указывать на риск паводка."
)

st.subheader("Сравнение по рекам")
fig_bar = plot_discharge_bar(df)
st.plotly_chart(fig_bar, use_container_width=True)
st.caption(
    "Средний сток за весь выбранный период. Чем выше столбец — тем больше "
    "воды несёт река."
)


# ---------- Таблица ----------
st.header("Статистика по рекам")

stats = (
    df.groupby(["river", "region", "nearest_city"])["river_discharge"]
    .agg(["mean", "min", "max"])
    .round(0)
    .reset_index()
)
stats.columns = ["Река", "Регион", "Ближайший город",
                 "Средний сток", "Минимум", "Максимум"]
st.dataframe(stats, use_container_width=True)


# ---------- Выводы ----------
st.header("Выводы")

st.markdown(
    f"Анализ по **{df['river'].nunique()}** рекам за период "
    f"{past_days + forecast_days} дней."
)

top_rivers = df.groupby("river")["river_discharge"].mean().nlargest(3)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Наибольший средний сток:**")
    for river, value in top_rivers.items():
        st.markdown(f"- **{river}** — {value:.0f} м³/с")

with col2:
    st.markdown("**Наименьший средний сток:**")
    bottom_rivers = df.groupby("river")["river_discharge"].mean().nsmallest(3)
    for river, value in bottom_rivers.items():
        st.markdown(f"- **{river}** — {value:.0f} м³/с")

if forecast_days > 0:
    history = df[df["time"] <= today]
    forecast = df[df["time"] > today]

    if not forecast.empty and not history.empty:
        growth = (
            forecast.groupby("river")["river_discharge"].max()
            / history.groupby("river")["river_discharge"].mean()
        ).round(2)

        growing = growth[growth > 1.2].sort_values(ascending=False)

        st.markdown("**Прогноз роста стока (>20% от среднего):**")
        if not growing.empty:
            # Для каждой растущей реки — регион и город
            warning_rows = []
            for river, ratio in growing.items():
                info = df[df["river"] == river].iloc[0]
                region = info.get("region", "—")
                city = info.get("nearest_city", "—")

                st.markdown(
                    f"- **{river}** — рост в **{ratio}×** раз  \n"
                    f"  Регион: {region} · Ближайший город: {city}"
                )
                warning_rows.append(f"{region} ({city})")

            st.warning(
                f"В ближайшие **{forecast_days}** дней ожидается рост стока "
                f"на **{len(growing)}** реках. Возможен риск подтопления "
                f"в следующих регионах:\n\n"
                + " · ".join(warning_rows)
            )
        else:
            st.success(
                f"Значительного роста стока в ближайшие {forecast_days} дней "
                "не прогнозируется. Ситуация стабильная."
            )

# ---------- Источники данных ----------
with st.expander("Откуда взяты данные"):
    st.markdown("""
    **Речной сток:**
    [Open-Meteo Flood API](https://open-meteo.com/en/docs/flood-api) — глобальная
    гидрологическая модель **GloFAS** (Global Flood Awareness System), разработанная
    в рамках программы **Copernicus Emergency Management Service** (Евросоюз).
    Разрешение модели — ~5 км. Данные обновляются ежедневно: прогноз до 210 дней.

    **Речная сеть (синие линии на карте):**
    [Natural Earth](https://www.naturalearthdata.com/) — открытые картографические
    данные в **общественном достоянии (public domain)**. Файл
    `ne_10m_rivers_lake_centerlines` содержит линии русел крупнейших рек мира.

    **Справочник рек (точки расчёта):**
    Координаты ключевых точек на 20 крупнейших реках России — компиляция
    из открытых источников (OpenStreetMap, Wikipedia).

    **Важно:**
    Все данные о стоке являются **модельными** — то есть рассчитанными
    гидрологической моделью, а не измеренными реальными приборами.
    Для официальной оценки паводковой ситуации используйте данные
    **Росгидромета** и **АИС ГМВО**.
    """)

st.markdown("---")
st.caption(
    "Проект: интерактивный анализ речного стока · "
    "Источник данных: [Open-Meteo Flood API](https://open-meteo.com/en/docs/flood-api)"
)
