import requests
from geopy.geocoders import Nominatim
from my_modules.API_KEY import API_KEY

import json


class Location:
    """Stores latitude and longitude"""

    def __init__(
        self, latitude: float | None = None, longitude: float | None = None
    ) -> None:

        self._geolocator = Nominatim(user_agent="my_weather_app")

        if latitude is None and longitude is None:

            self._set_current_coords()

        elif isinstance(latitude, (float)) and isinstance(longitude, (float)):

            self._latitude: float = round(latitude, 4)
            self._longitude: float = round(longitude, 4)

        else:

            raise TypeError

        self._get_current_city()

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    @property
    def city(self) -> str:
        return self._city

    @property
    def state(self) -> str:
        return self._state

    @property
    def country(self) -> str:
        return self._country

    def _set_current_coords(self):
        """Sets current latitude and longitude"""

        try:
            response = requests.get("https://ipinfo.io")
            data = response.json()

            location = data["loc"].split(",")

        except Exception as exception:

            print(f"Error: {exception}")

        else:
            self._latitude: float = round(float(location[0]), 4)
            self._longitude: float = round(float(location[1]), 4)

    def _get_current_city(self):

        location = self._geolocator.reverse(f"{self._latitude}, {self._longitude}")

        if location:
            address = location.raw.get("address", {})  # type: ignore
            city = address.get(
                "city", address.get("town", address.get("village", "N/A"))
            )
            state = address.get("state", "N/A")
            country = address.get("country", "N/A")

            self._city = city.lower()
            self._state = state.lower()
            self._country = country.lower()

        else:
            self._city = ""

    def set_location(self, city: str, state: str, country: str):

        address = f"{city}, {state}, {country}"

        location = self._geolocator.geocode(address)

        if location:

            self._latitude = round(location.latitude, 4)  # type: ignore
            self._longitude = round(location.longitude, 4)  # type: ignore

            self._city = city
            self._state = state
            self._country = country
        else:
            print("location not found")

    def __str__(self) -> str:
        return f"Latitude: {self._latitude} Longitude: {self._longitude}"


def get_location_data(loc: Location):
    """Gets location data"""

    latitude = loc.latitude
    longitude = loc.longitude

    exc = "current,minutely,daily,alerts"

    response = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&exclude={exc}&appid={API_KEY}"
    )

    return response.json()


def main():
    loc = Location()
    data = get_location_data(loc)
    with open("test.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    main()
