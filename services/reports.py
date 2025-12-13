from __future__ import annotations
import json
import pandas as pd

# Разрешённые значения
ALLOWED_BASE_TABLES = {
    "vacancy", "profession", "experience", "work_format", "skill",
    "vacancy_skill", "vacancy_work_format",
}
ALLOWED_AGG = {None, "", "count", "count_distinct", "sum", "avg", "min", "max"}
ALLOWED_OPS = {"=", "!=", ">", ">=", "<", "<=", "in", "between", "like"}
ALLOWED_GROUP_PERIOD = {None, "", "day", "week", "month", "year"}

# --- JOIN'ы от vacancy ---
JOINS = {
    "profession": """
        LEFT JOIN profession p ON p.profession_id = v.profession_id
    """,
    "experience": """
        LEFT JOIN experience e ON e.experience_id = v.experience_id
    """,
    "skill": """
        LEFT JOIN vacancy_skill vs ON vs.vacancy_id = v.vacancy_id
        LEFT JOIN skill s ON s.skill_id = vs.skill_id
    """,
    "work_format": """
        LEFT JOIN vacancy_work_format vwf ON vwf.vacancy_id = v.vacancy_id
        LEFT JOIN work_format wf ON wf.work_format_id = vwf.work_format_id
    """,
}

# --- Поля (логические имена) -> SQL выражение + требуемые JOIN keys ---
# Совет: в report_configs хранить именно эти ключи (profession, skill, work_format...)
FIELD_MAP = {
    # vacancy
    "vacancy_id":   {"expr": "v.vacancy_id", "joins": []},
    "created_at":   {"expr": "v.created_at", "joins": []},
    "salary_avg":   {"expr": "v.salary_avg", "joins": []},
    "profession_id":{"expr": "v.profession_id", "joins": []},
    "experience_id":{"expr": "v.experience_id", "joins": []},

    # joined lookup
    "profession":   {"expr": "p.name", "joins": ["profession"]},
    "experience":   {"expr": "e.name", "joins": ["experience"]},

    # m2m
    "skill":        {"expr": "s.name", "joins": ["skill"]},
    "work_format":  {"expr": "wf.name", "joins": ["work_format"]},
}

def _field_expr(field_key: str) -> tuple[str, set[str]]:
    if field_key not in FIELD_MAP:
        raise ValueError(f"Поле '{field_key}' не разрешено (нет в FIELD_MAP).")
    meta = FIELD_MAP[field_key]
    return meta["expr"], set(meta["joins"])

def _render_joins(required: set[str]) -> str:
    if not required:
        return ""
    parts = []
    for key in sorted(required):
        if key not in JOINS:
            raise ValueError(f"Неизвестный join key: {key}")
        parts.append(JOINS[key].strip())
    return "\n".join(parts)

def _apply_group_period(x_expr: str, period: str | None) -> str:
    if not period:
        return x_expr
    period = period.lower().strip()
    if period not in ALLOWED_GROUP_PERIOD:
        raise ValueError(f"group_by_period='{period}' запрещён.")
    return f"date_trunc('{period}', {x_expr})"

def _needs_distinct_vacancy(required_joins: set[str]) -> bool:
    # Если присоединили m2m таблицы, COUNT(*) будет завышать
    return bool(required_joins.intersection({"skill", "work_format"}))

def _agg_expr(agg: str | None, y_expr: str, required_joins: set[str]) -> str:
    agg = (agg or "").lower().strip()
    if agg not in ALLOWED_AGG:
        raise ValueError(f"y_agg_func='{agg}' запрещён.")

    if agg in ("", None):
        return y_expr

    if agg == "count":
        # чтобы не раздувало при join skills/work_format, по умолчанию считаем DISTINCT вакансии
        if _needs_distinct_vacancy(required_joins):
            return "COUNT(DISTINCT v.vacancy_id)"
        return "COUNT(*)"

    if agg == "count_distinct":
        return "COUNT(DISTINCT v.vacancy_id)"

    return f"{agg.upper()}({y_expr})"

def _build_where(filters) -> tuple[str, list, set[str]]:
    if not filters:
        return "", [], set()

    clauses = []
    params = []
    required_joins: set[str] = set()

    for f in filters:
        field = f.get("field")
        op = (f.get("op") or "").lower().strip()
        val = f.get("value")

        if op not in ALLOWED_OPS:
            raise ValueError(f"Оператор '{op}' запрещён.")

        expr, joins = _field_expr(field)
        required_joins |= joins

        if op == "in":
            if not isinstance(val, list) or not val:
                raise ValueError("Для op='in' value должен быть непустым списком.")
            placeholders = ", ".join(["%s"] * len(val))
            clauses.append(f"{expr} IN ({placeholders})")
            params.extend(val)

        elif op == "between":
            if not isinstance(val, list) or len(val) != 2:
                raise ValueError("Для op='between' value должен быть [from, to].")
            clauses.append(f"{expr} BETWEEN %s AND %s")
            params.extend(val)

        else:
            clauses.append(f"{expr} {op} %s")
            params.append(val)

    return "WHERE " + " AND ".join(clauses), params, required_joins

