#!/usr/bin/env python3

import json
from use_postgres import UseDatabase

db_creds = {'host': '',
            'user': '',
            'database': ''}

# 1 variable extraction
with open('sensor_data_4.json', 'r') as reader:
    sensor_readings = []
    json_object = json.load(reader)
    for i in json_object['Data'][0]['Data']:
        indiv_reading = []
        datetime = i['DateTime']
        edit_datetime = datetime[:8] + 'T' + datetime[8:] # add T for Postgres timestamp format
        indiv_reading.append(json_object['Data'][0]['LocationCode'])
        indiv_reading.append(edit_datetime)
        indiv_reading.append(i['Value'])
        sensor_readings.append(indiv_reading)



# 3 variable extraction, combines variables into one list
#  sensor_id |      datetime       | soil_moisture | light | air_temp
# -----------+---------------------+---------------+-------+----------
#  02krq5q5  | 2018-11-05 23:51:25 |         39.01 |   0.1 |    10.31
# this only works if soil_moisture is the first data variable returned
# when querying timeSeries/get endpoint

with open('sample_3_variable_data.json') as reader:
    json_object = json.load(reader)
    sensor_readings = []
    for i in json_object['Data']:
        if i['VariableCode'].endswith('soil_moisture'):
            for reading in i['Data']:
                datetime = reading['DateTime']
                edit_datetime = datetime[:8] + 'T' + datetime[8:]
                # if sensor_readings == []:
                indiv_reading = []
                indiv_reading.append(json_object['Data'][0]['LocationCode'])
                indiv_reading.append(edit_datetime)
                indiv_reading.append('calibrated_soil_moisture')
                indiv_reading.append(reading['Value'])
                sensor_readings.append(indiv_reading)
                # else:
                #     for a in sensor_readings:
                #         if a[0] == json_object['Data'][0]['LocationCode'] and a[1] == edit_datetime:
                #             a.append('calibrated_soil_moisture')
                #             a.append(reading['Value'])
        elif i['VariableCode'].endswith('light'):
            for reading in i['Data']:
                datetime = reading['DateTime']
                edit_datetime = datetime[:8] + 'T' + datetime[8:]
                if sensor_readings == []:
                    indiv_reading = []
                    indiv_reading.append(json_object['Data'][0]['LocationCode'])
                    indiv_reading.append(edit_datetime)
                    indiv_reading.append('light')
                    indiv_reading.append(reading['Value'])
                    sensor_readings.append(indiv_reading)
                else:
                    for a in sensor_readings:
                        if a[0] == json_object['Data'][0]['LocationCode'] and a[1] == edit_datetime:
                            a.append('light')
                            a.append(reading['Value'])
        elif i['VariableCode'].endswith('temperature'):
            for reading in i['Data']:
                datetime = reading['DateTime']
                edit_datetime = datetime[:8] + 'T' + datetime[8:]
                if sensor_readings == []:
                    indiv_reading = []
                    indiv_reading.append(json_object['Data'][0]['LocationCode'])
                    indiv_reading.append(edit_datetime)
                    indiv_reading.append('temperature')
                    indiv_reading.append(reading['Value'])
                    sensor_readings.append(indiv_reading)
                else:
                    for a in sensor_readings:
                        if a[0] == json_object['Data'][0]['LocationCode'] and a[1] == edit_datetime:
                            a.append('temperature')
                            a.append(reading['Value'])
                
        elif i['VariableCode'].endswith('temperature'):
            indiv_reading = []
            datetime = reading['DateTime']
            edit_datetime = datetime[:8] + 'T' + datetime[8:]
            indiv_reading.append(json_object['Data'][0]['LocationCode'])
            indiv_reading.append(edit_datetime)
            indiv_reading.append('air_temperature')
            indiv_reading.append(reading['Value'])
            sensor_readings.append(indiv_reading)

with UseDatabase(db_creds) as cursor:
    for i in sensor_readings:
        cursor.execute("""INSERT INTO combined_variables
                        VALUES(%s, %s, %s, %s, %s)""", 
                        (i[0], i[1], i[3], i[5], i[7]))







# extracts three variables, but they exist in a list separately 
#  sensor_id |      datetime       | soil_moisture | light | air_temp
# -----------+---------------------+---------------+-------+----------
#  02krq5q5  | 2018-11-05 23:51:25 |         39.01 |       |
#  02krq5q5  | 2018-11-05 23:51:25 |               |   0.1 |
#  02krq5q5  | 2018-11-05 23:51:25 |               |       |    10.31

with open('sample_3_variable_data.json') as reader:
    json_object = json.load(reader)
    sensor_readings = []
    for i in json_object['Data']:
        if i['VariableCode'].endswith('soil_moisture'):
            for reading in i['Data']:
                indiv_reading = []
                datetime = reading['DateTime']
                edit_datetime = datetime[:8] + 'T' + datetime[8:]
                indiv_reading.append(json_object['Data'][0]['LocationCode'])
                indiv_reading.append(edit_datetime)
                indiv_reading.append('calibrated_soil_moisture')
                indiv_reading.append(reading['Value'])
                sensor_readings.append(indiv_reading)
        elif i['VariableCode'].endswith('light'):
            for reading in i['Data']:
                indiv_reading = []
                datetime = reading['DateTime']
                edit_datetime = datetime[:8] + 'T' + datetime[8:]
                indiv_reading.append(json_object['Data'][0]['LocationCode'])
                indiv_reading.append(edit_datetime)
                indiv_reading.append('light')
                indiv_reading.append(reading['Value'])
                sensor_readings.append(indiv_reading)
        elif i['VariableCode'].endswith('temperature'):
            for reading in i['Data']:
                indiv_reading = []
                datetime = reading['DateTime']
                edit_datetime = datetime[:8] + 'T' + datetime[8:]
                indiv_reading.append(json_object['Data'][0]['LocationCode'])
                indiv_reading.append(edit_datetime)
                indiv_reading.append('air_temperature')
                indiv_reading.append(reading['Value'])
                sensor_readings.append(indiv_reading)
        
# combine separate variable list elements into one element
combined_readings = []
for i in sensor_readings:
    if i[1] not in combined_readings:

    

# insert one variable
with UseDatabase(db_creds) as cursor:
    for i in sensor_readings:
        cursor.execute("""INSERT INTO soil_readings
                        VALUES(%s, %s, %s)""", 
                        (i[0], i[1], i[2]))

# insert three variables
with UseDatabase(db_creds) as cursor:
    for i in sensor_readings:
        if i[1].endswith('moisture'):
            cursor.execute("""INSERT INTO three_variables
                        (sensor_id, datetime, soil_moisture)
                        VALUES(%s, %s, %s)""", 
                        (i[0], i[2], i[3]))
        elif i[1].endswith('light'):
            cursor.execute("""INSERT INTO three_variables
                        (sensor_id, datetime, light)
                        VALUES(%s, %s, %s)""", 
                        (i[0], i[2], i[3]))
        elif i[1].endswith('temperature'):
            cursor.execute("""INSERT INTO three_variables
                        (sensor_id, datetime, air_temp)
                        VALUES(%s, %s, %s)""", 
                        (i[0], i[2], i[3]))

