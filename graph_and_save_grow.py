#!/usr/bin/env python3

import argparse
import datetime
import os
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from psycopg2 import sql
from typing import List
from use_postgres import UseDatabase

aurora_creds = {
    'host': '',
    'port': 5432,
    'user': '',
    'password': ''
}

def grab_grow_sensor_uptimes() -> List:
    """Fetch and return all GROW sensor id's and their start and end datetimes"""
    url = 'https://grow.thingful.net/api/entity/timeSeriesInformations/get'
    header = {'Authorization': ''}
    response = requests.post(url, headers=header)
    json_object = response.json()
    current_sensors = []
    sensor_uptime_list = []
    for i in json_object['TimeSeriesInformations']:
        sensor_id = json_object['TimeSeriesInformations'][i]['LocationIdentifier'][-8:]
        if sensor_id not in current_sensors:
            current_sensors.append(sensor_id)
            sensor_details = []
            sensor_details.append(sensor_id)
            sensor_details.append(json_object['TimeSeriesInformations'][i]['StartDate'])
            sensor_details.append(json_object['TimeSeriesInformations'][i]['EndDate'])
            sensor_uptime_list.append(sensor_details)
    return sensor_uptime_list

def calculate_grow_time_intervals(sensor_uptimes: List, sensor_id: str) -> List:
    total_time_interval = []
    for i in sensor_uptimes:
        if i[0] == sensor_id:
            total_time_interval.append(i[1]) # start datetime
            total_time_interval.append(i[2]) # end datetime
    start_dt = datetime.datetime.strptime(total_time_interval[0],'%Y%m%d%H%M%S')
    end_dt = datetime.datetime.strptime(total_time_interval[1],'%Y%m%d%H%M%S')
    delta = end_dt - start_dt

    time_intervals = []
    while delta > datetime.timedelta(0):
        if delta < datetime.timedelta(days=7):
            interval = []
            end = end_dt 
            interval.append(start_dt.strftime('%Y%m%dT%H%M%S')) # include T for postgres insert
            interval.append(end_dt.strftime('%Y%m%dT%H%M%S'))
            time_intervals.append(interval)
            break
        else:
            interval = []
            end = start_dt + datetime.timedelta(days=7)
            interval.append(start_dt.strftime('%Y%m%dT%H%M%S'))
            interval.append(end.strftime('%Y%m%dT%H%M%S'))
            time_intervals.append(interval)
            delta -= datetime.timedelta(days=7)
            start_dt = end
    return time_intervals 

def grab_data(sensor_id: str, start_end_interval: List) -> List:
    with UseDatabase(aurora_creds) as cursor:
        table_name = f'grow_data_{sensor_id}'
        cursor.execute(sql.SQL("""SELECT soil_moisture, light, air_temperature, datetime
                        FROM {}
                        WHERE sensor_id = {}
                        AND datetime >= {}
                        AND datetime <= {}""")
                        .format(sql.Identifier(table_name),
                                sql.Literal(sensor_id),
                                sql.Literal(start_end_interval[0]),
                                sql.Literal(start_end_interval[1])))
        response = cursor.fetchall()
    return response

def graph_me_up(sensor_id: str, data: List, start_end_interval: List) -> 'Matplotlib Graph':
    """Graph the three extracted GROW attributes"""
    datetimes = [pd.to_datetime(x[3]) for x in data]
    y1 = np.array([x[0] for x in data])
    y2 = np.array([x[1] for x in data])
    y3 = np.array([x[2] for x in data])
    plt.plot(datetimes, y1, 'r', label='calibrated_soil_moisture' + ' %')
    plt.plot(datetimes, y2, 'g', label='light' + ' mol/m2/d')
    plt.plot(datetimes, y3, 'b', label='air_temperature' + ' C')
    plt.xticks(rotation=35, fontsize = 8)
    plt.legend()
    if os.path.isdir(f'grow_pngs/{sensor_id}'):
        pass
    else:
        os.mkdir(f'grow_pngs/{sensor_id}')
    plt.savefig(f'grow_pngs/{sensor_id}/{sensor_id}-{start_end_interval[0]}-{start_end_interval[1]}')
    plt.close()
    # plt.show()

if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('sensor_id')
    # args = parser.parse_args()

    # sensor_uptime_list = grab_grow_sensor_uptimes()
    # time_intervals = calculate_grow_time_intervals(sensor_uptime_list, args.sensor_id)

    sensor_uptime_list = grab_grow_sensor_uptimes()
    for i in sensor_uptime_list:
        time_intervals = calculate_grow_time_intervals(sensor_uptime_list, i[0])
        for t in time_intervals:
            data = grab_data(i[0], t)
            graph_me_up(i[0], data, t)
        print(f'Saved PNG for {i[0]}')
