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


def timestamp_to_time(time):

    return datetime.fromisoformat(time)


def format_func(value, tick_number):
    return datetime.strptime(str(int(value)), "%H").strftime("%I %p")


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

    TEMPERATURE_SCALE: dict[str, str] = {
        "celsius": "°C",
        "fahrenheit": "°F",
        "kelvin": "K",
        "rankine": "°R",
    }

    def __init__(self, cursor: sqlite3.Cursor, location: Location) -> None:

        if not isinstance(cursor, sqlite3.Cursor):
            raise TypeError
        if not isinstance(location, Location):
            raise TypeError

        self._cursor = cursor

        self._initialize_figure()
        self._initialize_plot()

        self._location = location

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

    def plot_temp(
        self,
        day_offset: int = 0,
        temp_scale: Literal[
            "celsius", "fahrenheit", "kelvin", "rankine"
        ] = "fahrenheit",
    ):
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

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = current_date_time + timedelta(days=day_offset)

            year = str(date.year)

            if len(str(date.month)) == 1:
                month = "0" + str(date.month)
            else:
                month = str(date.month)

            if len(str(date.day)) == 1:
                day = "0" + str(date.day)
            else:
                day = str(date.day)

            query = f"""
                    SELECT city,
                        date_time,
                        temp,
                        feels_like
                    FROM information
                    WHERE strftime('%Y', date_time) = '{year}'
                        AND strftime('%m', date_time) = '{month}'
                        AND strftime('%d', date_time) = '{day}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(query).fetchall()

            return data

        def prepare_data(data: list[Any]):

            def convert_temp(temp: float) -> float:
                if temp_scale == "fahrenheit":
                    return k_to_f(temp)
                elif temp_scale == "celsius":
                    return k_to_c(temp)
                elif temp_scale == "rankine":
                    return k_to_r(temp)
                else:  # kelvin
                    return temp

            lowest_temp = float("inf")
            highest_temp = float("-inf")
            time: list[int] = []
            real_temp: list[float] = []
            feel_temp: list[float] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                converted_temp = convert_temp(item[Indexes.temp_index.value])
                converted_feel = convert_temp(item[Indexes.feel_index.value])
                real_temp.append(converted_temp)
                feel_temp.append(converted_feel)
                lowest_temp = min(lowest_temp, converted_temp, converted_feel)
                highest_temp = max(highest_temp, converted_temp, converted_feel)

            return {
                "time": time,
                "temp": real_temp,
                "feel_temp": feel_temp,
                "low_temp": lowest_temp,
                "high_temp": highest_temp,
            }

        def plot_axes(axes: dict[str, Any]):
            plot.set_title(plot_title)
            plot.set_ylabel("Temp " + self.TEMPERATURE_SCALE[temp_scale])
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.plot(
                axes["time"],
                axes["temp"],
                label="Temp " + self.TEMPERATURE_SCALE[temp_scale],
                color="skyblue",
            )

            plot.fill_between(
                axes["time"],
                axes["temp"],
                axes["low_temp"] - 5,
                alpha=0.3,
                color="skyblue",
            )

            plot.plot(
                axes["time"],
                axes["feel_temp"],
                label="Feel " + self.TEMPERATURE_SCALE[temp_scale],
                color="salmon",
            )
            plot.fill_between(
                axes["time"],
                axes["feel_temp"],
                axes["low_temp"] - 5,
                alpha=0.3,
                color="salmon",
            )

            plot.set_ybound(axes["low_temp"] - 5, axes["high_temp"] + 5)
            plot.set_xlim(0, 23)

            plot.legend()

        def create_title(data):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + " temperature "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).month)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).day)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).year)
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            temp_index = 2
            feel_index = 3

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

        return figure

    def plot_sun(self, day_offset: int = 0):
        """Creates a Figure based on sun data in the database.

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with hourly uvi and cloud cover data.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_sun()
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = current_date_time + timedelta(days=day_offset)

            year = str(date.year)

            if len(str(date.month)) == 1:
                month = "0" + str(date.month)
            else:
                month = str(date.month)

            if len(str(date.day)) == 1:
                day = "0" + str(date.day)
            else:
                day = str(date.day)

            quere = f"""
                    SELECT city,
                        date_time,
                        clouds,
                        uvi
                    FROM information
                    WHERE strftime('%Y', date_time) = '{year}'
                        AND strftime('%m', date_time) = '{month}'
                        AND strftime('%d', date_time) = '{day}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(quere).fetchall()

            return data

        def prepare_data(data: list[Any]):

            time: list[int] = []
            clouds: list[float] = []
            uvi: list[float] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                clouds.append(item[Indexes.clouds_index.value])
                uvi.append(item[Indexes.uvi_index.value])

            return {"time": time, "clouds": clouds, "uvi": uvi}

        def plot_axes(axes: dict[str, Any]):

            plot.set_title(plot_title)
            plot.set_ylabel(r"Cloud cover % uvi")
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.plot(
                axes["time"],
                axes["clouds"],
                label="Cloud cover",
                color="skyblue",
            )

            plot.plot(
                axes["time"],
                axes["uvi"],
                label="Uvi",
                color="salmon",
            )
            plot.fill_between(
                axes["time"],
                axes["uvi"],
                0,
                alpha=0.3,
                color="salmon",
            )

            plot.set_xlim(0, 23)
            plot.set_ybound(0)

            plot.legend()

        def create_title(data):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + " clouds and uvi "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).month)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).day)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).year)
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            clouds_index = 2
            uvi_index = 3

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

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

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = current_date_time + timedelta(days=day_offset)

            year = str(date.year)

            if len(str(date.month)) == 1:
                month = "0" + str(date.month)
            else:
                month = str(date.month)

            if len(str(date.day)) == 1:
                day = "0" + str(date.day)
            else:
                day = str(date.day)

            quere = f"""
                    SELECT city,
                        date_time,
                        wind_speed,
                        wind_gust,
                        wind_deg
                    FROM information
                    WHERE strftime('%Y', date_time) = '{year}'
                        AND strftime('%m', date_time) = '{month}'
                        AND strftime('%d', date_time) = '{day}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(quere).fetchall()

            return data

        def prepare_data(data: list[Any]):

            time: list[int] = []
            wind_speed: list[float] = []
            wind_gust: list[float] = []
            wind_deg: list[int] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                wind_speed.append(item[Indexes.wind_speed.value])
                wind_gust.append(item[Indexes.wind_gust.value])
                wind_deg.append(item[Indexes.wind_deg.value])

            return {
                "time": time,
                "speed": wind_speed,
                "gust": wind_gust,
                "deg": wind_deg,
            }

        def plot_axes(axes: dict[str, Any]):

            plot.set_title(plot_title)
            plot.set_ylabel(r"mph")
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.plot(
                axes["time"],
                axes["speed"],
                label="Wind speed",
                color="skyblue",
            )

            plot.plot(
                axes["time"],
                axes["gust"],
                label="Wind gust",
                color="salmon",
            )

            plot.set_xlim(0, 23)

            plot.legend()

        def create_title(data):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + " wind "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).month)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).day)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).year)
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            wind_speed = 2
            wind_gust = 3
            wind_deg = 4

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

        return figure

    def plot_one_field(
        self,
        day_offset: int,
        field: Literal[
            "temp",
            "feels_like",
            "uvi",
            "clouds",
            "humidity",
            "wind_speed",
            "wind_deg",
            "wind_gust",
            "dew_point",
            "pop",
        ],
        y_axis_label: str = "Units of measure",
    ):
        """Creates a Figure based on a single weather field in the database.

        Args:
            field: The weather field to plot. Options include:
                - "temp" (temperature)
                - "feels_like" (apparent temperature)
                - "uvi" (ultraviolet index)
                - "clouds" (cloud cover percentage)
                - "humidity" (relative humidity)
                - "wind_speed" (wind speed in mph)
                - "wind_deg" (wind direction in degrees)
                - "wind_gust" (wind gust speed in mph)
            y_axis_label: Label for the y-axis (default: "Units of measure")

        Returns:
            matplotlib.figure.Figure: A matplotlib Figure object containing the plot
                with hourly data for the specified weather field.

        Example:
            >>> from graphs import MakePlot
            >>> from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            >>> import tkinter as tk
            >>> root = tk.Tk()
            >>> figure = MakePlot(cursor).plot_one_field("uvi", "mph")
            >>> figure_canvas = FigureCanvasTkAgg(figure, root)
            >>> canvas = figure_canvas.get_tk_widget()
            >>> canvas.pack()
        """

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = current_date_time + timedelta(days=day_offset)

            year = str(date.year)

            if len(str(date.month)) == 1:
                month = "0" + str(date.month)
            else:
                month = str(date.month)

            if len(str(date.day)) == 1:
                day = "0" + str(date.day)
            else:
                day = str(date.day)

            quere = f"""
                    SELECT city,
                        date_time,
                        {field}
                    FROM information
                    WHERE strftime('%Y', date_time) = '{year}'
                        AND strftime('%m', date_time) = '{month}'
                        AND strftime('%d', date_time) = '{day}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(quere).fetchall()

            return data

        def prepare_data(data: list[Any]):

            time: list[int] = []
            field: list[Any] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                field.append(item[Indexes.field.value])

            return {
                "time": time,
                "field": field,
            }

        def plot_axes(axes: dict[str, Any]):

            plot.set_title(plot_title)
            plot.set_ylabel(y_axis_label)
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.plot(
                axes["time"],
                axes["field"],
                label=field.capitalize(),
                color="skyblue",
            )

            plot.set_xlim(0, 23)

            plot.legend()

        def create_title(data):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + f" {field} "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).month)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).day)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).year)
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            field = 2

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

        return figure

    #
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

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = current_date_time + timedelta(days=day_offset)

            year = str(date.year)

            if len(str(date.month)) == 1:
                month = "0" + str(date.month)
            else:
                month = str(date.month)

            if len(str(date.day)) == 1:
                day = "0" + str(date.day)
            else:
                day = str(date.day)

            quere = f"""
                    SELECT city,
                        date_time,
                        pop
                    FROM information
                    WHERE strftime('%Y', date_time) = '{year}'
                        AND strftime('%m', date_time) = '{month}'
                        AND strftime('%d', date_time) = '{day}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(quere).fetchall()

            return data

        def prepare_data(data: list[Any]):

            time: list[int] = []
            percip: list[float] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                percip.append(item[Indexes.percip.value] * 100)

            return {
                "time": time,
                "percip": percip,
            }

        def plot_axes(axes: dict[str, Any]):

            plot.set_title(plot_title)
            plot.set_ylabel("Percipitation chance")
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.yaxis.set_major_formatter(PercentFormatter(xmax=100))

            plot.plot(
                axes["time"],
                axes["percip"],
                label="Percip %",
                color="skyblue",
            )

            plot.set_xlim(0, 23)
            plot.set_ylim(-5, 105)

            plot.legend()

        def create_title(data):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + " Percipitation "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).month)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).day)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).year)
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            percip = 2

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

        return figure

    #
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

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = current_date_time + timedelta(days=day_offset)

            year = str(date.year)

            if len(str(date.month)) == 1:
                month = "0" + str(date.month)
            else:
                month = str(date.month)

            if len(str(date.day)) == 1:
                day = "0" + str(date.day)
            else:
                day = str(date.day)

            quere = f"""
                    SELECT city,
                        date_time,
                        clouds
                    FROM information
                    WHERE strftime('%Y', date_time) = '{year}'
                        AND strftime('%m', date_time) = '{month}'
                        AND strftime('%d', date_time) = '{day}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(quere).fetchall()

            return data

        def prepare_data(data: list[Any]):

            time: list[int] = []
            clouds: list[float] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                clouds.append(item[Indexes.clouds.value])

            return {
                "time": time,
                "clouds": clouds,
            }

        def plot_axes(axes: dict[str, Any]):

            plot.set_title(plot_title)
            plot.set_ylabel("Cloud cover percent")
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.yaxis.set_major_formatter(PercentFormatter(xmax=100))

            plot.plot(
                axes["time"],
                axes["clouds"],
                label="Cover %",
                color="skyblue",
            )

            plot.set_xlim(0, 23)
            plot.set_ylim(-5, 105)

            plot.legend()

        def create_title(data):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + " Cloud cover "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).month)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).day)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).year)
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            clouds = 2

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

        return figure

    #
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

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = current_date_time + timedelta(days=day_offset)

            year = str(date.year)

            if len(str(date.month)) == 1:
                month = "0" + str(date.month)
            else:
                month = str(date.month)

            if len(str(date.day)) == 1:
                day = "0" + str(date.day)
            else:
                day = str(date.day)

            quere = f"""
                    SELECT city,
                        date_time,
                        uvi
                    FROM information
                    WHERE strftime('%Y', date_time) = '{year}'
                        AND strftime('%m', date_time) = '{month}'
                        AND strftime('%d', date_time) = '{day}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(quere).fetchall()

            return data

        def prepare_data(data: list[Any]):

            time: list[int] = []
            uvi: list[float] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                uvi.append(item[Indexes.uvi.value])

            return {
                "time": time,
                "uvi": uvi,
            }

        def plot_axes(axes: dict[str, Any]):

            plot.set_title(plot_title)
            plot.set_ylabel("UV Index")
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.plot(
                axes["time"],
                axes["uvi"],
                label="UVI",
                color="violet",
            )

            plot.fill_between(
                axes["time"],
                axes["uvi"],
                -1,
                alpha=0.3,
                color="violet",
            )

            plot.set_xlim(0, 23)
            plot.set_ylim(-1, 15)

            plot.legend()

        def create_title(data):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + " UV Index "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).month)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).day)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).year)
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            uvi = 2

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

        return figure

    #
    def plot_dew_point(
        self,
        day_offset: int = 0,
        temp_scale: Literal[
            "celsius", "fahrenheit", "kelvin", "rankine"
        ] = "fahrenheit",
    ):
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

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = current_date_time + timedelta(days=day_offset)

            year = str(date.year)

            if len(str(date.month)) == 1:
                month = "0" + str(date.month)
            else:
                month = str(date.month)

            if len(str(date.day)) == 1:
                day = "0" + str(date.day)
            else:
                day = str(date.day)

            query = f"""
                    SELECT city,
                        date_time,
                        dew_point
                    FROM information
                    WHERE strftime('%Y', date_time) = '{year}'
                        AND strftime('%m', date_time) = '{month}'
                        AND strftime('%d', date_time) = '{day}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(query).fetchall()

            return data

        def prepare_data(data: list[Any]):

            def convert_temp(temp: float) -> float:
                if temp_scale == "fahrenheit":
                    return k_to_f(temp)
                elif temp_scale == "celsius":
                    return k_to_c(temp)
                elif temp_scale == "rankine":
                    return k_to_r(temp)
                else:  # kelvin
                    return temp

            lowest_temp = float("inf")
            highest_temp = float("-inf")
            time: list[int] = []
            dew_point: list[float] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                converted_temp = convert_temp(item[Indexes.dew_point.value])

                dew_point.append(converted_temp)

                lowest_temp = min(lowest_temp, converted_temp)
                highest_temp = max(highest_temp, converted_temp)

            return {
                "time": time,
                "dew_point": dew_point,
                "low_temp": lowest_temp,
                "high_temp": highest_temp,
            }

        def plot_axes(axes: dict[str, Any]):
            plot.set_title(plot_title)
            plot.set_ylabel("Temp " + self.TEMPERATURE_SCALE[temp_scale])
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.plot(
                axes["time"],
                axes["dew_point"],
                label="Temp " + self.TEMPERATURE_SCALE[temp_scale],
                color="skyblue",
            )

            plot.fill_between(
                axes["time"],
                axes["dew_point"],
                axes["low_temp"] - 5,
                alpha=0.3,
                color="skyblue",
            )

            plot.set_ybound(axes["low_temp"] - 5, axes["high_temp"] + 5)
            plot.set_xlim(0, 23)

            plot.legend()

        def create_title(data):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + " temperature "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).month)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).day)
                + "-"
                + str(timestamp_to_time(data[0][Indexes.time_index.value]).year)
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            dew_point = 2

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

        return figure

    #
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

        def get_data(day_offset: int):

            current_date_time = datetime.now()
            date = str(current_date_time + timedelta(days=day_offset))[:10]

            quere = f"""
                    SELECT city,
                        date_time,
                        humidity
                    FROM information
                    WHERE strftime('%Y-%m-%d', date_time) = '{date}'
                        AND latitude = '{self._location.latitude}'
                        AND longitude = '{self._location.longitude}';
                    """
            data = self._cursor.execute(quere).fetchall()

            return data

        def prepare_data(data: list[Any]):

            time: list[int] = []
            humidity: list[float] = []

            for item in data:
                time.append(timestamp_to_time(item[Indexes.time_index.value]).hour)

                humidity.append(item[Indexes.humidity.value])

            return {
                "time": time,
                "humidity": humidity,
            }

        def plot_axes(axes: dict[str, Any]):

            plot.set_title(plot_title)
            plot.set_ylabel("Relative humidity")
            plot.set_xlabel("Hour")
            plot.tick_params(axis="x", labelrotation=45)
            plot.set_xticks(axes["time"])

            plot.yaxis.set_major_formatter(PercentFormatter(xmax=100))

            plot.plot(
                axes["time"],
                axes["humidity"],
                label="Humidity %",
                color="skyblue",
            )

            plot.fill_between(
                axes["time"],
                axes["humidity"],
                -5,
                color="skyblue",
                alpha=0.3,
            )

            plot.set_xlim(0, 23)
            plot.set_ylim(-5, 105)

            plot.legend()

        def create_title(
            data,
        ):
            return (
                str(data[0][Indexes.city_index.value]).capitalize()
                + " Humidity "
                + str(timestamp_to_time(data[0][Indexes.time_index.value]))[:10]
            )

        figure = self._figure
        plot = self._plot

        data = get_data(day_offset)

        class Indexes(Enum):
            city_index = 0
            time_index = 1
            humidity = 2

        plot_title = create_title(data)

        axes = prepare_data(data)
        plot_axes(axes)

        return figure


def main():

    pass


if __name__ == "__main__":
    main()
