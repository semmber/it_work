# app/web/app_streamlit.py
from __future__ import annotations

import json
from typing import Any
import ast

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from streamlit.runtime.state.query_params import process_query_params

from db import get_connection
from db.repositories import (
    fetch_report_configs,
    insert_report_config,
    deactivate_report_config,
    run_sql,
)
from services.reports import build_sql_from_config


# -----------------------------
# UI-константы (под твою схему)
# -----------------------------
CHART_TYPES = ["table", "line", "bar", "pie"]

BASE_TABLES = [
    "vacancy",
    "profession",
    "experience",
    "work_format",
    "skill",
    "vacancy_skill",
    "vacancy_work_format",
]

# Логические поля, которые поддерживает твой билдер для base_table='vacancy'
VACANCY_FIELDS = [
    "vacancy_id",
    "created_at",
    "salary_avg",
    "profession",
    "experience",
    "skill",
    "work_format",
    "profession_id",
    "experience_id",
]

AGG_FUNCS = ["count", "count_distinct", "avg", "sum", "min", "max"]

GROUP_PERIODS = ["", "day", "week", "month", "year"]

# Белый список “сырых” колонок для base_table != vacancy (для chart_type='table')
RAW_TABLE_COLUMNS = {
    "profession": ["profession_id", "name"],
    "experience": ["experience_id", "code", "name"],
    "work_format": ["work_format_id", "code", "name"],
    "skill": ["skill_id", "name"],
    "vacancy_skill": ["vacancy_id", "skill_id"],
    "vacancy_work_format": ["vacancy_id", "work_format_id"],
}


# -----------------------------
# Streamlit helpers
# -----------------------------
st.set_page_config(page_title="Reports", layout="wide")
st.title("Отчёты и просмотр данных (через report_configs)")

def _reload_configs_cache() -> None:
    st.cache_data.clear()

@st.cache_data(ttl=60)
def _cached_configs(only_active: bool = True) -> pd.DataFrame:
    with get_connection() as conn:
        return fetch_report_configs(conn, only_active=only_active)

def _coerce_filters_value(op: str, value_text: str) -> Any:
    """
    Преобразует value из текстового поля в нужный тип под op:
    - in: "a,b,c" -> ["a","b","c"]
    - between: "2025-01-01,2025-02-01" -> ["2025-01-01","2025-02-01"]
    Иначе оставляет строкой (Postgres сам приведёт где надо, если типы совместимы).
    """
    op = (op or "").lower().strip()
    v = (value_text or "").strip()

    if op == "in":
        return [x.strip() for x in v.split(",") if x.strip()]
    if op == "between":
        parts = [x.strip() for x in v.split(",") if x.strip()]
        if len(parts) != 2:
            # оставим как есть — билдер потом ругнётся, и это нормально
            return parts
        return parts
    return v

def _unwrap_one(x: Any) -> Any:
    # список с одним элементом -> элемент
    if isinstance(x, list) and len(x) == 1:
        return x[0]

    # строка вида "['=']" -> "="
    if isinstance(x, str):
        s = x.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = ast.literal_eval(s)
                if isinstance(parsed, list) and len(parsed) == 1:
                    return parsed[0]
            except Exception:
                pass
        return s

    return x

def _filters_editor(initial: list[dict], allowed_fields: list[str]) -> list[dict]:
    """
    Удобный редактор фильтров.
    Возвращает список dict: [{"field":..., "op":..., "value":...}, ...]
    """
    if initial is None:
        initial = []

    df = pd.DataFrame(initial)
    if df.empty:
        df = pd.DataFrame(columns=["field", "op", "value"])

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "field": st.column_config.SelectboxColumn("field", options=allowed_fields, required=True),
            "op": st.column_config.SelectboxColumn("op", options=["=", "!=", ">", ">=", "<", "<=", "in", "between", "like"], required=True),
            "value": st.column_config.TextColumn("value (для in/between через запятую)", required=True),
        },
        hide_index=True,
        key="filters_editor",
    )

    out: list[dict] = []
    for _, row in edited.iterrows():
        field = _unwrap_one(row.get("field"))
        op = _unwrap_one(row.get("op"))
        value_raw = _unwrap_one(row.get("value"))
        field = str(field or "").strip()
        op = str(op or "").strip()
        value_raw = str(value_raw or "").strip()
        print(value_raw)
        if not field or not op or not value_raw:
            continue
        out.append({"field": field, "op": op, "value": _coerce_filters_value(op, value_raw)})
    return out

