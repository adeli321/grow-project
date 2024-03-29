// This creates a map that shows (on click) all of the GROW
// sensors located in Europe.
// Once loaded, you can input the sensor id, start date, 
// and end date to return a graph of the GROW variables
// from that sensor.

google.charts.load('current', {'packages':['corechart']});
// google.charts.setOnLoadCallback(getSensorData);
// google.charts.setOnLoadCallback(drawChart);

var activeWindow;

function clearBox(elementID)
{
    document.getElementById(elementID).innerHTML = "";
}

function addInfoWindow(marker, message) {
    // Function to add InfoWindow to map marker
    var infoWindow = new google.maps.InfoWindow({
        content: message
    });

    google.maps.event.addListener(marker, 'click', function() {
        // Close active window if exists
        if (activeWindow != null) {
            activeWindow.close();
        }
        // Open new window 
        infoWindow.open(map, marker); 
        // Store new window in global variable 
        activeWindow = infoWindow; 
    });

    google.maps.event.addListener(marker, 'click', function() {
        // Clear all values in input boxes
        document.getElementById('end_date').value = '';
        document.getElementById('start_date').value = '';
        document.getElementById('sensor_id').value = '';
        // Match end date & insert to input box
        var reg = /End Date\: (.*)<br>Sensor Id/;
        var end = reg.exec(message)[1];
        document.getElementById('end_date').value += end;
        // Match start date & insert to input box
        // Start date is the GROW start date, unless
        // the range is larger than 9 days, 
        // then the start date = end date minus 9 days.
        var start_reg = /Start Date\: (.*)<br>End Date/;
        var start = start_reg.exec(message)[1];
        var start_date = new Date(start);
        var end_date = new Date(end);
        end_date.setDate(end_date.getDate()-9);
        if (start_date > end_date) {
            var start_date = start_date.toISOString().slice(0,-5);
            document.getElementById('start_date').value += start_date;
        } else {
            var new_start_date = end_date.toISOString().slice(0,-5);
            document.getElementById('start_date').value += new_start_date;
        }
        // Match sensor id & insert to input box
        var sensor_reg = /Sensor Id\: (.*)/;
        var sensor_id = sensor_reg.exec(message)[1];
        document.getElementById('sensor_id').value += sensor_id;
    });
}

function getSensorData() {
    // Function which calls an api endpoint, receives data, 
    // then calls the initMap function with that data.
    $.getJSON('http://flask-env.hhxgagpxbh.eu-west-1.elasticbeanstalk.com/api/all_grow_true_json', initMap);
}

function getHealthyData() {
    $.getJSON('http://flask-env.hhxgagpxbh.eu-west-1.elasticbeanstalk.com/api/all_grow_healthy_json', initMap);
}

function getRecoveredData() {
    $.getJSON('http://flask-env.hhxgagpxbh.eu-west-1.elasticbeanstalk.com/api/all_grow_recovered_json', initMap);
}

function getFaultyData() {
    $.getJSON('http://flask-env.hhxgagpxbh.eu-west-1.elasticbeanstalk.com/api/all_grow_faulty_json', initMap);
}

function getGrowData() {
    start = document.getElementById('start_date').value; 
    end = document.getElementById('end_date').value; 
    sensor_id = document.getElementById('sensor_id').value;
    params = {
        start: start, 
        end: end, 
        sensor_id: sensor_id
    }
    $.getJSON('http://flask-env.hhxgagpxbh.eu-west-1.elasticbeanstalk.com/api/indiv_grow_data', params, processGrowData);
}

function checkGrowFaults() {
    sensor_id = document.getElementById('sensor_id').value;
    params = {
        sensor_id: sensor_id
    }
    $.getJSON('http://flask-env.hhxgagpxbh.eu-west-1.elasticbeanstalk.com/api/check_faulty_grow', params, processGrowFaults);
}

function processGrowFaults(data) {
    // document.getElementById('grow_health_data_1').innerHTML = data[0][0];
    // document.getElementById('grow_health_data_2').innerHTML = data[0][1];
    if (data.length == 0) {
        var days_since_anomaly = null;
        var last_anomaly_datetime = null;
    } else {
        var days_since_anomaly = data[0][0];
        var last_anomaly_datetime = data[0][1];
    }
    if (days_since_anomaly == null) {
        var health_status = 'Healthy';
    } else if (days_since_anomaly < 2) {
        var health_status = 'Not Healthy';
    } else {
        var health_status = 'Recovered State';
    }
    document.getElementById('grow_health_status').innerHTML = health_status;
    document.getElementById('grow_anomaly_date').innerHTML = last_anomaly_datetime;
}

