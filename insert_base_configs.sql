-- 1) Сырые данные vacancy (таблица)
INSERT INTO report_configs
(name, description, chart_type, base_table, x_field, y_agg_func, y_field, filters_json, group_by_period, is_active)
VALUES
(
  'Сырые данные: vacancy',
  'Показ строк из vacancy с базовыми справочниками (профессия/опыт), без агрегации.',
  'table',
  'vacancy',
  'vacancy_id, profession, salary_avg, experience, created_at',
  'count',          -- обязательное поле, в table-режиме не используется
  NULL,
  NULL,
  NULL,
  TRUE
);

-- 2) Количество вакансий в день (line)
INSERT INTO report_configs
(name, description, chart_type, base_table, x_field, y_agg_func, y_field, filters_json, group_by_period, is_active)
VALUES
(
  'Вакансии по дням',
  'Количество вакансий, сгруппированное по дням публикации.',
  'line',
  'vacancy',
  'created_at',
  'count',
  NULL,
  NULL,
  'day',
  TRUE
);

-- 3) ТОП навыков (pie) — подсчёт уникальных вакансий по навыку
INSERT INTO report_configs
(name, description, chart_type, base_table, x_field, y_agg_func, y_field, filters_json, group_by_period, is_active)
VALUES
(
  'ТОП навыков',
  'Распределение вакансий по навыкам (COUNT DISTINCT vacancy_id). TOP-10 лучше ограничить в UI.',
  'pie',
  'vacancy',
  'skill',
  'count_distinct',
  NULL,
  NULL,
  NULL,
  TRUE
);

-- 4) Средняя зарплата по профессии (bar)
INSERT INTO report_configs
(name, description, chart_type, base_table, x_field, y_agg_func, y_field, filters_json, group_by_period, is_active)
VALUES
(
  'Средняя зарплата по профессии',
  'AVG(salary_avg) по каждой профессии.',
  'bar',
  'vacancy',
  'profession',
  'avg',
  'salary_avg',
  NULL,
  NULL,
  TRUE
);
