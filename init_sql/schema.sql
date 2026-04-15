CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    conf_year INTEGER,
    origin TEXT,
    abstract_url TEXT,
    scraped_url TEXT,
    notes TEXT,
    http_status INTEGER,
    scraped_at TIMESTAMP DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (conf_year, origin, abstract_url, scraped_url)
);