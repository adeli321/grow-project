#!/usr/bin/env python3

import argparse
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List
from psycopg2 import sql
from use_postgres import UseDatabase

db_creds = {
    'host': 'localhost', 
    'user': '', 
    'database': ''
}

aurora_creds = {
    'host': '',
    'port': 5432,
    'user': '',
    'password': ''
}

def grab_data(sensor_id: str, variable: str) -> List:
    with UseDatabase(aurora_creds) as cursor:
        table_name = f'grow_data_{sensor_id}'
        cursor.execute(sql.SQL("""SELECT {} FROM {}
                        WHERE sensor_id = {}""")
                        .format(sql.Identifier(variable),
                                sql.Identifier(table_name),
                                sql.Literal(sensor_id)))
        response = cursor.fetchall()
        cursor.execute(sql.SQL("""SELECT MIN(datetime), 
                                MAX(datetime)
                                FROM {}
                                WHERE sensor_id = {}""")
                        .format(sql.Identifier(table_name),
                                sql.Literal(sensor_id)))
        dates = cursor.fetchall()
        start_date = dates[0][0].strftime('%Y-%m-%d %H:%M:%S')
        end_date = dates[0][1].strftime('%Y-%m-%d %H:%M:%S')
    return response, start_date, end_date, variable

def plot_data(data: List, start_date: str, end_date: str, variable: str) -> 'plot':
    fig, axs = plt.subplots(1, 2, tight_layout=True)
    data = [float(x[0]) for x in data]
    # data = np.asarray(data)

    axs[0].plot(data)
    axs[1].hist(data, bins=20)
    # axs[0].xlabel([start_date, end_date])
    # axs[0].title(variable)
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('grow_sensor_id')
    parser.add_argument('variable', choices={'soil_moisture',
                                            'light', 
                                            'air_temperature'})
    args = parser.parse_args()

    data, start_date, end_date, variable = grab_data(args.grow_sensor_id, args.variable)
    plot_data(data, start_date, end_date, variable)



