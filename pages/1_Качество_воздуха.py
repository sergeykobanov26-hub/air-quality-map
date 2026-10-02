"""Streamlit-приложение: качество воздуха в городах России."""

import streamlit as st

from src.cities import load_cities, get_cities_by_district, get_districts, get_default_cities
from src.data_air import fetch_cities
from src.filters import (
    filter_by_pollutant,
    get_city_current,
    get_city_stats,
    analyze_data,
)
from src.labels import (
    POLLUTANT_LABELS,
    get_pollutant_description,
    get_pollutant_unit,
)
from src.plots import create_map, plot_timeseries, plot_bar_avg, plot_distribution
from streamlit_folium import st_folium



# ---------- Заголовок ----------
st.title("Качество воздуха в городах России")
st.caption("Интерактивный анализ данных Open-Meteo Air Quality API")



# ---------- Загрузка справочника городов ----------
@st.cache_data
def get_cities_df():
    return load_cities()


cities_df = get_cities_df()


# ---------- Загрузка данных о воздухе ----------
@st.cache_data(ttl=3600)
def load_air_data(city_names_tuple, past_days):
    cities_to_fetch = cities_df[cities_df["city"].isin(city_names_tuple)]
    return fetch_cities(cities_to_fetch, past_days=past_days, forecast_days=0)


# ---------- Боковая панель ----------
st.sidebar.header("Фильтры")

past_days = st.sidebar.slider("Период (дней назад)", 1, 30, 7)

districts = ["Все"] + get_districts(cities_df)
selected_district = st.sidebar.selectbox("Федеральный округ", districts)

if selected_district == "Все":
    available_cities = cities_df["city"].tolist()
else:
    available_cities = get_cities_by_district(cities_df, selected_district)

default_cities = get_default_cities(cities_df, count=10)
default_cities = [c for c in default_cities if c in available_cities]

selected_cities = st.sidebar.multiselect(
    "Города",
    options=available_cities,
    default=default_cities,
)

selected_pollutant = st.sidebar.selectbox(
    "Загрязнитель",
    options=list(POLLUTANT_LABELS.keys()),
    format_func=lambda x: POLLUTANT_LABELS[x],
)


with st.sidebar.expander("О проекте и данных"):
    st.markdown("""
    **Источники данных:**
    - Качество воздуха: [Open-Meteo API](https://open-meteo.com/en/docs/air-quality-api)
    - Список городов: компиляция открытых данных (Росстат + OpenStreetMap)

    **Ограничения:**
    В проект включены города России с населением более 50 000 человек.
    Малые населённые пункты, как правило, имеют меньше промышленных
    источников загрязнения.
    """)


# ---------- Проверка выбора ----------
if not selected_cities:
    st.warning("Выберите хотя бы один город в боковой панели.")
    st.stop()


# ---------- Загрузка данных ----------
with st.spinner(f"Загрузка данных для {len(selected_cities)} городов..."):
    df = load_air_data(tuple(selected_cities), past_days)


df_filtered = filter_by_pollutant(df, selected_pollutant)


# ---------- Ключевые показатели ----------
st.header("Ключевые показатели")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Городов", len(df_filtered["city"].unique()))
with col2:
    st.metric("Записей", f"{len(df_filtered):,}".replace(",", " "))
with col3:
    st.metric("Среднее", f"{df_filtered[selected_pollutant].mean():.1f}")
with col4:
    max_row = df_filtered.loc[df_filtered[selected_pollutant].idxmax()]
    st.metric(
        "Максимум",
        f"{max_row[selected_pollutant]:.1f}",
        help=f"Город: {max_row['city']}",
    )


# ---------- Карта ----------
st.header("Карта загрязнения")

current = get_city_current(df_filtered)
m = create_map(current, pollutant=selected_pollutant)

map_key = f"map_{selected_pollutant}_{len(selected_cities)}_{past_days}"
st_folium(m, height=500, use_container_width=True,
          returned_objects=[], key=map_key)

# Пояснение загрязнителя
description = get_pollutant_description(selected_pollutant)
if description:
    st.info(description)

# Легенда AQI
st.markdown("**Уровень загрязнения (PM2.5, мкг/м³):**")
legend_cols = st.columns(6)
legend_items = [
    ("🟢", "0–12", "Хорошо"),
    ("🟡", "12–35", "Умеренно"),
    ("🟠", "35–55", "Вредно для чувствительных"),
    ("🔴", "55–150", "Вредно"),
    ("🟣", "150–250", "Очень вредно"),
    ("⚫", "> 250", "Опасно"),
]
for col, (emoji, value, label) in zip(legend_cols, legend_items):
    with col:
        st.markdown(f"{emoji} **{value}**  \n{label}")


# ---------- Графики ----------
st.header("Динамика во времени")

fig_ts = plot_timeseries(df_filtered, pollutant=selected_pollutant)
st.plotly_chart(fig_ts, use_container_width=True)