def build_sql_from_config(cfg: dict) -> tuple[str, list]:
    """
    cfg — строка из report_configs (dict):
    name, chart_type, base_table, x_field, y_agg_func, y_field, filters_json, group_by_period
    """
    chart_type = (cfg.get("chart_type") or "").lower().strip()
    base_table = (cfg.get("base_table") or "").lower().strip()
    x_field = (cfg.get("x_field") or "").strip()
    y_agg = (cfg.get("y_agg_func") or "").strip()
    y_field = (cfg.get("y_field") or "").strip() or None
    group_by_period = (cfg.get("group_by_period") or "").strip() or None

    if base_table not in ALLOWED_BASE_TABLES:
        raise ValueError(f"base_table='{base_table}' запрещён. Разрешено: {sorted(ALLOWED_BASE_TABLES)}")

    # filters_json может прийти как dict/list (psycopg2) или строка
    raw_filters = cfg.get("filters_json")
    filters = []
    if raw_filters:
        filters = json.loads(raw_filters) if isinstance(raw_filters, str) else raw_filters

    # ---- CASE 1: базовые таблицы без vacancy (простая таблица) ----
    # Для "сырых данных" из profession/skill/work_format/... просто показываем столбцы.
    if base_table != "vacancy":
        if chart_type != "table":
            raise ValueError("Для base_table != 'vacancy' поддерживаю только chart_type='table'.")
        # x_field как CSV-список столбцов таблицы
        cols = [c.strip() for c in x_field.split(",") if c.strip()]
        if not cols:
            raise ValueError("Для table нужно x_field='col1, col2, ...'")

        # Важно: тут нет FIELD_MAP, потому что это *не* vacancy-отчёт.
        # Делаем строгий whitelist столбцов по твоей схеме:
        WHITELIST = {
            "profession": {"profession_id", "name"},
            "experience": {"experience_id", "code", "name"},
            "work_format": {"work_format_id", "code", "name"},
            "skill": {"skill_id", "name"},
            "vacancy_skill": {"vacancy_id", "skill_id"},
            "vacancy_work_format": {"vacancy_id", "work_format_id"},
        }
        bad = [c for c in cols if c not in WHITELIST[base_table]]
        if bad:
            raise ValueError(f"Недопустимые столбцы для {base_table}: {bad}")

        sql = f"SELECT {', '.join(cols)} FROM {base_table} LIMIT 1000"
        return sql, []

    # ---- CASE 2: base_table = vacancy ----
    required_joins: set[str] = set()

    # WHERE (может потребовать join)
    where_sql, params, where_joins = _build_where(filters)
    required_joins |= where_joins

    # 2.1) TABLE режим: показать строки (в т.ч. “всё вместе” через join’ы)
    if chart_type == "table":
        # x_field — CSV логических полей из FIELD_MAP:
        # "vacancy_id, profession, salary_avg, experience, created_at, skill, work_format"
        keys = [k.strip() for k in x_field.split(",") if k.strip()]
        if not keys:
            raise ValueError("Для chart_type='table' нужно x_field со списком полей через запятую.")

        select_exprs = []
        for k in keys:
            expr, joins = _field_expr(k)
            required_joins |= joins
            select_exprs.append(f"{expr} AS {k}")

        join_sql = _render_joins(required_joins)

        # Если выбран skill/work_format, строки будут размножаться (по навыкам/форматам).
        # Это ОК для “полной информации”, но если не хочешь — можно потом сделать агрегирование array_agg.
        sql = f"""
            SELECT {", ".join(select_exprs)}
            FROM vacancy v
            {join_sql}
            {where_sql}
            ORDER BY v.created_at DESC
            LIMIT 1000
        """.strip()
        return sql, params

    # 2.2) GRAPH режим: x + агрегированный y
    if not x_field:
        raise ValueError("Для графика нужен x_field.")
    x_expr, x_joins = _field_expr(x_field)
    required_joins |= x_joins
    x_expr = _apply_group_period(x_expr, group_by_period)

    # y_field может быть пустым для count/count_distinct
    y_expr = "1"
    if y_field:
        y_expr, y_joins = _field_expr(y_field)
        required_joins |= y_joins

    y_select = _agg_expr(y_agg, y_expr, required_joins)

    join_sql = _render_joins(required_joins)

    # --- убираем NULL из pie (и вообще из любых pie) ---
    if chart_type == "pie":
        x_expr_raw, _ = _field_expr(x_field)  # без date_trunc
        if where_sql:
            where_sql += f" AND {x_expr_raw} IS NOT NULL"
        else:
            where_sql = f"WHERE {x_expr_raw} IS NOT NULL"

    # --- TOP-10 для навыков в pie (без "прочее") ---
    limit_sql = ""
    if chart_type == "pie" and x_field == "skill":
        limit_sql = "LIMIT 10"

    sql = f"""
        SELECT
            {x_expr} AS x,
            {y_select} AS y
        FROM vacancy v
        {join_sql}
        {where_sql}
        GROUP BY {x_expr}
        ORDER BY y DESC
        {limit_sql}
    """.strip()

    return sql, params

def fetch_report_df(conn, cfg_row: dict) -> pd.DataFrame:
    sql, params = build_sql_from_config(cfg_row)
    return pd.read_sql(sql, conn, params=params)

