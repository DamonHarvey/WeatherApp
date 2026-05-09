import sqlite3
from sqlite3 import Error
import tables


def create_connection(db_file):

    connection = None
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as error:
        print(error)

    return connection


def create_table(connecton: sqlite3.Connection, statment: str):

    cur = connecton.cursor()
    try:
        cur.execute(statment)
    except Error as error:
        print(error)


def main():
    db_file = "WeatherData.db"
    connection = create_connection(db_file)
    if connection is None:
        return

    create_table(connection, tables.TABLE_location)
    create_table(connection, tables.TABLE_weather)

    connection.commit()
    connection.close()

    print("done")


if __name__ == "__main__":
    main()
