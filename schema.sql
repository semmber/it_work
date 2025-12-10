
CREATE TABLE profession (
	profession_id SERIAL PRIMARY KEY,
	name TEXT UNIQUE NOT NULL
);
CREATE TABLE experience (
	experience_id SERIAL PRIMARY KEY,
	code TEXT UNIQUE,
	name TEXT
);
CREATE TABLE work_format (
	work_format_id SERIAL PRIMARY KEY,
	code TEXT UNIQUE,
	name TEXT
);
CREATE TABLE skill (
	skill_id SERIAL PRIMARY KEY,
	name TEXT UNIQUE
);
CREATE TABLE vacancy (
	vacancy_id BIGINT PRIMARY KEY, -- id из HH
	profession_id INT REFERENCES profession(profession_id),
	experience_id INT REFERENCES experience(experience_id),
	salary_avg NUMERIC, -- только средняя зарплата в рублях
	created_at TIMESTAMPTZ DEFAULT now() -- или когда была опубликована вакансия
);
CREATE TABLE vacancy_work_format (
	vacancy_id BIGINT REFERENCES vacancy(vacancy_id) ON DELETE CASCADE,
	work_format_id INT REFERENCES work_format(work_format_id) ON DELETE CASCADE,
	PRIMARY KEY (vacancy_id, work_format_id)
);
CREATE TABLE vacancy_skill (
	vacancy_id BIGINT REFERENCES vacancy(vacancy_id) ON DELETE CASCADE,
	skill_id INT REFERENCES skill(skill_id) ON DELETE CASCADE,
	PRIMARY KEY (vacancy_id, skill_id)
);
CREATE TABLE report_configs (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,          -- название отчёта
    description     TEXT,
    chart_type      TEXT NOT NULL,          -- 'bar', 'line', 'pie'…
    base_table      TEXT NOT NULL,          -- 'vacancies', 'skills', 'vacancy_skill' и т.п.
    x_field         TEXT NOT NULL,          -- поле по оси X (город, язык, дата)
    y_agg_func      TEXT NOT NULL,          -- 'count', 'avg', 'sum'
    y_field         TEXT,                   -- поле для агрегации (salary_from, salary_to)
    filters_json    JSONB,                  -- условия (город='Москва', только активные и т.п.)
    group_by_period TEXT,                   -- 'day', 'month', 'year' (если нужно)
    is_active       BOOLEAN DEFAULT TRUE
);
