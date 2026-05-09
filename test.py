from my_modules.data_base import DataBase
from my_modules.weather_api import get_location_data, Location
from my_modules.graphs import MakePlot

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def main():

    root = tk.Tk()

    loc = Location()
    loc.set_location("bondurant", "iowa", "usa")
    # data = get_location_data(loc)

    db = DataBase("WeatherData.db")

    plotr = MakePlot(db.cursor, loc)

    figure = plotr.plot_temp(1)

    figure_canvas = FigureCanvasTkAgg(figure, root)
    canvas = figure_canvas.get_tk_widget()
    canvas.pack()

    # db.add_data(data)
    # db.update_data_base()

    db.connection.close()

    root.mainloop()


if __name__ == "__main__":
    main()
