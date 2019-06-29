#!/usr/bin/env python3

import argparse
import requests
from pprint import pprint

def grab_observations(sensor_id, variable, start, end):
    url = 'https://grow.thingful.net/api/timeSeries/get'
    header = {'Authorization': 'Bearer 8tze34c9qt-7320dcbe17138840d554e4b5fd0c6a0f'}
    payload2 = {'Readers': [{'DataSourceCode': 'Thingful.Connectors.GROWSensors',
                            'Settings': {'LocationCodes': ['6dngspdq'], 
                                    'VariableCodes': ['Thingful.Connectors.GROWSensors.light'],
                                    'StartDate': '20181229090408', 
                                    'EndDate': '20190104072755'
                                    }}]}
    payload2['Readers'][0]['Settings']['LocationCodes'] = [sensor_id]
    payload2['Readers'][0]['Settings']['VariableCodes'] = ['Thingful.Connectors.GROWSensors.' + variable]
    payload2['Readers'][0]['Settings']['StartDate'] = start
    payload2['Readers'][0]['Settings']['EndDate'] = end 
    response = requests.post(url, headers=header, json=payload2)
    print(response.url)
    print(payload2)
    pprint(response.json())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sensor_id')
    parser.add_argument('variable')
    parser.add_argument('start')
    parser.add_argument('end')
    args = parser.parse_args()
    grab_observations(args.sensor_id, args.variable, 
                    args.start, args.end)



    