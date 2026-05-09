import sqlite3
from sqlite3 import Error
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
from my_modules.weather_api import Location


def create_connection(db_file):

    connection = None
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as error:
        print(error)

    return connection


class DataBase:

    def __init__(self, db_file: str) -> None:

        if not isinstance(db_file, str):
            raise TypeError

        connection = create_connection(db_file)
        if connection is None:
            return

        self.connection: sqlite3.Connection = connection
        self.cursor: sqlite3.Cursor = connection.cursor()

    def add_data(self, data):

        self._data = data

    def update_data_base(self):

        self._add_weather_data()

        city = self._get_city()
        self._add_location_data(city)

        self._add_information_data()

        self.connection.commit()

    def _add_location_data(self, city: str):

        to_db = [
            (
                city,
                self._data["lat"],
                self._data["lon"],
                self._data["timezone"],
                self._data["timezone_offset"],
            )
        ]

        self.cursor.executemany(
            "REPLACE INTO location (city, latitude, longitude, timezone, timezone_offset) VALUES (?, ?, ?, ?, ?);",
            to_db,
        )

    def _add_weather_data(self):

        to_db = [
            (
                weather_item.get("id", None),
                weather_item.get("main", None),
                weather_item.get("description", None),
                weather_item.get("icon", None),
            )
            for hourly_item in self._data["hourly"]
            for weather_item in hourly_item["weather"]
        ]

        self.cursor.executemany(
            "REPLACE INTO weather (weather_ID, main, description, icon) VALUES (?, ?, ?, ?);",
            to_db,
        )

    def _add_information_data(self):

        latitude = self._data["lat"]
        longitude = self._data["lon"]

        to_db = [
            (
                latitude,
                longitude,
                i.get("dt", None),
                i.get("temp", None),
                i.get("feels_like", None),
                i.get("pressure", None),
                i.get("humidity", None),
                i.get("dew_point", None),
                i.get("uvi", None),
                i.get("clouds", None),
                i.get("visibility", None),
                i.get("wind_speed", None),
                i.get("wind_deg", None),
                i.get("wind_gust", None),
                i["weather"][0]["id"],
                i.get("pop", None),
            )
            for i in self._data["hourly"]
        ]

        self.cursor.executemany(
            "REPLACE INTO data (latitude, longitude, dt, temp, feels_like, pressure, humidity, dew_point, uvi, clouds, visibility, wind_speed, wind_deg, wind_gust, weather_ID, pop) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            to_db,
        )

    def _get_location_ID(self) -> int:

        latitude = self._data["lat"]
        longitude = self._data["lon"]

        return self.cursor.execute(
            f"SELECT location_ID FROM location WHERE latitude = {latitude} and longitude = {longitude}"
        ).fetchone()[0]

    def _get_city(self) -> str:
        geolocator = Nominatim(user_agent="my_weather_app")

        latitude = self._data["lat"]
        longitude = self._data["lon"]

        location = geolocator.reverse(f"{latitude}, {longitude}")

        raw_data = getattr(location, "raw", {})
        address = raw_data.get("address", {})

        city: str = address.get("city", address.get("town", address.get("village", "")))

        return city.lower()

    def clear_data_table(self):

        self.cursor.execute("DELETE FROM data;")
        self.connection.commit()

    def clear_location_table(self):

        self.cursor.execute("DELETE FROM location;")
        self.connection.commit()

    def clear_weather_table(self):

        self.cursor.execute("DELETE FROM weather;")
        self.connection.commit()

    def is_whole_date_stored(self, city: str, day_offset):

        current_date_time = datetime.now()
        date = current_date_time + timedelta(day_offset)

        year = date.year

        if len(str(date.month)) == 1:
            month = "0" + str(date.month)
        else:
            month = str(date.month)

        if len(str(date.day)) == 1:
            day = "0" + str(date.day)
        else:
            day = str(date.day)

        hours = self.cursor.execute(f"""
            SELECT date_time FROM information
                WHERE city = '{city}'
                AND strftime('%Y', date_time) = '{year}'
                AND strftime('%m', date_time) = '{month}'
                AND strftime('%d', date_time) = '{day}';
                """).fetchall()

        if len(hours) == 24:
            return True
        else:
            return False

    def is_next_48_hours_stored(self, location: Location):

        current_date_time = datetime.now()
        date = str(current_date_time)

        date_hour = date[:13] + ":00:00"

        hours = self.cursor.execute(f"""
            SELECT * from information
                WHERE latitude = '{location.latitude}'
                AND longitude = '{location.longitude}'
                AND date_time >= '{date_hour}';
                """).fetchall()

        if len(hours) == 48:
            return True
        else:
            return False


def main():
    db = DataBase("WeatherData.db")


if __name__ == "__main__":
    main()
