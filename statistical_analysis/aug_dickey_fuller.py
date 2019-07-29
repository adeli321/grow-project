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

def grab_data(sensor_id: str, variable: str) -> List:
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
    data_1d = dataframe.iloc[:,0].values
    return data_1d

def aug_dickey_fuller_test(array: List) -> '':
    test = adfuller(array, autolag='AIC')
    test_results = pd.Series(test[0:4], index=['Test Statistic', 'P-value', 'Lag Used', '# of Observations Used'])
    for key, value in test[4].items():
        test_results[f'Critical Value: {key}'] = value
    return test_results

