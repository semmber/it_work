from psycopg2.extras import RealDictCursor
from . import get_connection

# Получение чистых данных их БД

def get_all_vacancies(limit=1000):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM vacancy LIMIT %s", (limit,))
        return cur.fetchall()

def get_all_experience(limit=1000):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM experience LIMIT %s", (limit,))
        return cur.fetchall()

def get_all_profession(limit=1000):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM profession LIMIT %s", (limit,))
        return cur.fetchall()

def get_all_skill(limit=5000):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM skill LIMIT %s", (limit,))
        return cur.fetchall()

def get_all_vacancy_skill(limit=5000):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM vacancy_skill LIMIT %s", (limit,))
        return cur.fetchall()

def get_all_vacancy_work_format(limit=5000):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM vacancy_work_format LIMIT %s", (limit,))
        return cur.fetchall()

def get_all_work_format(limit=1000):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM work_format LIMIT %s", (limit,))
        return cur.fetchall()

def get_report_configs():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM report_configs WHERE is_active = TRUE ORDER BY id")
        return cur.fetchall()

# Получение конкретного значения для создания графика

def get_report_config(report_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM report_configs WHERE id = %s", (report_id,))
        return cur.fetchone()

# Добавление данных в БД

def create_report_config(data: dict):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO report_configs
                (name, description, chart_type, base_table,
                 x_field, y_agg_func, y_field, filters_json, group_by_period)
            VALUES (%(name)s, %(description)s, %(chart_type)s, %(base_table)s,
                    %(x_field)s, %(y_agg_func)s, %(y_field)s,
                    %(filters_json)s, %(group_by_period)s)
            RETURNING id
            """,
            data,
        )
        return cur.fetchone()["id"]