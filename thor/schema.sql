DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS config;
DROP TABLE IF EXISTS nodes;
DROP TABLE IF EXISTS lightning_events;

CREATE TABLE alerts
(
	id           INTEGER PRIMARY KEY AUTOINCREMENT,
	publisher_id TEXT    NOT NULL UNIQUE, -- ID provided by the publisher of the alert if it comes from an online source, to avoid duplication.
	timestamp    INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated      INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
	expiry       INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
	type         TEXT    NOT NULL DEFAULT "Unknown",
	data         TEXT    NOT NULL DEFAULT "{}"
);

CREATE TABLE nodes
(
	id                TEXT PRIMARY KEY,
	last_ip           TEXT NOT NULL,
	last_contact_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	type              TEXT
);

CREATE TABLE config
(
	id      TEXT PRIMARY KEY,
	value   TEXT NULL DEFAULT NULL,
	updated INTEGER DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lightning_events
(
	id        INTEGER PRIMARY KEY AUTOINCREMENT,
	distance  REAL,
	energy    REAL,
	timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
