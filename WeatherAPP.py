import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from my_modules.data_base import DataBase
from my_modules.graphs import MakePlot
import my_modules.weather_api as weather_api
from my_modules.weather_api import Location


class App:

    TEXT_COLOR = "#000000"
    BUTTON_COLOR = "#DA93D0"
    BUTTON_COLOR_TWO = "#9BD7E9"

    def __init__(self, data_base: DataBase, location: Location) -> None:
        self._initialized = False

        self._root = tk.Tk()
        self._data_base = data_base

        self._location = location
        self.check_and_call_api()

        self.make_plot = MakePlot(self._data_base.cursor, location)

        self.last_plot = self._plot_temp

        self._initialize_window()
        self._initialize_time_frame_buttons()
        self._initialize_graph_buttons()
        self._initialize_plot()

        self._initialized = True

    def run(self):

        tk.mainloop()

    def _initialize_window(self):
        root = self._root

        root.title("WeatherApp")
        root.iconbitmap(r"icon.ico")
        root.resizable(False, False)
        root.config(background="#ffffff")

    def _initialize_time_frame_buttons(self):
        root = self._root

        BUTTON_HEIGHT = 2

        button_frame = tk.Frame(root)
        button_frame.grid(column=0, row=0, columnspan=2)

        button = tk.Button(
            button_frame,
            name="a",
            text="Todays weather information",
            height=BUTTON_HEIGHT,
            width=27,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR,
            command=lambda: self.last_plot(0),
        )
        button.grid(column=4, row=0, sticky="nsew")

        button = tk.Button(
            button_frame,
            name="b",
            text="Tomorrows weather information",
            height=BUTTON_HEIGHT,
            width=27,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR,
            command=lambda: self.last_plot(1),
        )
        button.grid(column=5, row=0, sticky="nsew")

        button = tk.Button(
            button_frame,
            name="change location",
            text="Location:",
            height=BUTTON_HEIGHT,
            width=10,
            foreground=self.TEXT_COLOR,
            background="#1DC79C",
            command=self._change_location,
        )
        button.grid(column=0, row=0, sticky="nsew")

        WIDTH = 9

        city = tk.Text(button_frame, name="city", height=BUTTON_HEIGHT, width=WIDTH)
        city.insert(0.0, self._location.city)
        city.grid(column=1, row=0, sticky="nsew")

        self.city = city

        state = tk.Text(button_frame, name="state", height=BUTTON_HEIGHT, width=WIDTH)
        state.insert(0.0, self._location.state)
        state.grid(column=2, row=0, sticky="nsew")

        self.state = state

        country = tk.Text(
            button_frame, name="country", height=BUTTON_HEIGHT, width=WIDTH
        )
        country.insert(0.0, self._location.country)
        country.grid(column=3, row=0, sticky="nsew")

        self.country = country

    def _initialize_graph_buttons(self):
        root = self._root

        BUTTON_WIDTH = 8
        BUTTON_HEIGHT = 1

        button_frame = tk.Frame(root)
        button_frame.grid(column=1, row=1, rowspan=1)

        label = tk.Label(
            button_frame,
            name="plots",
            text="Graphs",
            height=2,
            background="#ffffff",
        )
        label.grid(column=0, row=0, sticky="nesw")

        button = tk.Button(
            button_frame,
            name="temp",
            text="Temp",
            height=BUTTON_HEIGHT,
            width=BUTTON_WIDTH,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR_TWO,
            command=lambda: self._plot_temp(self.day),
        )
        button.grid(column=0, row=1, sticky="nesw")

        button = tk.Button(
            button_frame,
            name="wind",
            text="Wind",
            height=BUTTON_HEIGHT,
            width=BUTTON_WIDTH,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR_TWO,
            command=lambda: self._plot_wind_speed(self.day),
        )
        button.grid(column=0, row=2, sticky="nesw")

        button = tk.Button(
            button_frame,
            name="percip",
            text="Percip",
            height=BUTTON_HEIGHT,
            width=BUTTON_WIDTH,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR_TWO,
            command=lambda: self._plot_percipitaiton(self.day),
        )
        button.grid(column=0, row=3, sticky="nesw")

        button = tk.Button(
            button_frame,
            name="cloud_cover",
            text="Cloud",
            height=BUTTON_HEIGHT,
            width=BUTTON_WIDTH,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR_TWO,
            command=lambda: self._plot_cloud_cover(self.day),
        )
        button.grid(column=0, row=4, sticky="nesw")

        button = tk.Button(
            button_frame,
            name="humid",
            text="Humidity",
            height=BUTTON_HEIGHT,
            width=BUTTON_WIDTH,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR_TWO,
            command=lambda: self._plot_relative_humidity(self.day),
        )
        button.grid(column=0, row=5, sticky="nesw")

        button = tk.Button(
            button_frame,
            name="dew_point",
            text="Dew point",
            height=BUTTON_HEIGHT,
            width=BUTTON_WIDTH,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR_TWO,
            command=lambda: self._plot_dew_point(self.day),
        )
        button.grid(column=0, row=6, sticky="nesw")

        button = tk.Button(
            button_frame,
            name="uvi",
            text="UV Index",
            height=BUTTON_HEIGHT,
            width=BUTTON_WIDTH,
            foreground=self.TEXT_COLOR,
            background=self.BUTTON_COLOR_TWO,
            command=lambda: self._plot_uvi(self.day),
        )
        button.grid(column=0, row=7, sticky="nesw")

    def _initialize_plot(self):

        self._plot_temp(0)

    def _change_location(self):

        self._location.set_location(
            self.city.get(0.0, "end")[:-1],
            self.state.get(0.0, "end")[:-1],
            self.country.get(0.0, "end")[:-1],
        )

        self.check_and_call_api()

        self.make_plot.update_data()

        self.last_plot(self.day)

    def check_and_call_api(self):

        if not self._data_base.is_next_48_hours_stored(self._location):
            print(f"Calling api, Hours stored:{self.make_plot.data_item_count()}")

            data = weather_api.get_location_data(self._location)
            self._data_base.add_data(data)
            self._data_base.update_data_base()

        else:
            print("Data for next 48 hours stored")

    def _plot_temp(self, day_offset):
        self.day = day_offset

        figure = self.make_plot.plot_temp(day_offset)
        figure_canvas = FigureCanvasTkAgg(figure, self._root)
        canvas = figure_canvas.get_tk_widget()

        canvas.grid(column=0, row=1, columnspan=1)

        if self._initialized is True:
            self.graph.destroy()
        self.graph = canvas
        self.last_plot = self._plot_temp

    def _plot_wind_speed(self, day_offset):
        self.day = day_offset

        figure = self.make_plot.plot_wind_speed(day_offset)
        figure_canvas = FigureCanvasTkAgg(figure, self._root)
        canvas = figure_canvas.get_tk_widget()

        canvas.grid(column=0, row=1)

        self.graph.destroy()
        self.graph = canvas
        self.last_plot = self._plot_wind_speed

    def _plot_cloud_cover(self, day_offset):
        self.day = day_offset

        figure = self.make_plot.plot_cloud_cover(day_offset)
        figure_canvas = FigureCanvasTkAgg(figure, self._root)
        canvas = figure_canvas.get_tk_widget()

        canvas.grid(column=0, row=1)

        self.graph.destroy()
        self.graph = canvas
        self.last_plot = self._plot_cloud_cover

    def _plot_relative_humidity(self, day_offset):
        self.day = day_offset

        figure = self.make_plot.plot_humidity(day_offset)
        figure_canvas = FigureCanvasTkAgg(figure, self._root)
        canvas = figure_canvas.get_tk_widget()

        canvas.grid(column=0, row=1)

        self.graph.destroy()
        self.graph = canvas
        self.last_plot = self._plot_relative_humidity

    def _plot_dew_point(self, day_offset):
        self.day = day_offset

        figure = self.make_plot.plot_dew_point(day_offset)
        figure_canvas = FigureCanvasTkAgg(figure, self._root)
        canvas = figure_canvas.get_tk_widget()

        canvas.grid(column=0, row=1)

        self.graph.destroy()
        self.graph = canvas
        self.last_plot = self._plot_dew_point

    def _plot_percipitaiton(self, day_offset):
        self.day = day_offset

        figure = self.make_plot.plot_percipitation(day_offset)
        figure_canvas = FigureCanvasTkAgg(figure, self._root)
        canvas = figure_canvas.get_tk_widget()

        canvas.grid(column=0, row=1)

        self.graph.destroy()
        self.graph = canvas
        self.last_plot = self._plot_percipitaiton

    def _plot_uvi(self, day_offset):
        self.day = day_offset

        figure = self.make_plot.plot_uvi(day_offset)
        figure_canvas = FigureCanvasTkAgg(figure, self._root)
        canvas = figure_canvas.get_tk_widget()

        canvas.grid(column=0, row=1)

        self.graph.destroy()
        self.graph = canvas
        self.last_plot = self._plot_uvi


def main():
    db_file = "WeatherData.db"
    db = DataBase(db_file)

    location = Location()

    db.add_data(weather_api.get_location_data(location))
    db.update_data_base()

    # location.set_location("bondurant", "iowa", "usa")

    app = App(db, location)
    app.run()

    db.connection.close()


if __name__ == "__main__":
    main()
