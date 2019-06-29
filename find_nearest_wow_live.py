#!/usr/bin/env python3

import json
import requests
from typing import List
from math import cos, asin, sqrt
from use_postgres import UseDatabase

db_creds = {'host': 'localhost',
            'user': 'anthonydelivanis',
            'database': 'anthonydelivanis'}

def distance(lat1: int, lon1: int, lat2: int, lon2: int) -> int:
    """Use Haversine formula to compute distance between lat/lon coordinates"""
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 12742 * asin(sqrt(a))

def closest(data: List, v: List) -> List:
    """Finds the closest lat/lon coords near v"""
    return min(data, key=lambda p: distance(v[1],v[2],p[1],p[2]))

def close_distance(data: List) -> List:
    """Returns the distance between GROW and WOW"""
    for i in data:
        dist = distance(i[1], i[2], i[3][1], i[3][2])
        i.append(dist)
    return data 

def grab_grow_ids() -> List:
    """Grabs distinct sensor ids and coordinates from grow location api"""
    url = 'https://grow.thingful.net/api/entity/locations/get'
    header = {'Authorization': 'Bearer 8tze34c9qt-7320dcbe17138840d554e4b5fd0c6a0f'}
    payload = {'DataSourceCodes': ['Thingful.Connectors.GROWSensors']}
    response = requests.post(url, headers=header, json=payload)
    json_object = response.json()
    grow_current_sensors = []
    for i in json_object['Locations']:
        sensor_id = json_object['Locations'][i]['Code']
        if sensor_id not in grow_current_sensors:
            lat = json_object['Locations'][i]['Y']
            lon = json_object['Locations'][i]['X']
            grow_current_sensors.append([sensor_id, lat, lon])
    return grow_current_sensors
#  [['005qg039', 38.1090933333333, -8.58671], ['005ssbsd', 0, 0], ['00vshs16', 48.0816172603591, 20.764303520279]]

def grab_wow_ids_and_coords() -> List:
    """Grabs WOW site ids and location coordinates from static file"""
    with open('wow_api/wow_observations_europe.json', 'r') as reader:
        json_object = json.load(reader)
        wow_site_list = []
        for i in range(len(json_object['Object'])):
            try:
                if json_object['Object'][i]['RainfallAmount_Millimetre'] is not None:
                    site_id = json_object['Object'][i]['SiteId']
                    lat = json_object['Object'][i]['Latitude']
                    lon = json_object['Object'][i]['Longitude']
                    wow_site_list.append([site_id, lat, lon])
            except KeyError:
                pass
    return wow_site_list
# [['904966001', 52.256439, 20.565886], ['535dc74d-f949-e611-9401-0003ff59b0cc', 45.722650112859, 0.62060626745222]]

def find_nearest_wow(grow_current_sensors: List, wow_site_list: List) -> List:
    """For each grow sensor, find the nearest WOW observation site"""
    for i in range(len(grow_current_sensors)):
        closest_wow = closest(wow_site_list, grow_current_sensors[i])
        grow_current_sensors[i].append(closest_wow)
    return grow_current_sensors
        # ValueError: too many values to unpack (expected 2)
        # closest_wow, distance = closest(wow_site_list, grow_current_sensors[i])
        # grow_current_sensors[i].append([closest_wow, distance])

        # works 
        
# [['005qg039', 38.1090933333333, -8.58671, ['2ce01a20-fc29-e911-9461-0003ff596eab', 38.532, -9.012]], 
# ['005ssbsd', 0, 0, ['c1d3cfdd-4829-e911-9462-0003ff59610a', 36.70756531, 3.1598618]], 
# ['00vshs16', 48.0816172603591, 20.764303520279, ['3ac29743-01ce-e811-a8ec-0003ff59b2da', 47.3089, 19.8311]]]



def insert_to_db(grow_current_sensors: List) -> None:
    """Insert the grow/WOW sensor/station mappings to local Postgres"""
    with UseDatabase(db_creds) as cursor:
        for i in grow_current_sensors:
            cursor.execute("""INSERT INTO grow_to_wow_mapping_0625
                            VALUES(%s, %s, %s, %s, %s, %s, %s)""",
                            (i[0], i[1], i[2], i[3][0], i[3][1], i[3][2], i[4]))

if __name__ == '__main__':
    grow_sensor_ids = grab_grow_ids()
    wow_site_list = grab_wow_ids_and_coords()
    sensor_site_mappings = find_nearest_wow(grow_sensor_ids, wow_site_list)
    mappings_and_distance = close_distance(sensor_site_mappings)
    insert_to_db(mappings_and_distance)
