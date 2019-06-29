#!/usr/bin/env python3

import requests
from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request, Response
from use_postgres import UseDatabase

app = Flask(__name__)
CORS(app)
# cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
db_creds = {
    'host': '',
    'user': '',
    'database': ''
}

@app.route('/api/all_grow')
def fetch_all_grow_info() -> 'JSON':
    with UseDatabase(db_creds) as cursor:
        SQL = """SELECT * FROM all_sensors_0618 limit 20;"""
        cursor.execute(SQL)
        response = cursor.fetchall()
    return jsonify(response)

@app.route('/api/all_grow_true_json')
def fetch_all_json() -> 'JSON':
    with UseDatabase(db_creds) as cursor:
        resp_list = []
        SQL = """SELECT row_to_json(all_sensors_0625)
                FROM all_sensors_0625;"""
        cursor.execute(SQL)
        response = cursor.fetchall()
        for i in response:
            resp_list.append(i[0])
    return jsonify(resp_list)

@app.route('/api/indiv_grow_data')
@cross_origin()
def get_me_grow() -> 'JSON': 
    start = request.args.get('start', None)
    start = start.replace('-','').replace('T','').replace(':','')
    end = request.args.get('end', None)
    end = end.replace('-','').replace('T','').replace(':','')
    sensor_id = request.args.get('sensor_id', None)
    header = {'Authorization': ''}
    url = 'https://grow.thingful.net/api/timeSeries/get'
    payload = {'Readers': [{'DataSourceCode': 'Thingful.Connectors.GROWSensors',
                            'Settings': 
                                {'LocationCodes': [sensor_id], # 02krq5q5
                                'VariableCodes': ['Thingful.Connectors.GROWSensors.light',
                                                'Thingful.Connectors.GROWSensors.air_temperature',
                                                'Thingful.Connectors.GROWSensors.calibrated_soil_moisture'],
                                'StartDate': start, # 20181028200000
                                'EndDate': end }}]}
    response = requests.post(url, headers=header, json=payload)
    return response.content

@app.route('/api/get_wow_data')
def get_me_wow() -> 'JSON':
    sensor_id = request.args.get('sensor_id', None)
    start = request.args.get('start', None)
    end = request.args.get('end', None)
    wow_site_id, distance = match_wow_site(sensor_id)
    header = {'Ocp-Apim-Subscription-Key': ''}
    url = 'https://apimgmt.www.wow.metoffice.gov.uk/api/observations/byversion'
    payload = {'site_id': wow_site_id,
            'start_time': start, # 2019-05-24T20:00:00
            'end_time': end}
    response = requests.get(url, headers=header, params=payload)
    json_object = response.json()
    data_dict = dict()
    data_dict['distance'] = []
    data_dict['datetime'] = []
    data_dict['air_temp'] = []
    data_dict['rainfall'] = []
    # data_dict['soil_moisture'] = []
    for i in json_object['Object']:
        data_dict['air_temp'].append(i['DryBulbTemperature_Celsius'])
        data_dict['rainfall'].append(i['RainfallAmount_Millimetre'])
        data_dict['datetime'].append(i['ReportEndDateTime'])
    data_dict['distance'].append(distance)
    return jsonify(data_dict)

@app.route('/api/match_grow_to_wow')
def match_closest_wow() -> str:
    sensor_id = request.args.get('sensor_id', None)
    wow_site, _ = match_wow_site(sensor_id)
    return wow_site

def match_wow_site(sensor_id: str) -> str:
    """Find closest WOW site to select grow sensor"""
    with UseDatabase(db_creds) as cursor:
        cursor.execute("""SELECT site_id, distance
                            FROM grow_to_wow_mapping_0625
                            WHERE sensor_id = %s;""", (sensor_id,))
        site_id = cursor.fetchone() # ('c1d3cfdd-4829-e911-9462-0003ff59610a',)
        # site_id = cursor.fetchall() # [('c1d3cfdd-4829-e911-9462-0003ff59610a',)]
    return site_id 



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)