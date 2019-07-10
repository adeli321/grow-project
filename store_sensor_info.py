#!/usr/bin/env python3

import json
import time
import requests
import itertools
import argparse
from use_postgres import UseDatabase
from datetime import datetime
from typing import List

db_creds = {'host': '',
            'user': '',
            'database': ''}

aurora_creds = {
    'host': '',
    'port': 5432,
    'user': '',
    'password': ''
}

def grab_grow_sensors() -> List:
    """Grabs all GROW sensor id's, last upload date, days active"""
    url = 'https://grow.thingful.net/api/entity/timeSeriesInformations/get'
    header = {'Authorization': ''}
    response = requests.post(url, headers=header)
    json_object = response.json()
    current_sensors = []
    sensor_info_list = []
    for i in json_object['TimeSeriesInformations']:
        sensor_id = json_object['TimeSeriesInformations'][i]['LocationIdentifier'][-8:]
        # end_date = json_object['TimeSeriesInformations'][i]['EndDate']
        # if end_date.startswith('20190606'):
        if sensor_id not in current_sensors:
            current_sensors.append(sensor_id)
            sensor_list = []
            start_date = json_object['TimeSeriesInformations'][i]['StartDate']
            end_date = json_object['TimeSeriesInformations'][i]['EndDate']
            start_dt = datetime.strptime(start_date, '%Y%m%d%H%M%S')
            end_dt = datetime.strptime(end_date, '%Y%m%d%H%M%S')
            delta_dt = end_dt - start_dt
            days_active = delta_dt.days # difference in days from start to end dates
            edit_start_date = start_date[:8] + 'T' + start_date[8:] # add T for later insert to Postgres
            edit_end_date = end_date[:8] + 'T' + end_date[8:] # add T for later insert to Postgres
            sensor_list.append(sensor_id)
            # sensor_list.append(edit_end_date)
            sensor_list.append(days_active)
            sensor_list.append(edit_start_date) # added
            sensor_list.append(edit_end_date) # added
            sensor_info_list.append(sensor_list)
    return sensor_info_list

    # Thought I needed this for de-duplication, but that is already taken care of
    # sensor_info_list.sort()
    # sensor_info_unique = list(k for k,_ in itertools.groupby(sensor_info_list)) 
    # return sensor_info_unique

def filter_for_new_sensor_updates(new_sensor_list: List) -> List:
    """Compare sensor info to Postgres table to see if the individual sensor 
    info is already in the table. If not present, keep the sensor info for further 
    processing and eventual insert into Postgres table"""
    with UseDatabase(aurora_creds) as cursor:
        sql_check = """SELECT EXISTS (SELECT 1 FROM pg_tables
                                        WHERE tablename = 'all_sensor_info');"""
        cursor.execute(sql_check)
        response = cursor.fetchone()
        if response[0] == True:
            sql_collect = """SELECT row_to_json(all_sensor_info)
                                FROM all_sensor_info;"""
            cursor.execute(sql_collect)
            all_stored_sensors = cursor.fetchall()
        else:
            all_stored_sensors = []
    stored_sensor_ids = []
    for i in all_stored_sensors:
        stored_sensor_ids.append(i[0]['sensor_id'])
    new_sensor_info = []
    for i in new_sensor_list:
        if i[0] not in stored_sensor_ids:
            new_sensor_info.append(i)
        else:
            for stored_sensor in all_stored_sensors:
                if stored_sensor[0]['sensor_id'] == i[0] and \
                    stored_sensor[0]['end_date'].replace('-','').replace(':','') != i[3]:
                    new_sensor_info.append(i)
    return new_sensor_info, stored_sensor_ids

def lookup_location_coords(sensor_list: List, gcloud_api_key: str) -> List:
    """Find and append location coords, address, owner id to GROW sensor list"""
    url = 'https://grow.thingful.net/api/entity/locations/get'
    header = {'Authorization': ''}
    payload = {'DataSourceCodes': ['Thingful.Connectors.GROWSensors']}
    response = requests.post(url, headers=header, json=payload)
    json_object = response.json()
    for sensor in sensor_list:
        for i in json_object['Locations']:
            if json_object['Locations'][i]['Code'] == sensor[0]:
                lat = json_object['Locations'][i]['Y']
                lon = json_object['Locations'][i]['X']
                owner_id = json_object['Locations'][i]['UserUid']
                full_address = get_address(str(lat) + ',' + str(lon), gcloud_api_key)
                sensor.append(lat)
                sensor.append(lon)
                sensor.append(full_address)
                sensor.append(owner_id)
                time.sleep(0.025)
    return sensor_list

def get_address(latlng: str, api_key: str) -> List:
    """Query Google Geocoding API to reverse geocode latlng to full address"""
    url = 'https://maps.googleapis.com/maps/api/geocode/json' 
    payload = {'latlng': latlng, 'key': api_key} 
    response = requests.get(url, params=payload)
    json_object = response.json()
    full_address = []
    try:
        for i in json_object['results'][0]['address_components']:
            full_address.append(i['long_name'])
    except:
        full_address.append('')
    return ' '.join(full_address)

