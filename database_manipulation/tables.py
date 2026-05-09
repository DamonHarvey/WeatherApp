TABLE_location = """
CREATE TABLE IF NOT EXISTS location (
   latitude REAL NOT NULL,
   longitude REAL NOT NULL,
   city TEXT NOT NULL,
   timezone TEXT NOT NULL,
   timezone_offset INTEGER NOT NULL,
   PRIMARY KEY(latitude, longitude)
);
"""

TABLE_weather = """
CREATE TABLE IF NOT EXISTS weather (
   weather_ID INTEGER PRIMARY KEY,
   main TEXT NOT NULL,
   description TEXT NOT NULL,
   icon text NOT NULL
);
"""

TABLE_data = """
CREATE TABLE IF NOT EXISTS data (
   latitude REAL NOT NULL,
   longitude REAL NOT NULL,   
   dt INTEGER,
   
   temp REAL,
   feels_like REAL,
   pressure INTEGER,
   humidity INTEGER,
   dew_point REAL,
   uvi REAL,
   clouds INTEGER,
   visibility INTEGER,
   wind_speed REAL,
   wind_deg INTEGER,
   wind_gust REAL,
   weather_ID INTEGER NOT NULL,
   pop REAL,
   
   PRIMARY KEY(latitude, longitude, dt),
   FOREIGN KEY(latitude) REFERENCES location(latitude),
   FOREIGN KEY(longitude) REFERENCES location(longitude),
   FOREIGN KEY(weather_ID) REFERENCES weather(weather_ID)
   ON DELETE CASCADE
);
"""


VIEW_information = """
CREATE VIEW information AS
	SELECT l.city,
		   datetime(d.dt + l.timezone_offset, 'unixepoch') AS date_time,
		   d.temp,
		   d.feels_like,
		   d.uvi,
		   d.clouds,
		   d.humidity,
		   d.wind_speed,
		   d.wind_deg,
		   d.wind_gust,
         d.dew_point,
         d.pop
	FROM data d
	JOIN location l
		ON l.latitude = d.latitude
      AND l.longitude = d.longitude
"""