function processGrowData(data) {
    // The order of GROW variables returned is not consistent
    // So we need to check if the variable names match
    // Before assigning them to their javascript variables
    if (data['Data'][0]['VariableCode'] == 'Thingful.Connectors.GROWSensors.air_temperature') {
        air_temperature = data['Data'][0]['Data'];
    } else if (data['Data'][0]['VariableCode'] == 'Thingful.Connectors.GROWSensors.calibrated_soil_moisture') {
        soil_moisture = data['Data'][0]['Data'];
    } else {
        light = data['Data'][0]['Data'];
    }

    if (data['Data'][1]['VariableCode'] == 'Thingful.Connectors.GROWSensors.air_temperature') {
        air_temperature = data['Data'][1]['Data'];
    } else if (data['Data'][1]['VariableCode'] == 'Thingful.Connectors.GROWSensors.calibrated_soil_moisture') {
        soil_moisture = data['Data'][1]['Data'];
    } else {
        light = data['Data'][1]['Data'];
    }

    if (data['Data'][2]['VariableCode'] == 'Thingful.Connectors.GROWSensors.air_temperature') {
        air_temperature = data['Data'][2]['Data'];
    } else if (data['Data'][2]['VariableCode'] == 'Thingful.Connectors.GROWSensors.calibrated_soil_moisture') {
        soil_moisture = data['Data'][2]['Data'];
    } else {
        light = data['Data'][2]['Data'];
    }
    window.grow_air_temperature = air_temperature;
    window.grow_soil_moisture = soil_moisture;
    drawGrowChart(air_temperature, soil_moisture, light);
}

function getWowData() {
    start = document.getElementById('start_date').value; 
    end = document.getElementById('end_date').value; 
    sensor_id = document.getElementById('sensor_id').value;
    params = {
        start: start, 
        end: end, 
        sensor_id: sensor_id
    }
    $.getJSON('http://flask-env.hhxgagpxbh.eu-west-1.elasticbeanstalk.com/api/get_wow_data', params, processWowData);
}

function processWowData(data) {
    distance = data['distance'];
    air_temperature = data['air_temp'];
    datetimes = data['datetime'];
    rainfall = data['rainfall'];
    drawWowChart(distance, air_temperature, datetimes, rainfall);
    drawGrowWowTemp(window.grow_air_temperature, air_temperature, datetimes)
    drawGrowWowRainfall(window.grow_soil_moisture, rainfall, datetimes)
}

function drawGrowWowTemp(grow_air_temp, wow_air_temp, datetimes) {
    var data = new google.visualization.DataTable();
    data.addColumn('datetime', 'datetime');
    data.addColumn('number', 'grow_air_temp');
    data.addColumn('number', 'wow_air_temp');
    for (i = grow_air_temp.length - 1; i >= 0; i--) {
        var date_str = grow_air_temp[i]['DateTime'];
        var date_edit = date_str.slice(0,4) + '-' 
                        + date_str.slice(4,6) + '-' 
                        + date_str.slice(6,8) + 'T'
                        + date_str.slice(8,10) + ':'
                        + date_str.slice(10,12) + ':'
                        + date_str.slice(12,14) 
        var my_date = new Date(date_edit);
        data.addRow([my_date, 
            grow_air_temp[i]['Value'], 
            null
        ]);
    }
    for (i = wow_air_temp.length - 1; i >= 0; i--) {
        var date_str = datetimes[i];
        var my_date = new Date(date_str);
        data.addRow([my_date,
                    null,
                    wow_air_temp[i]
                ]);
    }
    var options = {
        title: 'GROW/WOW Air Temperature Comparison',
        legend: {position: 'bottom'},
        // width: 1200,
        height: 400,
        backgroundColor: '#70d27d'
    };
    var chart = new google.visualization.LineChart(document.getElementById('grow_wow_temp_chart'));
    chart.draw(data, options);
}

function drawGrowWowRainfall(grow_soil_moisture, wow_rainfall, datetimes) {
    var data = new google.visualization.DataTable();
    data.addColumn('datetime', 'datetime');
    data.addColumn('number', 'grow_soil_moisture');
    data.addColumn('number', 'wow_rainfall');
    for (i = grow_soil_moisture.length - 1; i >= 0; i--) {
        var date_str = grow_soil_moisture[i]['DateTime'];
        var date_edit = date_str.slice(0,4) + '-' 
                        + date_str.slice(4,6) + '-' 
                        + date_str.slice(6,8) + 'T'
                        + date_str.slice(8,10) + ':'
                        + date_str.slice(10,12) + ':'
                        + date_str.slice(12,14) 
        var my_date = new Date(date_edit);
        data.addRow([my_date, 
            grow_soil_moisture[i]['Value'], 
            null
        ]);
    }
    for (i = wow_rainfall.length - 1; i >= 0; i--) {
        var date_str = datetimes[i];
        var my_date = new Date(date_str);
        data.addRow([my_date,
                    null,
                    wow_rainfall[i]
                ]);
    }
    var options = {
        title: 'GROW/WOW Rainfall - Soil Moisture Comparison',
        legend: {position: 'bottom'},
        // width: 1200,
        height: 400,
        backgroundColor: '#70d27d'
    };
    var chart = new google.visualization.LineChart(document.getElementById('grow_wow_rainfall_chart'));
    chart.draw(data, options);
}