def _render_chart(chart_type: str, df: pd.DataFrame) -> None:
    """
    Ожидаем для графиков df с колонками x, y (как делает билдер).
    Для table — просто dataframe.
    """
    chart_type = (chart_type or "").lower().strip()

    if chart_type == "table":
        st.dataframe(df, use_container_width=True)
        return

    if df.empty:
        st.info("Нет данных для отображения.")
        return

    if "x" not in df.columns or "y" not in df.columns:
        st.warning("Для графика ожидаются колонки 'x' и 'y'. Показываю таблицей.")
        st.dataframe(df, use_container_width=True)
        return

    # Приведём x к строке для устойчивого отображения (особенно date_trunc)
    x = df["x"].astype(str)
    y = df["y"]

    if chart_type == "line":
        chart_df = pd.DataFrame({"x": x, "y": y})
        chart_df = chart_df.set_index("x")
        st.line_chart(chart_df)

    elif chart_type == "bar":
        chart_df = pd.DataFrame({"x": x, "y": y})
        chart_df = chart_df.set_index("x")
        st.bar_chart(chart_df)

    elif chart_type == "pie":
        scale_pct = 90
        scale = scale_pct / 100.0

        # Базовый размер фигуры (в дюймах), масштабируем
        base_w, base_h = 7.0, 5.0
        fig, ax = plt.subplots(figsize=(base_w * scale, base_h * scale), dpi=120)

        df2 = df[df["x"].notna()].copy()
        labels = df2["x"].astype(str)
        sizes = df2["y"]

        ax.pie(sizes, labels=labels, autopct="%1.1f%%", textprops={"fontsize": 10})
        ax.axis("equal")

        # ВАЖНО: не растягиваем на всю ширину контейнера
        st.pyplot(fig, use_container_width=False)

    else:
        st.warning(f"Неизвестный chart_type='{chart_type}'. Показываю таблицей.")
        st.dataframe(df, use_container_width=True)


# -----------------------------
# Загрузка конфигов и выбор
# -----------------------------
configs = _cached_configs(only_active=True)

if configs.empty:
    st.warning("В report_configs нет активных конфигураций (is_active=true). Добавь хотя бы одну.")
    st.stop()

records = configs.to_dict(orient="records")
names = [r["name"] for r in records]

left, right = st.columns([3, 1])
with left:
    idx = st.selectbox(
        "Выберите конфигурацию (report_configs)",
        range(len(names)),
        format_func=lambda i: names[i],
    )
with right:
    st.write("")
    st.write("")
    new_btn = st.button("➕ Новая конфигурация", use_container_width=True)

selected = records[idx]

btn_row = st.columns([1, 1, 2])
with btn_row[0]:
    show_btn = st.button("Показать", type="primary", use_container_width=True)
with btn_row[1]:
    preview_sql_btn = st.button("Показать SQL", use_container_width=True)
with btn_row[2]:
    st.caption("Удаление делаем мягко: is_active=false")

# -----------------------------
# Показ выбранного отчёта
# -----------------------------
if preview_sql_btn:
    try:
        sql, params = build_sql_from_config(selected)
        st.code(sql, language="sql")
        st.write("params:", params)
    except Exception as e:
        st.error(f"Ошибка построения SQL: {e}")

if show_btn:
    try:
        sql, params = build_sql_from_config(selected)
        with get_connection() as conn:
            df = run_sql(conn, sql, params=params)

        st.subheader(selected["name"])
        if selected.get("description"):
            st.write(selected["description"])

        _render_chart(selected["chart_type"], df)

    except Exception as e:
        st.error(f"Ошибка построения/выполнения отчёта: {e}")


