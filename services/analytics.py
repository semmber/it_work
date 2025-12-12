import json
import pandas as pd
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from db import get_connection


ALLOWED_TABLES = {"vacancy", "employer", "area", "report_configs"}  # добавь свои
ALLOWED_AGG = {"count", "sum", "avg", "min", "max"}

# (опционально) список полей для каждой таблицы — самый безопасный вариант
ALLOWED_FIELDS = {
    "vacancy": {"created_at", "salary_from", "salary_to", "id", "employer_id", "area_id"},
    # ...
}

def build_df_from_config(cfg: dict) -> pd.DataFrame:
    base_table = cfg["base_table"]
    x_field = cfg["x_field"]
    y_field = cfg["y_field"]
    agg = (cfg["y_agg_func"] or "").lower()
    group_by_period = cfg.get("group_by_period")  # day/week/month
    filters = cfg.get("filters_json")  # может быть dict или str

    # --- валидация ---
    if base_table not in ALLOWED_TABLES:
        raise ValueError("base_table запрещён")

    if agg not in ALLOWED_AGG:
        raise ValueError("y_agg_func запрещён")

    if base_table in ALLOWED_FIELDS:
        if x_field not in ALLOWED_FIELDS[base_table]:
            raise ValueError("x_field запрещён")
        if y_field and y_field not in ALLOWED_FIELDS[base_table]:
            raise ValueError("y_field запрещён")

    # filters_json может храниться как JSON строка
    if isinstance(filters, str) and filters.strip():
        filters = json.loads(filters)
    if filters is None:
        filters = {}

    # --- X выражение с периодом ---
    x_ident = sql.Identifier(x_field)
    if group_by_period in ("day", "week", "month"):
        # date_trunc для timestamp
        x_expr = sql.SQL("date_trunc({}, {})").format(sql.Literal(group_by_period), x_ident)
    else:
        x_expr = x_ident

    # --- Y выражение ---
    if agg == "count":
        y_expr = sql.SQL("COUNT(*)")
    else:
        y_expr = sql.SQL("{}({})").format(sql.SQL(agg.upper()), sql.Identifier(y_field))

    where_parts = []
    params = []

    # Простой формат фильтров: {"area_id": 1, "employer_id": 10}
    for k, v in filters.items():
        # проверка полей фильтра
        if base_table in ALLOWED_FIELDS and k not in ALLOWED_FIELDS[base_table]:
            raise ValueError(f"filter field запрещён: {k}")
        where_parts.append(sql.SQL("{} = %s").format(sql.Identifier(k)))
        params.append(v)

    where_sql = sql.SQL("")
    if where_parts:
        where_sql = sql.SQL("WHERE ") + sql.SQL(" AND ").join(where_parts)

    query = sql.SQL("""
        SELECT
            {x_expr} AS x,
            {y_expr} AS y
        FROM {table}
        {where_sql}
        GROUP BY x
        ORDER BY x
    """).format(
        x_expr=x_expr,
        y_expr=y_expr,
        table=sql.Identifier(base_table),
        where_sql=where_sql,
    )

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    return df
