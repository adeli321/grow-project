#! /usr/bin/env python3

import requests
import json
import datetime
from typing import List
from use_postgres import UseDatabase

aurora_creds = {
    'host': '',
    'port': 5432,
    'user': '',
    'password': ''
}

def grab_sensor_uptimes() -> List:
    """Fetch and return all GROW sensor id's and their start and end datetimes"""
    url = 'https://grow.thingful.net/api/entity/timeSeriesInformations/get'
    header = {'Authorization': 'Bearer 8tze34c9qt-7320dcbe17138840d554e4b5fd0c6a0f'}
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

#  [['6dngspdq', '20181017130825', '20181229090408'], ['5tjrqt1c', '20181017131407', '20181017135907'], 
# ['fqzb9jsq', '20181017133111', '20181229094049'], ['mqe06kvv', '20181017132233', '20181017140733'], 
# ['xw97j79a', '20181017130255', '20181017143255'], ['fzja2fbn', '20181017131122', '20181017135622']]

def check_most_recent_data(sensor_id: str, start_date: str, end_date: str) -> str:
    with UseDatabase(aurora_creds) as cursor:
        sql = "SELECT end_date FROM all_sensor_info WHERE sensor_id = %s"
        cursor.execute(sql, (sensor_id,))
        try:
            stored_end_date = cursor.fetchone()[0]
        except TypeError:
            stored_end_date = datetime.datetime.strptime(start_date, '%Y%m%d%H%M%S')
    end_dt = datetime.datetime.strptime(end_date, '%Y%m%d%H%M%S')
    delta = end_dt - stored_end_date
    if delta == datetime.timedelta(0):
        sensor_start_end_intervals = []
    else:
        # do I need to offset the start/end datetimes? Or can the end date be the same as the next start date??
        sensor_start_end_intervals = []
        while delta > datetime.timedelta(0):
            interval = []
            start = stored_end_date 
            end = start + datetime.timedelta(days=10)
            interval.append(start)
            interval.append(end)
            sensor_start_end_intervals.append(interval)
            if delta > datetime.timedelta(days=10):
                stored_end_date = stored_end_date + datetime.timedelta(days=10)
            else:
                stored_end_date = end_dt
            delta = delta - datetime.timedelta(days=10)
    return sensor_start_end_intervals





        