# -----------------------------
# Создание новой конфигурации
# -----------------------------
if new_btn:

    @st.dialog("Создать новую конфигурацию")
    def create_config_dialog():
        st.write("Все параметры — выпадающие списки/мультиселекты (кроме имени и описания).")

        name = st.text_input("Имя (name)")
        description = st.text_area("Описание (description)")

        chart_type = st.selectbox("Тип (chart_type)", CHART_TYPES, index=0)
        base_table = st.selectbox("Базовая таблица (base_table)", BASE_TABLES, index=0)

        # Для base_table != vacancy разрешаем только table (как в билдере)
        if base_table != "vacancy" and chart_type != "table":
            st.warning("Для base_table != 'vacancy' поддерживается только chart_type='table'. Переключаю на table.")
            chart_type = "table"

        # Выбор полей под table / graph
        x_field = ""
        y_agg_func = "count"
        y_field = None
        group_by_period = None

        st.divider()

        if base_table == "vacancy":
            allowed_fields = VACANCY_FIELDS

            if chart_type == "table":
                picked = st.multiselect(
                    "Поля таблицы (x_field как список через запятую)",
                    options=allowed_fields,
                    default=["vacancy_id", "profession", "salary_avg", "experience", "created_at"],
                )
                x_field = ", ".join(picked)
                y_agg_func = st.selectbox("y_agg_func (в table не используется, но обязателен)", ["count", "count_distinct"], index=0)
                y_field = None
                group_by_period = None

            else:
                x_field = st.selectbox("x_field", options=allowed_fields, index=allowed_fields.index("created_at") if "created_at" in allowed_fields else 0)
                y_agg_func = st.selectbox("y_agg_func", options=AGG_FUNCS, index=AGG_FUNCS.index("count"))
                if y_agg_func in ("avg", "sum", "min", "max"):
                    # разумные y_field для этих агрегатов
                    y_field = st.selectbox("y_field", options=["salary_avg"], index=0)
                else:
                    y_field = None

                # group_by_period — только если x_field это дата/время (created_at)
                if x_field == "created_at":
                    group_by_period = st.selectbox("group_by_period", options=GROUP_PERIODS, index=GROUP_PERIODS.index("day"))
                    if group_by_period == "":
                        group_by_period = None
                else:
                    group_by_period = None

            st.divider()
            st.write("Фильтры (filters_json)")
            st.caption("Для in/between value вводи через запятую. Пример: in → Python,SQL ; between → 2025-01-01,2025-02-01")
            filters_list = _filters_editor(initial=[], allowed_fields=allowed_fields)
            filters_json = filters_list if filters_list else None

        else:
            # base_table != vacancy: только table, x_field = список колонок реальной таблицы
            cols = RAW_TABLE_COLUMNS.get(base_table, [])
            picked_cols = st.multiselect(
                f"Колонки таблицы {base_table} (x_field как список через запятую)",
                options=cols,
                default=cols,
            )
            x_field = ", ".join(picked_cols)
            y_agg_func = st.selectbox("y_agg_func (в table не используется, но обязателен)", ["count"], index=0)
            y_field = None
            group_by_period = None
            filters_json = None

        st.divider()

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            preview_btn = st.button("Предпросмотр", use_container_width=True)
        with c2:
            save_btn = st.button("Сохранить", type="primary", use_container_width=True)
        with c3:
            st.caption("Предпросмотр строит SQL и выполняет его без сохранения.")

        # Сборка cfg dict для предпросмотра/проверки билдером
        draft_cfg = {
            "name": name.strip(),
            "description": description.strip(),
            "chart_type": chart_type,
            "base_table": base_table,
            "x_field": x_field,
            "y_agg_func": y_agg_func,
            "y_field": y_field,
            "filters_json": filters_json,
            "group_by_period": group_by_period,
            "is_active": True,
        }

        if preview_btn:
            try:
                sql, params = build_sql_from_config(draft_cfg)
                st.code(sql, language="sql")
                st.write("params:", params)

                with get_connection() as conn:
                    df = run_sql(conn, sql, params=params)

                st.subheader("Результат предпросмотра")
                _render_chart(chart_type, df)

            except Exception as e:
                st.error(f"Ошибка предпросмотра: {e}")

        if save_btn:
            if not name.strip():
                st.warning("Имя (name) обязательно.")
                return
            if not x_field.strip():
                st.warning("Нужно выбрать поля (x_field не должен быть пустым).")
                return

            try:
                with get_connection() as conn:
                    new_id = insert_report_config(
                        conn=conn,
                        name=name.strip(),
                        description=description.strip() or None,
                        chart_type=chart_type,
                        base_table=base_table,
                        x_field=x_field,
                        y_agg_func=y_agg_func,
                        y_field=y_field,
                        filters_json=filters_json,
                        group_by_period=group_by_period,
                    )

                st.success(f"Сохранено (id={new_id}).")
                _reload_configs_cache()
                st.rerun()

            except Exception as e:
                st.error(f"Ошибка сохранения: {e}")

    create_config_dialog()


# -----------------------------
# Деактивация (мягкое удаление)
# -----------------------------
with st.expander("Управление конфигурациями"):
    all_cfg = _cached_configs(only_active=False)
    if all_cfg.empty:
        st.info("Конфигураций нет.")
    else:
        active_mask = all_cfg["is_active"] == True
        st.write(f"Активных: {int(active_mask.sum())} / Всего: {len(all_cfg)}")

        # Список только активных для деактивации
        active_df = all_cfg[active_mask].copy()
        if active_df.empty:
            st.info("Нет активных конфигураций для деактивации.")
        else:
            id_map = {
                f'{row["name"]} (id={int(row["id"])})': int(row["id"])
                for _, row in active_df.iterrows()
            }
            pick = st.selectbox("Выберите конфиг для деактивации", list(id_map.keys()))
            if st.button("Сделать is_active=false"):
                with get_connection() as conn:
                    deactivate_report_config(conn, id_map[pick])
                st.success("Деактивировано.")
                _reload_configs_cache()
                st.rerun()
