#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify
from use_postgres import UseDatabase
from psycopg2 import sql

app = Flask(__name__)

aurora_creds = {
        'host': 'grow-data-instance-1.cynbkpreeybn.eu-west-1.rds.amazonaws.com',
        'port': 5432,
        'dbname': 'postgres',
        'user': 'grow_user',
        'password': 'ILoveGROW'
    }

@app.route('/login')
def login() -> 'html':
    with UseDatabase(aurora_creds) as cursor:
        sql_select_sensors = """SELECT COUNT(tablename) 
                        FROM pg_tables
                        WHERE tablename LIKE ('grow_data_%');"""
        cursor.execute(sql_select_sensors)
        sensors = cursor.fetchone()[0]
        sql_select_owners = """SELECT COUNT(DISTINCT(owner_id)) 
                                FROM all_sensor_info;"""
        cursor.execute(sql_select_owners)
        owners = cursor.fetchone()[0]

    return render_template('login.html', number_sensors=sensors,
                            number_owners=owners)

@app.route('/all_grow_map')
def all_grow_map() -> 'html':
    with UseDatabase(aurora_creds) as cursor:
        sql_select_sensors = """SELECT COUNT(tablename) 
                        FROM pg_tables
                        WHERE tablename LIKE ('grow_data_%');"""
        cursor.execute(sql_select_sensors)
        total_sensors = cursor.fetchone()[0]
        sql_select_healthy = """SELECT count(*)
                        FROM all_sensor_info 
                        WHERE sensor_id NOT IN 
                            (SELECT SUBSTRING(grow_table, 11, 8) 
					        FROM grow_anomalies);"""
        cursor.execute(sql_select_healthy)
        healthy_sensors = cursor.fetchone()[0]
        sql_select_recovered = """SELECT count(*)
                        FROM all_sensor_info 
                        WHERE sensor_id IN 
                            (SELECT SUBSTRING(grow_table, 11, 8) 
					        FROM grow_anomalies
				   	        WHERE days_since_anomaly >= 2);"""
        cursor.execute(sql_select_recovered)
        recovered_sensors = cursor.fetchone()[0]
        sql_select_faulty = """SELECT count(*)
                        FROM all_sensor_info 
                        WHERE sensor_id IN 
                            (SELECT SUBSTRING(grow_table, 11, 8) 
					        FROM grow_anomalies
				   	        WHERE days_since_anomaly < 2);"""
        cursor.execute(sql_select_faulty)
        faulty_sensors = cursor.fetchone()[0]
    return render_template('new_grow_map.html', healthy_sensors=healthy_sensors,
                            recovered_sensors=recovered_sensors, faulty_sensors=faulty_sensors,
                            number_sensors=total_sensors)

@app.route('/owner_map')
def owner_map() -> 'html':
    return render_template('owner_map.html')

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    with UseDatabase(aurora_creds) as cursor:
        search = request.args.get('q')
        search_str = f'%{search}%'
        sql_select = sql.SQL("""SELECT address 
                                FROM all_sensor_info
                                WHERE address LIKE {}""").format(sql.Literal(search_str))
        cursor.execute(sql_select)
        results = [i[0] for i in cursor.fetchall()]
        return jsonify(matching_results=results)

@app.route('/grow_by_address')
def grow_by_address() -> 'JSON':
    with UseDatabase(aurora_creds) as cursor:
        address = request.args.get('address')
        resp_list = []
        sql_select = sql.SQL("""SELECT row_to_json(all_sensor_info)
                FROM all_sensor_info
                WHERE address = {};""").format(sql.Literal(address))
        cursor.execute(sql_select)
        response = cursor.fetchall()
        for i in response:
            resp_list.append(i[0])
    return jsonify(resp_list)

