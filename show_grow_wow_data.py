#!/usr/bin/env python3

# Query GROW and WOW and show results on matplotlib graphs

import json
import argparse
import requests
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List
from use_postgres import UseDatabase

db_creds = {
    'host': '',
    'user': '',
    'database': ''
}

def query_grow_data(sensor_id: str, start: str, end: str) -> List:
    """Query GROW API for temperature, soil moisture, light"""
    start_date = start.replace('T', '') # creates an additional string, tbd if that's ok
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
        data_dict[attribute_name] = dict()
        data_dict[attribute_name]['Datetime'] = []
        data_dict[attribute_name]['Value'] = []
        for k in i['Data']:
            data_dict[attribute_name]['Datetime'].append(k['DateTime'])
            data_dict[attribute_name]['Value'].append(k['Value'])
    return data_dict

def graph_me_up(data: dict) -> 'Matplotlib Graph':
    """Graph the three extracted GROW attributes"""
    datetimes = [pd.to_datetime(x) for x in data[list(data.keys())[0]]['Datetime']]
    y1 = np.array([x for x in data[list(data.keys())[0]]['Value']])
    y2 = np.array([x for x in data[list(data.keys())[1]]['Value']])
    y3 = np.array([x for x in data[list(data.keys())[2]]['Value']])
    # plt.plot(datetimes, y1, 'r', label=list(data)[0] + ' %')
    # plt.plot(datetimes, y2, 'g', label=list(data)[1] + ' mol/m2/d')
    # plt.plot(datetimes, y3, 'b', label=list(data)[2] + ' C')
    # plt.plot_date(datetimes, y1, color='r')
    # plt.plot_date(datetimes, y2, color='g')
    # plt.plot_date(datetimes, y3, color='b')
    # plt.xticks(rotation='vertical', fontsize = 8)
    # plt.legend()
    return datetimes, y1, y2, y3
    # plt.show()

def match_wow_site(sensor_id: str) -> str:
    """Find closest WOW site to select grow sensor"""
    with UseDatabase(db_creds) as cursor:
        cursor.execute("""SELECT site_id 
                            FROM grow_to_wow_mapping_0625
                            WHERE sensor_id = %s;""", (sensor_id,))
        site_id = cursor.fetchone() # ('c1d3cfdd-4829-e911-9462-0003ff59610a',)
        # site_id = cursor.fetchall() # [('c1d3cfdd-4829-e911-9462-0003ff59610a',)]
    return site_id 

def query_wow_data(site_id: str, start: str, end: str) -> 'plot':
    """Query WOW API for temperature, rainfall, humidity"""
    start = dt.datetime.strptime(start, '%Y%m%dT%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
    end = dt.datetime.strptime(end, '%Y%m%dT%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
    header = {'Ocp-Apim-Subscription-Key': ''}
    url = 'https://apimgmt.www.wow.metoffice.gov.uk/api/observations/byversion'
    payload = {'site_id': site_id[0],
            'start_time': start, # 2019-05-24T20:00:00
            'end_time': end}
    response = requests.get(url, headers=header, params=payload)
    json_object = response.json()
    return json_object

def extract_wow_data(json_object: dict) -> dict:
    """Extract air temp and rainfall amount from wow json object"""
    data_dict = dict()
    data_dict['datetime'] = []
    data_dict['air_temp'] = []
    data_dict['rainfall'] = []
    # data_dict['soil_moisture'] = []
    for i in json_object['Object']:
        data_dict['air_temp'].append(i['DryBulbTemperature_Celsius'])
        data_dict['rainfall'].append(i['RainfallAmount_Millimetre'])
        data_dict['datetime'].append(i['ReportEndDateTime'])
        # data_dict['soil_moisture'].append(i['SoilMoisture_Percent'])
    return data_dict

def turn_up_for_graphs(data: dict) -> 'Matplotlib Graph':
    """Graph the extracted WOW data"""
    datetimes = [pd.to_datetime(x) for x in data['datetime']]
    y1 = [x for x in data['air_temp']]
    y2 = [x for x in data['rainfall']]
    # y3 = [x for x in data['soil_moisture']]
    # plt.plot(datetimes, y1, 'r', label='Air Temperature C')
    # plt.plot(datetimes, y2, 'g', label='Rainfall in Mm')
    # plt.plot(datetimes, y3, 'b', label='Soil Moisture %')
    # plt.xticks(rotation='vertical', fontsize = 8)
    # plt.legend()
    return datetimes, y1, y2
    # plt.show()

def plot_both_graphs(datetimes, y1, y2, y3, datetimes2, y4, y5) -> 'Two Matplotlib Graphs':
    plt.figure(1)
    plt.plot(datetimes, y1, 'r', label='Soil Moisture %')
    plt.plot(datetimes, y2, 'g', label='Light mol/m2/d')
    plt.plot(datetimes, y3, 'b', label='Air Temperature C')
    plt.xticks(rotation='vertical', fontsize = 8)
    plt.title('GROW Data')
    plt.legend()
    plt.figure(2)
    plt.plot(datetimes2, y4, 'b', label='Air Temperature C')
    plt.plot(datetimes2, y5, 'g', label='Rainfall in Mm')
    # plt.plot(datetimes2, y6, 'b', label='Soil Moisture %')
    plt.xticks(rotation='vertical', fontsize = 8)
    plt.title('WOW Data')
    plt.legend()
    plt.show()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sensor_id')
    parser.add_argument('start')
    parser.add_argument('end')
    args = parser.parse_args()

    grow_json_object = query_grow_data(args.sensor_id, args.start, args.end)
    grow_data_dict = extract_grow_data(grow_json_object)
    datetimes, y1, y2, y3 = graph_me_up(grow_data_dict)

    wow_site = match_wow_site(args.sensor_id)
    wow_json_object = query_wow_data(wow_site, args.start, args.end)
    wow_data_dict = extract_wow_data(wow_json_object)
    datetimes2, y4, y5 = turn_up_for_graphs(wow_data_dict)
    plot_both_graphs(datetimes, y1, y2, y3, datetimes2, y4, y5)

    # ssah0hsp 20190501T080000 20190510T080000
    # 3t02tc74 20190530T220000 20190603T220000
    # h1z13w03 20190510T220000 20190513T220000
    # h1z13w03 20190410T220000 20190418T220000
    # pnf75wwa 20190516T220000 20190522T220000
    # epfffpth 20190601T133540 20190605T133540
    # p10r55vj 2019-03-18T19:47:03 2019-03-20T19:47:03

    # m65ex1jn returns bad grow data?
    # kw1kdkvt returns bad grow data



    # plot2 = turn_up_for_graphs(wow_data_dict)
    # plt.figure(1)
    # plt.plot(plot1)
    # plt.figure(2)
    # plt.plot(plot2)
    # plt.show()



    