if selected_pollutant in ("pm2_5", "pm10"):
    st.caption(
        "Оранжевая линия — рекомендации ВОЗ (2021) для среднесуточной концентрации. "
        "Красная линия — ПДК России (СанПиН 1.2.3685-21). "
        "Значения выше красной линии означают превышение российских нормативов."
    )

st.subheader("Сравнение по городам")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("**Средние значения**")
    fig_bar = plot_bar_avg(df_filtered, pollutant=selected_pollutant)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.markdown("**Распределение**")
    fig_hist = plot_distribution(df_filtered, pollutant=selected_pollutant)
    st.plotly_chart(fig_hist, use_container_width=True)


# ---------- Таблица ----------
st.header("Статистика по городам")
st.dataframe(get_city_stats(df_filtered), use_container_width=True)


# ---------- Выводы ----------
st.header("Выводы")

stats = analyze_data(df_filtered, selected_pollutant, past_days)
label = POLLUTANT_LABELS[selected_pollutant]
unit = get_pollutant_unit(selected_pollutant)

st.markdown(f"Анализ за последние **{past_days}** дней по **{stats['total_cities']}** городам.")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Общая картина**")
    st.markdown(f"""
- Средний уровень **{label}** — **{stats['mean_value']:.1f} {unit}**
- Самый чистый воздух — **{stats['min_city']}** ({stats['min_value']:.1f} {unit})
- Самый загрязнённый — **{stats['max_city']}** ({stats['max_value']:.1f} {unit})
- Разница между городами — **{stats['max_value'] / max(stats['min_value'], 0.1):.1f}×**
""")

with col2:
    st.markdown("**Превышения нормативов**")

    if stats["who_norm"]:
        if stats["who_exceed_count"] > 0:
            cities_list = ", ".join(stats["who_exceed_cities"][:5])
            if len(stats["who_exceed_cities"]) > 5:
                cities_list += f" и ещё {len(stats['who_exceed_cities']) - 5}"
            st.markdown(
                f"- **ВОЗ ({stats['who_norm']} {unit}):** "
                f"превышено в **{stats['who_exceed_count']} из {stats['total_cities']}** городах  \n"
                f"  _{cities_list}_"
            )
        else:
            st.markdown(f"- **ВОЗ ({stats['who_norm']} {unit}):** превышений нет")

    if stats["ru_norm"]:
        if stats["ru_exceed_count"] > 0:
            cities_list = ", ".join(stats["ru_exceed_cities"][:5])
            if len(stats["ru_exceed_cities"]) > 5:
                cities_list += f" и ещё {len(stats['ru_exceed_cities']) - 5}"
            st.markdown(
                f"- **Россия ({stats['ru_norm']} {unit}):** "
                f"превышено в **{stats['ru_exceed_count']} из {stats['total_cities']}** городах  \n"
                f"  _{cities_list}_"
            )
        else:
            st.markdown(f"- **Россия ({stats['ru_norm']} {unit}):** превышений нет")

# Итог
st.markdown("**Итог**")

if stats["ru_norm"] and stats["ru_exceed_count"] and stats["ru_exceed_count"] > 0:
    st.warning(
        f"За последние {past_days} дней в **{stats['ru_exceed_count']}** "
        f"из **{stats['total_cities']}** городов средний уровень **{label}** "
        f"превышает ПДК России. Наибольшее превышение — в "
        f"**{stats['ru_exceed_cities'][0]}**."
    )
elif stats["who_norm"] and stats["who_exceed_count"] and stats["who_exceed_count"] > 0:
    st.warning(
        f"Российские ПДК соблюдены, но рекомендации ВОЗ превышены в "
        f"**{stats['who_exceed_count']}** городах. Самый проблемный — "
        f"**{stats['who_exceed_cities'][0]}**."
    )
else:
    st.success(
        f"За последние {past_days} дней во всех выбранных городах уровень "
        f"**{label}** соответствует нормативам. Воздух чистый."
    )

with st.expander("Откуда взяты нормативы"):
    st.markdown("""
    **Рекомендации ВОЗ (2021):**
    Всемирная организация здравоохранения публикует рекомендуемые
    предельные значения загрязнителей воздуха. Для PM2.5 среднесуточная
    норма — 15 мкг/м³, для PM10 — 45 мкг/м³.
    [Официальный документ](https://www.who.int/publications/i/item/9789240034228)

    **ПДК России (СанПиН 1.2.3685-21):**
    Обязательные нормативы РФ. Для PM2.5 среднесуточная ПДК — 35 мкг/м³,
    для PM10 — 60 мкг/м³. Они менее строгие, чем рекомендации ВОЗ.
    [Текст СанПиН](https://docs.cntd.ru/document/573500115)
    """)


st.divider()
st.caption(
    "Проект: интерактивный анализ качества воздуха · "
    "Источник данных: [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api)"
)