def insert_to_postgres(sensor_list: List, stored_sensor_ids: List) -> None:
    """Insert sensor list details to local Postgres DB"""
    with UseDatabase(aurora_creds) as cursor:
        sql_create = """CREATE TABLE IF NOT EXISTS all_sensor_info(
                        sensor_id varchar(8),
                        days_active integer, 
                        start_date timestamp, 
                        end_date timestamp, 
                        latitude numeric, 
                        longitude numeric, 
                        address varchar(140), 
                        owner_id varchar(36));"""
        cursor.execute(sql_create)
        for i in sensor_list:
            if i[0] in stored_sensor_ids:
                cursor.execute("""UPDATE all_sensor_info
                            SET days_active = %s,
                            start_date = %s,
                            end_date = %s
                            WHERE sensor_id = %s""",
                            (i[1], i[2], i[3], i[0]))
                            # VALUES(%s, %s, %s, %s, %s, %s, %s, %s)""",
                            # (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7]))
            else:
                cursor.execute("""INSERT INTO all_sensor_info
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s)""",
                            (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7]))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('gcloud_api_key')
    args = parser.parse_args()

    sensor_info = grab_grow_sensors()
    new_sensor_info, stored_sensor_ids = filter_for_new_sensor_updates(sensor_info)
    sensor_list = lookup_location_coords(new_sensor_info, args.gcloud_api_key)
    insert_to_postgres(sensor_list, stored_sensor_ids)


# old manual file lookup code
# with open('grow_sensor_uptime/sensor_uptime_0614.json', 'r') as reader:
#     json_object = json.load(reader)
#     current_sensors = []
#     for i in json_object['TimeSeriesInformations']:
#         sensor_id = json_object['TimeSeriesInformations'][i]['LocationIdentifier'][-8:]
#         end_date = json_object['TimeSeriesInformations'][i]['EndDate']
#         if end_date.startswith('201906'):
#             if sensor_id not in current_sensors:
#                 current_sensors.append(sensor_id)

# Grabs sensors from grow_sensor_locations
# with open('grow_sensor_locations/sensor_locations_0614.json', 'r') as reader:
#     json_object = json.load(reader)
#     current_sensors = []
#     for i in json_object['Locations']:
#         sensor_id = json_object['Locations'][i]['Code']
#         # if end_date.startswith('201906'):
#         if sensor_id not in current_sensors:
#             current_sensors.append(sensor_id)

# Grab total number of sensors from locations.json
# with open('sensor_locations_0530.json', 'r') as reader:
#     json_object = json.load(reader)
#     sensor_count = 0
#     for i in json_object['Locations']:
#         sensor_count += 1

# old manual file lookup code
# Add metadata (uptime, last upload time) to sensor id
# with open('grow_sensor_uptime/sensor_uptime_0614.json', 'r') as reader:
#     json_object = json.load(reader)
#     sensor_info_list = []
#     for i in json_object['TimeSeriesInformations']:
#         sensor_id = json_object['TimeSeriesInformations'][i]['LocationIdentifier'][-8:]
#         if sensor_id in current_sensors:
#             sensor_list = []
#             start_date = json_object['TimeSeriesInformations'][i]['StartDate']
#             end_date = json_object['TimeSeriesInformations'][i]['EndDate']
#             start_dt = datetime.strptime(start_date, '%Y%m%d%H%M%S')
#             end_dt = datetime.strptime(end_date, '%Y%m%d%H%M%S')
#             delta_dt = end_dt - start_dt
#             days_active = delta_dt.days
#             edit_end_date = end_date[:8] + 'T' + end_date[8:]
#             sensor_list.append(sensor_id)
#             sensor_list.append(edit_end_date)
#             sensor_list.append(days_active)
#             sensor_info_list.append(sensor_list)
# # Remove duplicate sensors from list
# sensor_info_list.sort()
# sensor_info_unique = list(k for k,_ in itertools.groupby(sensor_info_list))

# old manual file lookup code
# Look up locations of sensors
# with open('grow_sensor_locations/sensor_locations_0614.json', 'r') as reader:
#     json_object = json.load(reader)
#     for sensor in sensor_info_unique:
#         for i in json_object['Locations']:
#             if json_object['Locations'][i]['Code'] == sensor[0]:
#                 lat = json_object['Locations'][i]['Y']
#                 lon = json_object['Locations'][i]['X']
#                 owner_id = json_object['Locations'][i]['UserUid']
#                 sensor.append(lat)
#                 sensor.append(lon)
#                 sensor.append(owner_id)

# sensor_info_unique is a list of lists containing 6 elements each
# sensor_id, last_upload_datetime, days_active, latitude, longitude, owner_id
# ['020gvfg2', '20190518T164855', 55, 0, 0, 'd9d3997e-299f-4ed7-9744-fca1b1a45b27']
