DROP TABLE IF EXISTS TargetType;

CREATE TABLE TargetType (
    Id INTEGER PRIMARY KEY autoincrement,
    Name string NOT NULL,
    Comment string
);

DROP TABLE IF EXISTS Target;

CREATE TABLE Target (
    Id INTEGER PRIMARY KEY autoincrement,
    Name string NOT NULL UNIQUE,
    Type INTEGER,
    Comment string
);

DROP TABLE IF EXISTS Temperature;

CREATE TABLE Temperature (
    Id INTEGER PRIMARY KEY autoincrement,
    Date DATE NOT NULL UNIQUE,
    Temperature FLOAT
);