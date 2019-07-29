#!/usr/bin/env python3

import argparse
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List
from psycopg2 import sql
from use_postgres import UseDatabase
from statsmodels.tsa.stattools import adfuller

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

def grab_data_for_adf(sensor_id: str, variable: str) -> List:
    with UseDatabase(aurora_creds) as cursor:
        table_name = f'grow_data_{sensor_id}'
        cursor.execute(sql.SQL("""SELECT datetime, {} 
                        FROM {}
                        WHERE sensor_id = {}""")
                        .format(sql.Identifier(variable),
                                sql.Identifier(table_name),
                                sql.Literal(sensor_id)))
        response = cursor.fetchall()
    dataframe = pd.DataFrame({'date': [x[0] for x in response],
                            'value': [float(x[1]) for x in response]})
    dataframe.set_index('date', inplace=True)
    data_1d = dataframe.iloc[:,0].values # takes all rows of the first column, converts pd series to numpy ndarray
    return data_1d

def aug_dickey_fuller_test(array: List) -> '':
    test = adfuller(array, autolag='AIC')
    test_results = pd.Series(test[0:4], index=['Test Statistic', 'P-value', 'Lag Used', '# of Observations Used'])
    for key, value in test[4].items():
        test_results[f'Critical Value: {key}'] = value

    if test_results['Test Statistic'] < test_results['Critical Value: 1%']:
        test_results['1% Finding'] = 'H0 rejected: Timeseries is stationary'
    else:
        test_results['1% Finding'] = 'H0 failed to reject: Timeseries is non-stationary'

    if test_results['Test Statistic'] < test_results['Critical Value: 5%']:
        test_results['5% Finding'] = 'H0 rejected: Timeseries is stationary'
    else:
        test_results['5% Finding'] = 'H0 failed to reject: Timeseries is non-stationary'

    if test_results['Test Statistic'] < test_results['Critical Value: 10%']:
        test_results['10% Finding'] = 'H0 rejected: Timeseries is stationary'
    else:
        test_results['10% Finding'] = 'H0 failed to reject: Timeseries is non-stationary'

    return test_results

def grab_data_for_plot(sensor_id: str, variable: str) -> List:
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
    plt.plot(data)
    plt.xlabel([start_date, end_date])
    plt.title(variable)
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('grow_sensor_id')
    parser.add_argument('variable', choices={'soil_moisture',
                                            'light', 
                                            'air_temperature'})
    args = parser.parse_args()

    data_1d = grab_data_for_adf(args.grow_sensor_id, args.variable)
    test_results = aug_dickey_fuller_test(data_1d)
    print(test_results)
    data, start_date, end_date, variable = grab_data_for_plot(args.grow_sensor_id, args.variable)
    plot_data(data, start_date, end_date, variable)



