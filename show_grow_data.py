#!/usr/bin/env python3

import json
import argparse
import requests
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List

def query_grow_data(sensor_id: str, start: str, end: str) -> List:
    """Query GROW API for temperature, soil moisture, light"""
    start_date = start.replace('T', '')
    end_date = end.replace('T', '')
    header = {'Authorization': ''}
    url = 'https://grow.thingful.net/api/timeSeries/get'
    payload = {'Readers': [{'DataSourceCode': 'Thingful.Connectors.GROWSensors',
                            'Settings': 
                                {'LocationCodes': [sensor_id], # 02krq5q5
                                'VariableCodes': ['Thingful.Connectors.GROWSensors.light',
                                                'Thingful.Connectors.GROWSensors.air_temperature',
                                                'Thingful.Connectors.GROWSensors.calibrated_soil_moisture'],
                                'StartDate': start_date, # 20181028200000
                                'EndDate': end_date 
                                }
                            }]
                }
    response = requests.post(url, headers=header, json=payload)
    json_object = response.json()
    return json_object

def extract_grow_data(json_object: dict) -> dict:
    """Extract data values, datetimes, and attribute name from GROW data json object"""
    data_dict = dict()
    for i in json_object['Data']:
        attribute_name = i['VariableCode'].replace('Thingful.Connectors.GROWSensors.','')
        data_dict[attribute_name] = {}
        data_dict[attribute_name]['Datetime'] = []
        data_dict[attribute_name]['Value'] = []
        # if attribute_name == 'calibrated_soil_moisture':


        for k in i['Data']:
            data_dict[attribute_name]['Datetime'].append(k['DateTime'])
            data_dict[attribute_name]['Value'].append(k['Value'])
    return data_dict

def graph_me_up(data: dict) -> 'Matplotlib Graph':
    """Graph the three extracted GROW attributes"""
    datetimes = [pd.to_datetime(x) for x in data[list(data.keys())[0]]['Datetime']]
    y1 = np.array([x for x in data['calibrated_soil_moisture']['Value']])
    y2 = np.array([x for x in data['air_temperature']['Value']])
    y3 = np.array([x for x in data['light']['Value']])

    # assums ordered dict, not good
    # y1 = np.array([x for x in data[list(data.keys())[0]]['Value']])
    # y2 = np.array([x for x in data[list(data.keys())[1]]['Value']])
    # y3 = np.array([x for x in data[list(data.keys())[2]]['Value']])
    plt.plot(datetimes, y1, 'r', label='calibrated_soil_moisture' + ' %')
    plt.plot(datetimes, y2, 'g', label='air_temperature' + ' C')
    plt.plot(datetimes, y3, 'b', label='light' + ' mol/m2/d')
    # plt.plot_date(datetimes, y1, color='r')
    # plt.plot_date(datetimes, y2, color='g')
    # plt.plot_date(datetimes, y3, color='b')
    plt.xticks(rotation='vertical', fontsize = 8)
    plt.legend()
    plt.show()




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sensor_id')
    parser.add_argument('start')
    parser.add_argument('end')
    args = parser.parse_args()

    json_object = query_grow_data(args.sensor_id, args.start, args.end)
    data_dict = extract_grow_data(json_object)
    graph_me_up(data_dict)