#! /usr/bin/env python3

import requests
import json
import datetime
from typing import List
from use_postgres import UseDatabase

db_creds = {'host': '',
            'user': '',
            'database': ''}

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

#  [['6dngspdq', '20181017130825', '20181229090408'], ['5tjrqt1c', '20181017131407', '20181017135907'], 
# ['fqzb9jsq', '20181017133111', '20181229094049'], ['mqe06kvv', '20181017132233', '20181017140733'], 
# ['xw97j79a', '20181017130255', '20181017143255'], ['fzja2fbn', '20181017131122', '20181017135622']]

def check_most_recent_grow_data(sensor_id: str, start_date: str, end_date: str) -> str:
    with UseDatabase(aurora_creds) as cursor:
        sql = "SELECT end_date FROM all_sensor_info WHERE sensor_id = %s"
        cursor.execute(sql, (sensor_id,))
        try:
            stored_end_date = cursor.fetchone()[0]
        except TypeError:
            # if there is no end date already stored, use the grow sensor start date 
            stored_end_date = datetime.datetime.strptime(start_date, '%Y%m%d%H%M%S')
    end_dt = datetime.datetime.strptime(end_date, '%Y%m%d%H%M%S')
    delta = end_dt - stored_end_date
    print(delta)
    if delta == datetime.timedelta(0):
        # if the stored end date and end date are the same, no updates need to be made
        sensor_start_end_intervals = []
    else:
        # do I need to offset the start/end datetimes? Or can the end date be the same as the next start date??
        sensor_start_end_intervals = []
        while delta > datetime.timedelta(0):
            interval = []
            start = stored_end_date 
            end = start + datetime.timedelta(days=10)
            interval.append(start.strftime('%Y%m%d%H%M%S'))
            interval.append(end.strftime('%Y%m%d%H%M%S'))
            sensor_start_end_intervals.append(interval)
            if delta > datetime.timedelta(days=10):
                stored_end_date = stored_end_date + datetime.timedelta(days=10)
            else:
                stored_end_date = end_dt
            delta = delta - datetime.timedelta(days=10)
    return sensor_id, sensor_start_end_intervals

def grab_and_insert_grow_data(sensor_id: str, sensor_start_end_intervals: List) -> None:
    """Query specific grow sensor for each interval in sensor_start_end_intervals list. 
    Insert grow data to AWS Aurora data store."""
    header = {'Authorization': ''}
    url = 'https://grow.thingful.net/api/timeSeries/get'
    with UseDatabase(db_creds) as cursor:
        for datetime_interval in sensor_start_end_intervals:
            payload = {'Readers': [{'DataSourceCode': 'Thingful.Connectors.GROWSensors',
                                    'Settings': 
                                        {'LocationCodes': [sensor_id], # 02krq5q5
                                        'VariableCodes': ['Thingful.Connectors.GROWSensors.light',
                                                        'Thingful.Connectors.GROWSensors.air_temperature',
                                                        'Thingful.Connectors.GROWSensors.calibrated_soil_moisture'],
                                        'StartDate': datetime_interval[0], # 20181028200000
                                        'EndDate': datetime_interval[1]
                                    }}]}
            response = requests.post(url, headers=header, json=payload)
            json_object = response.json()
            soil_moisture = []
            light = []
            air_temperature = []
            for i in json_object['Data']:
                if i['VariableCode'].endswith('soil_moisture'):
                    for reading in i['Data']:
                        indiv_reading = []
                        datetime = reading['DateTime']
                        edit_datetime = datetime[:8] + 'T' + datetime[8:]
                        indiv_reading.append(edit_datetime)
                        indiv_reading.append(reading['Value'])
                        soil_moisture.append(indiv_reading)
                elif i['VariableCode'].endswith('light'):
                    for reading in i['Data']:
                        indiv_reading = []
                        datetime = reading['DateTime']
                        edit_datetime = datetime[:8] + 'T' + datetime[8:]
                        indiv_reading.append(edit_datetime)
                        indiv_reading.append(reading['Value'])
                        light.append(indiv_reading)
                elif i['VariableCode'].endswith('temperature'):
                    for reading in i['Data']:
                        indiv_reading = []
                        datetime = reading['DateTime']
                        edit_datetime = datetime[:8] + 'T' + datetime[8:]
                        indiv_reading.append(edit_datetime)
                        indiv_reading.append(reading['Value'])
                        air_temperature.append(indiv_reading)
    with UseDatabase(db_creds) as cursor:
        sql_create = """CREATE TABLE IF NOT EXISTS grow_data(
                        sensor_id varchar(8),
                        datetime timestamp, 
                        soil_moisture numeric, 
                        light numeric, 
                        air_temperature numeric
                        );"""
        cursor.execute(sql_create)
        for a, b, c in zip(soil_moisture, light, air_temperature):
            cursor.execute("""INSERT INTO grow_data
                            VALUES(%s, %s, %s, %s, %s)""",
                            (sensor_id, a[0], a[1], b[1], c[1]))





        