function drawGrowChart(air_temperature, soil_moisture, light) {
    var data = new google.visualization.DataTable();
    data.addColumn('datetime', 'datetime');
    data.addColumn('number', 'air_temp');
    data.addColumn('number', 'soil_moisture');
    data.addColumn('number', 'light');

    // iterates through array backwards to graph data
    // from past to recent
    for (i = air_temperature.length - 1; i >= 0; i--) {
        var date_str = air_temperature[i]['DateTime'];
        var date_edit = date_str.slice(0,4) + '-' 
                        + date_str.slice(4,6) + '-' 
                        + date_str.slice(6,8) + 'T'
                        + date_str.slice(8,10) + ':'
                        + date_str.slice(10,12) + ':'
                        + date_str.slice(12,14) 
        var my_date = new Date(date_edit);
        data.addRow([my_date, 
                    air_temperature[i]['Value'],
                    soil_moisture[i]['Value'],
                    light[i]['Value']
                ]);
    }

    var options = {
        title: 'GROW Sensor Values',
        legend: {position: 'bottom'},
        // width: 1200,
        height: 400,
        backgroundColor: '#ffffff'
        // 70d27d
        // '#35a744'
        // backgroundColor: '#C2F3C8'
        // CAFFE1
    };
    var chart = new google.visualization.LineChart(document.getElementById('grow_line_chart'));
    chart.draw(data, options);
}

function drawWowChart(distance, air_temperature, datetimes, rainfall) {
    var data = new google.visualization.DataTable();
    data.addColumn('datetime', 'datetime');
    data.addColumn('number', 'air_temp');
    data.addColumn('number', 'rainfall');
    for (i = air_temperature.length - 1; i >= 0; i--) {
        var date_str = datetimes[i];
        var my_date = new Date(date_str);
        data.addRow([my_date,
                    air_temperature[i], 
                    rainfall[i],
                ]);
    }
    var options = {
        title: 'WOW Site ' + distance + ' km away',
        legend: {position: 'bottom'},
        // width: 1200,
        height: 400,
        backgroundColor: '#70d27d'
    };
    var chart = new google.visualization.LineChart(document.getElementById('wow_line_chart'));
    chart.draw(data, options);
}

function initMap(data) {
    // Create the map centered on the United Kingdom.
    // var dat = $.getJSON('http://0.0.0.0:8080/all_grow_true_json');
    // for (var index in dat) {console.log(data[index][0].address)};
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 4,
        center: {lat: 55.3781, lng: 3.4360},
        mapTypeId: 'terrain'
    });

    // Image to use for map pinpoint icon
    var image = {
        url: 'static/images/google-maps-location-icon.jpg',
        scaledSize : new google.maps.Size(12, 12),
    };
    // http://chittagongit.com//images/google-maps-location-icon/google-maps-location-icon-2.jpg
    var grow;
    grow = data;
    for (var sensor in grow) {
        // document.getElementById("demo").innerHTML = sensor;
        var growCircle = new google.maps.Circle({
            strokeColor: '#FF0000',
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: '#FF0000',
            fillOpacity: 0.35,
            map: map,
            center: new google.maps.LatLng(grow[sensor].latitude, grow[sensor].longitude),
            radius: 200,
            label: grow[sensor].sensor_id,
            county: grow[sensor].address
        });

        var marker = new google.maps.Marker({
            position: new google.maps.LatLng(grow[sensor].latitude, grow[sensor].longitude),
            map: map, 
            animation: google.maps.Animation.DROP,
            icon: image
            });
        

        addInfoWindow(marker, ('Address: ' + grow[sensor].address +
            // '<br>Owner Id: ' + grow[sensor].owner_id +
            '<br>Days Active: ' + grow[sensor].days_active +
            '<br>Start Date: ' + grow[sensor].start_date +
            '<br>End Date: ' + grow[sensor].end_date +
            '<br>Sensor Id: ' + grow[sensor].sensor_id));
    }
}

// References:
// Google Maps API Documentation was referenced.
// https://developers.google.com/maps/documentation/javascript/tutorial

// JQuery Reference.
// https://api.jquery.com/jquery.getjson/ 
// JQuery Download.
// https://jquery.com/download/

// Image for Map Marker Icon:
// http://chittagongit.com//images/google-maps-location-icon/google-maps-location-icon-2.jpg

// Anthony Delivanis

