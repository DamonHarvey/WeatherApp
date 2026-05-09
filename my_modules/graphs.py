from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, PercentFormatter
import sqlite3
from datetime import datetime, timedelta
from typing import Literal, Any
from enum import Enum
from my_modules.weather_api import Location


def k_to_f(temp: float) -> float:
    return (temp - 273.15) * 9 / 5 + 32


def k_to_c(temp: float) -> float:
    return temp - 273.15


def k_to_r(temp: float) -> float:
    return temp * 1.8


def convert_temp(temp: float, temp_scale: str) -> float:
    if temp_scale == "fahrenheit":
        return k_to_f(temp)
    elif temp_scale == "celsius":
        return k_to_c(temp)
    elif temp_scale == "rankine":
        return k_to_r(temp)
    else:  # kelvin
        pass
    return temp


def timestamp_to_time(time):

    return datetime.fromisoformat(time)


def format_func(value, tick_number):
    return datetime.strptime(str(int(value)), "%H").strftime("%I %p")


def create_title(data, title: str, hour_offset):
    return (
        str(data[0][Index.CITY_INDEX.value]).capitalize()
        + f" {title} "
        + str(timestamp_to_time(data[hour_offset][Index.TIME_INDEX.value]))[:10]
    )


class Index(Enum):
    CITY_INDEX = 0
    TIME_INDEX = 1
    TEMP_INDEX = 2
    FEEL_INDEX = 3
    UVI_INDEX = 4
    CLOUD_INDEX = 5
    HUMIDITY_INDEX = 6
    WIND_SPEED_INDEX = 7
    WIND_GUST_INDEX = 8
    DEW_POINT_INDEX = 9
    PERCIP_INDEX = 10


TEMPERATURE_SCALE: dict[str, str] = {
    "celsius": "°C",
    "fahrenheit": "°F",
    "kelvin": "K",
    "rankine": "°R",
}