@app.route('/grow_by_owner')
def grow_by_owner() -> 'JSON':
    with UseDatabase(aurora_creds) as cursor:
        owner = request.args.get('owner_id')
        resp_list = []
        sql_select = sql.SQL("""SELECT row_to_json(all_sensor_info)
                FROM all_sensor_info
                WHERE owner_id = {};""").format(sql.Literal(owner))
        cursor.execute(sql_select)
        response = cursor.fetchall()
        for i in response:
            resp_list.append(i[0])
    return jsonify(resp_list)

@app.route('/owner_stats')
def owner_stats() -> 'DataTable':
    with UseDatabase(aurora_creds) as cursor:
        owner = request.args.get('owner_id')
        sql_healthy = sql.SQL("""SELECT sensor_id
                            FROM all_sensor_info 
                            WHERE sensor_id NOT IN 
                                (SELECT SUBSTRING(grow_table, 11, 8) 
					            FROM grow_anomalies)
                            AND sensor_id IN
                                (SELECT sensor_id
                                FROM all_sensor_info
                                WHERE owner_id = {});""").format(sql.Literal(owner))
        cursor.execute(sql_healthy)
        healthy_sensors = [x[0] for x in cursor.fetchall()]
        sql_recovered = sql.SQL("""SELECT sensor_id
                            FROM all_sensor_info 
                            WHERE sensor_id IN 
                                (SELECT SUBSTRING(grow_table, 11, 8) 
					            FROM grow_anomalies
				   	            WHERE days_since_anomaly >= 2)
                            AND sensor_id IN
                                (SELECT sensor_id
                                FROM all_sensor_info
                                WHERE owner_id = {});""").format(sql.Literal(owner))
        cursor.execute(sql_recovered)
        recovered_sensors = [x[0] for x in cursor.fetchall()]
        sql_faulty = sql.SQL("""SELECT sensor_id
                            FROM all_sensor_info 
                            WHERE sensor_id IN 
                                (SELECT SUBSTRING(grow_table, 11, 8) 
					            FROM grow_anomalies
				   	            WHERE days_since_anomaly < 2)
                            AND sensor_id IN
                                (SELECT sensor_id
                                FROM all_sensor_info
                                WHERE owner_id = {});""").format(sql.Literal(owner))
        cursor.execute(sql_faulty)
        faulty_sensors= [x[0] for x in cursor.fetchall()]
        sensor_dict = dict()
        sensor_dict['owner_id'] = owner
        sensor_dict['healthy'] = healthy_sensors
        sensor_dict['recovered'] = recovered_sensors
        sensor_dict['faulty'] = faulty_sensors
        print(jsonify(sensor_dict))
    return jsonify(sensor_dict)

@app.route('/healthy_stats')
def healthy_stats() -> 'JSON':
    with UseDatabase(aurora_creds) as cursor:
        # healthy_sensors = request.args.get('healthy_sensors')
        # print(healthy_sensors)
        owner = request.args.get('owner_id')
        sql_healthy = sql.SQL("""SELECT sensor_id
                            FROM all_sensor_info 
                            WHERE sensor_id NOT IN 
                                (SELECT SUBSTRING(grow_table, 11, 8) 
					            FROM grow_anomalies)
                            AND sensor_id IN
                                (SELECT sensor_id
                                FROM all_sensor_info
                                WHERE owner_id = {});""").format(sql.Literal(owner))
        cursor.execute(sql_healthy)
        healthy_sensors = [x[0] for x in cursor.fetchall()]
        healthy_data = []
        for i in healthy_sensors:
            sql_select = sql.SQL("""SELECT sensor_id, 
                                    battery_level, 
                                    soil_moisture, 
                                    light, 
                                    air_temperature, 
                                    datetime
                                    FROM {}
                                    WHERE datetime = (SELECT MAX(datetime)
                                        FROM {})""").format(sql.Identifier(f'grow_data_{i}'),
                                        sql.Identifier(f'grow_data_{i}'))
            cursor.execute(sql_select)
            results = cursor.fetchall()
            healthy_data.append(results)
    return jsonify(healthy_data)
            
        

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
