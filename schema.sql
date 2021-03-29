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
    -- Base FLOAT,
    -- Accumulation FLOAT,
    Comment string
);

DROP TABLE IF EXISTS TargetData;

CREATE TABLE TargetData (
    Id INTEGER PRIMARY KEY autoincrement,
    Target INTEGER,
    State string,
    Reference INTEGER NULL,
    Base FLOAT,
    Accumulation FLOAT,
    Comment string
);

DROP TABLE IF EXISTS Temperature;

CREATE TABLE Temperature (
    Id INTEGER PRIMARY KEY autoincrement,
    Date DATE NOT NULL UNIQUE,
    Temperature FLOAT
);