class MakePlot:
    """Builds matplotlib figures from weather data stored in SQLite.

    This helper class loads hourly weather observations from the connected
    SQLite cursor and generates reusable matplotlib Figure objects for
    temperature, sun data, wind speed, and arbitrary single-field plots.

    Attributes:
        _cursor: SQLite cursor used to query weather records from the
            loaded database.
        _figure: Matplotlib Figure object used for the current plot.
        _plot: Matplotlib Axes object used for drawing the current plot.
    """

    def __init__(
        self,
        cursor: sqlite3.Cursor,
        location: Location,
        temp_scale: Literal[
            "celsius", "fahrenheit", "kelvin", "rankine"
        ] = "fahrenheit",
    ) -> None:

        if not isinstance(cursor, sqlite3.Cursor):
            raise TypeError
        if not isinstance(location, Location):
            raise TypeError
        if not temp_scale in TEMPERATURE_SCALE:
            raise ValueError

        self.temp_scale = temp_scale

        self._cursor = cursor
        self._location = location

        self._get_data()
        self._prepare_data()

        self._initialize_figure()
        self._initialize_plot()

    def _get_data(self):

        current_date_time = datetime.now()
        two_days_from_now = current_date_time + timedelta(2)

        date = str(current_date_time)[:10]
        date_two = str(two_days_from_now)[:10]

        quere = f"""
                SELECT city,
                    date_time,
                    temp,
                    feels_like,
                    uvi,
                    clouds,
                    humidity,
                    wind_speed,
                    wind_gust,
                    dew_point,
                    pop
                FROM information
                WHERE strftime('%Y-%m-%d', date_time) >= '{date}'
                    AND strftime('%Y-%m-%d', date_time) < '{date_two}'
                    AND latitude = '{self._location.latitude}'
                    AND longitude = '{self._location.longitude}';
                """
        self._data = self._cursor.execute(quere).fetchall()

        # print("DEBUG:")
        # for item in self._data:
        #     print(item)
        # print(len(self._data))

    def _prepare_data(self):

        city: list[str] = []
        time: list[datetime] = []
        uvi: list[float] = []
        cloud: list[int] = []
        temp: list[float] = []
        feel: list[float] = []
        humidity: list[int] = []
        percip: list[float] = []
        dew_point: list[float] = []
        wind_gust: list[float] = []
        wind_speed: list[float] = []

        lowest_temp = float("inf")
        highest_temp = float("-inf")

        lowest_wind_speed = float("inf")
        highest_wind_speed = float("-inf")

        for item in self._data:

            city.append(item[Index.CITY_INDEX.value])
            time.append(timestamp_to_time(item[Index.TIME_INDEX.value]))
            uvi.append(item[Index.UVI_INDEX.value])
            cloud.append(item[Index.CLOUD_INDEX.value])

            converted_temp = convert_temp(item[Index.TEMP_INDEX.value], self.temp_scale)
            converted_feel = convert_temp(item[Index.FEEL_INDEX.value], self.temp_scale)
            convert_dew = convert_temp(
                item[Index.DEW_POINT_INDEX.value], self.temp_scale
            )
            temp.append(converted_temp)
            feel.append(converted_feel)
            lowest_temp = min(lowest_temp, converted_temp, converted_feel, convert_dew)
            highest_temp = max(
                highest_temp, converted_temp, converted_feel, convert_dew
            )

            humidity.append(item[Index.HUMIDITY_INDEX.value])
            percip.append(item[Index.PERCIP_INDEX.value])

            dew_point.append(convert_dew)

            wind_gust.append(item[Index.WIND_GUST_INDEX.value])
            wind_speed.append(item[Index.WIND_SPEED_INDEX.value])
            highest_wind_speed = max(
                highest_wind_speed,
                item[Index.WIND_SPEED_INDEX.value],
                item[Index.WIND_GUST_INDEX.value],
            )
            lowest_wind_speed = min(
                lowest_wind_speed,
                item[Index.WIND_SPEED_INDEX.value],
                item[Index.WIND_GUST_INDEX.value],
            )

        self._data_axes = {
            "city": city,
            "time": time,
            "uvi": uvi,
            "cloud": cloud,
            "temp": temp,
            "feel": feel,
            "humidity": humidity,
            "percip": percip,
            "dew_point": dew_point,
            "wind_gust": wind_gust,
            "wind_speed": wind_speed,
        }

        self._lowest_plot_temp: float = lowest_temp - 5
        self._highest_plot_temp: float = highest_temp + 5

        self._lowest_plot_wind_speed: float = lowest_wind_speed - 5
        self._highest_plot_wind_speed: float = highest_wind_speed + 5

    def update_data(self):
        self._data.clear()
        self._data_axes.clear()

        self._get_data()
        self._prepare_data()

    def _initialize_figure(self):
        figure = Figure(figsize=(8, 5), dpi=80)
        figure.subplots_adjust(left=0.10, right=0.97, top=0.93)

        self._figure = figure

    def _initialize_plot(self):
        figure: Figure = self._figure

        plot = figure.add_subplot()
        plot.grid(True)

        plot.xaxis.set_major_formatter(FuncFormatter(format_func))

        self._plot = plot

    def plot_humidity(self, day_offset: int = 0):
        """Creates a Figure based on humidity data in the database.

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with hourly humidity data.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_humidity()
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        self._initialize_figure()
        self._initialize_plot()

        hour_offset = day_offset * 24
        hour_range = slice(hour_offset, 24 + hour_offset)

        #### # Don't like
        first_date = datetime.fromisoformat(self._data[0][1])

        if day_offset == 0:
            hour_range = slice(0, 24 - first_date.hour)
        elif day_offset == 1:
            hour_range = slice(24 - first_date.hour, len(self._data))
        #### # Don't like

        data = {key: value[hour_range] for key, value in self._data_axes.items()}

        hours = [item.hour for item in data["time"]]

        figure = self._figure
        plot = self._plot

        plot_title = create_title(self._data, "Humidity", hour_offset)
        plot.set_title(plot_title)
        plot.set_ylabel("Relative humidity")
        plot.set_xlabel("Hour")
        plot.tick_params(axis="x", labelrotation=45)
        plot.set_xticks(hours)

        plot.yaxis.set_major_formatter(PercentFormatter(xmax=100))

        plot.plot(
            hours,
            data["humidity"],
            label="Humidity %",
            color="skyblue",
        )

        plot.fill_between(
            data["time"],
            data["humidity"],
            -5,
            color="skyblue",
            alpha=0.3,
        )

        plot.set_xlim(0, 23)
        plot.set_ylim(-5, 105)

        plot.legend()

        return figure

    def plot_dew_point(self, day_offset: int = 0):
        """Creates a Figure based on dew point data in the database.

        Args:
            temp_scale: The temperature scale to display. Options are:
                - "celsius" (°C)
                - "fahrenheit" (°F)
                - "kelvin" (K)
                - "rankine" (°R)

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with dew point data.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_dew_point("fahrenheit")
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        self._initialize_figure()
        self._initialize_plot()

        hour_offset = day_offset * 24
        hour_range = slice(hour_offset, 24 + hour_offset)

        #### # Don't like
        first_date = datetime.fromisoformat(self._data[0][1])

        if day_offset == 0:
            hour_range = slice(0, 24 - first_date.hour)
        elif day_offset == 1:
            hour_range = slice(24 - first_date.hour, len(self._data))
        #### # Don't like

        data = {key: value[hour_range] for key, value in self._data_axes.items()}

        hours = [item.hour for item in data["time"]]

        figure = self._figure
        plot = self._plot

        plot_title = create_title(self._data, "Dew point", hour_offset)
        plot.set_title(plot_title)
        plot.set_ylabel("Temp " + TEMPERATURE_SCALE[self.temp_scale])
        plot.set_xlabel("Hour")
        plot.tick_params(axis="x", labelrotation=45)
        plot.set_xticks(hours)

        plot.plot(
            hours,
            data["dew_point"],
            label="Temp " + TEMPERATURE_SCALE[self.temp_scale],
            color="skyblue",
        )

        plot.fill_between(
            hours,
            data["dew_point"],
            self._lowest_plot_temp,
            alpha=0.3,
            color="skyblue",
        )

        plot.set_ybound(self._lowest_plot_temp, self._highest_plot_temp)
        plot.set_xlim(0, 23)

        plot.legend()

        return figure

    def plot_uvi(self, day_offset: int = 0):
        """Creates a Figure based on uvi data in the database.

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with hourly uvi data.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_uvi()
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        self._initialize_figure()
        self._initialize_plot()

        hour_offset = day_offset * 24
        hour_range = slice(hour_offset, 24 + hour_offset)

        #### # Don't like
        first_date = datetime.fromisoformat(self._data[0][1])

        if day_offset == 0:
            hour_range = slice(0, 24 - first_date.hour)
        elif day_offset == 1:
            hour_range = slice(24 - first_date.hour, len(self._data))
        #### # Don't like

        data = {key: value[hour_range] for key, value in self._data_axes.items()}

        hours = [item.hour for item in data["time"]]

        figure = self._figure
        plot = self._plot

        plot_title = create_title(self._data, "UV index", hour_offset)
        plot.set_title(plot_title)
        plot.set_ylabel("UV Index")
        plot.set_xlabel("Hour")
        plot.tick_params(axis="x", labelrotation=45)
        plot.set_xticks(hours)

        plot.plot(
            hours,
            data["uvi"],
            label="UVI",
            color="violet",
        )

        plot.fill_between(
            hours,
            data["uvi"],
            -1,
            alpha=0.3,
            color="violet",
        )

        plot.set_xlim(0, 23)
        plot.set_ylim(-1, 15)

        plot.legend()

        return figure

    def plot_percipitation(self, day_offset: int = 0):
        """Creates a Figure based on wind data in the database.

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with hourly wind data.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_wind_speed()
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        self._initialize_figure()
        self._initialize_plot()

        hour_offset = day_offset * 24
        hour_range = slice(hour_offset, 24 + hour_offset)

        #### # Don't like
        first_date = datetime.fromisoformat(self._data[0][1])

        if day_offset == 0:
            hour_range = slice(0, 24 - first_date.hour)
        elif day_offset == 1:
            hour_range = slice(24 - first_date.hour, len(self._data))
        #### # Don't like

        data = {key: value[hour_range] for key, value in self._data_axes.items()}

        hours = [item.hour for item in data["time"]]

        figure = self._figure
        plot = self._plot

        plot_title = create_title(self._data, "Percipitation", hour_offset)
        plot.set_title(plot_title)
        plot.set_ylabel("Percipitation chance")
        plot.set_xlabel("Hour")
        plot.tick_params(axis="x", labelrotation=45)
        plot.set_xticks(hours)

        plot.yaxis.set_major_formatter(PercentFormatter(xmax=100))

        plot.plot(
            hours,
            data["percip"],
            label="Percip %",
            color="skyblue",
        )

        plot.set_xlim(0, 23)
        plot.set_ylim(-5, 105)

        plot.legend()

        return figure

    def plot_cloud_cover(self, day_offset: int = 0):
        """Creates a Figure based on cloud cover data in the database.

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with hourly cloud cover data.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_cloud_cover()
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        self._initialize_figure()
        self._initialize_plot()

        hour_offset = day_offset * 24
        hour_range = slice(hour_offset, 24 + hour_offset)

        #### # Don't like
        first_date = datetime.fromisoformat(self._data[0][1])

        if day_offset == 0:
            hour_range = slice(0, 24 - first_date.hour)
        elif day_offset == 1:
            hour_range = slice(24 - first_date.hour, len(self._data))
        #### # Don't like

        data = {key: value[hour_range] for key, value in self._data_axes.items()}

        hours = [item.hour for item in data["time"]]

        figure = self._figure
        plot = self._plot

        plot_title = create_title(self._data, "Cloud cover", hour_offset)
        plot.set_title(plot_title)
        plot.set_ylabel("Cloud cover percent")
        plot.set_xlabel("Hour")
        plot.tick_params(axis="x", labelrotation=45)
        plot.set_xticks(hours)

        plot.yaxis.set_major_formatter(PercentFormatter(xmax=100))

        plot.plot(
            hours,
            data["cloud"],
            label="Cover %",
            color="skyblue",
        )

        plot.set_xlim(0, 23)
        plot.set_ylim(-5, 105)

        plot.legend()

        return figure

    def plot_temp(self, day_offset: int = 0):
        """Creates a Figure based on temperature data in the database.

        Args:
            temp_scale: The temperature scale to display. Options are:
                - "celsius" (°C)
                - "fahrenheit" (°F)
                - "kelvin" (K)
                - "rankine" (°R)

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with temperature and feels-like temperature data.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_temp("fahrenheit")
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        self._initialize_figure()
        self._initialize_plot()

        hour_offset = day_offset * 24
        hour_range = slice(hour_offset, 24 + hour_offset)

        #### # Don't like
        first_date = datetime.fromisoformat(self._data[0][1])

        if day_offset == 0:
            hour_range = slice(0, 24 - first_date.hour)
        elif day_offset == 1:
            hour_range = slice(24 - first_date.hour, len(self._data))
        #### # Don't like

        data = {key: value[hour_range] for key, value in self._data_axes.items()}

        hours = [item.hour for item in data["time"]]

        figure = self._figure
        plot = self._plot

        plot_title = create_title(self._data, "Cloud cover", hour_offset)
        plot.set_title(plot_title)
        plot.set_ylabel("Temp " + TEMPERATURE_SCALE[self.temp_scale])
        plot.set_xlabel("Hour")
        plot.tick_params(axis="x", labelrotation=45)
        plot.set_xticks(hours)

        plot.plot(
            hours,
            data["temp"],
            label="Temp " + TEMPERATURE_SCALE[self.temp_scale],
            color="skyblue",
        )

        plot.fill_between(
            hours,
            data["temp"],
            self._lowest_plot_temp,
            alpha=0.3,
            color="skyblue",
        )

        plot.plot(
            hours,
            data["feel"],
            label="Feel " + TEMPERATURE_SCALE[self.temp_scale],
            color="salmon",
        )
        plot.fill_between(
            hours,
            data["feel"],
            self._lowest_plot_temp,
            alpha=0.3,
            color="salmon",
        )

        plot.set_ybound(self._lowest_plot_temp, self._highest_plot_temp)
        plot.set_xlim(0, 23)

        plot.legend()

        return figure

    def plot_wind_speed(self, day_offset: int = 0):
        """Creates a Figure based on wind data in the database.

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with hourly wind data.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_wind_speed()
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        self._initialize_figure()
        self._initialize_plot()

        hour_offset = day_offset * 24
        hour_range = slice(hour_offset, 24 + hour_offset)

        #### # Don't like
        first_date = datetime.fromisoformat(self._data[0][1])

        if day_offset == 0:
            hour_range = slice(0, 24 - first_date.hour)
        elif day_offset == 1:
            hour_range = slice(24 - first_date.hour, len(self._data))
        #### # Don't like

        data = {key: value[hour_range] for key, value in self._data_axes.items()}

        hours = [item.hour for item in data["time"]]

        figure = self._figure
        plot = self._plot

        plot_title = create_title(self._data, "Wind speed", hour_offset)
        plot.set_title(plot_title)
        plot.set_ylabel(r"mph")
        plot.set_xlabel("Hour")
        plot.tick_params(axis="x", labelrotation=45)
        plot.set_xticks(hours)

        plot.plot(
            hours,
            data["wind_speed"],
            label="Wind speed",
            color="skyblue",
        )

        plot.plot(
            hours,
            data["wind_gust"],
            label="Wind gust",
            color="salmon",
        )

        plot.set_xlim(0, 23)
        plot.set_ylim(self._lowest_plot_wind_speed, self._highest_plot_wind_speed)

        plot.legend()

        return figure

    def data_item_count(self):
        return len(self._data)


def main():
    pass


if __name__ == "__main__":
    main()
