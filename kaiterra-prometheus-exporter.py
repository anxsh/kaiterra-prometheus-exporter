#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import requests
import aqi
from flask import Flask, Response, request

app = Flask(__name__)

parser = argparse.ArgumentParser(description='Web server that publishes Kaiterra (LaserEgg+ Chemical) metrics for Prometheus')

parser.add_argument('--kaiterra-api-key',
                    type=str,
                    help="API key for Kaiterra (https://www.kaiterra.com/dev/)",
                    required=True)

parser.add_argument('--port',
                    type=int,
                    help="listen port for this server",
                    default='9880')

LASER_EGG_METRICS = [
    { 'name': 'tvoc', 'field': 'rtvoc', 'description': 'Total volatile organic compounds (ppb)' },
    { 'name': 'humidity', 'field': 'rhumid', 'description': 'Humidity (%)' },
    { 'name': 'pm10', 'field': 'rpm10c', 'description': 'PM10: inhalable particles with diameters <= 10 micrometers (µg/m³)' },
    { 'name': 'pm25', 'field': 'rpm25c', 'description': 'PM2.5: inhalable particles with diameters <= 2.5 micrometers (µg/m³)' },
    { 'name': 'temperature', 'field': 'rtemp', 'description': 'Temperature (C)' }
]

API_URL_FORMAT = 'https://api.kaiterra.com/v1/devices/{device_id}/top?key={api_key}'

RESPONSE_FORMAT = '\n'.join(['# HELP {metric} {description}',
                             '# TYPE {metric} gauge',
                             '{metric} {value}'])    

METRIC_PREFIX = 'kaiterra'

def start_server(port):
    app.run(host='0.0.0.0', port=port, debug=False)    

def main():
    args = parser.parse_args()
    app.config['api_key'] = args.kaiterra_api_key
    print("starting server at port: %d" % args.port)
    start_server(args.port)

def get_device_readings(device_id):
    api_key = app.config['api_key']

    readings = {}
    r = requests.get(API_URL_FORMAT.format(device_id=device_id, api_key=api_key))
    if r.status_code == 200:
        data = r.json()['data']
        for reading in data:
            readings[reading['param']] = reading['points'][0]['value']
    return readings

@app.route("/")
def hello_world():
    return "<p>Hello, World! This is the Kaiterra Exporter for Prometheus</p>"


@app.route("/metrics")
def metrics():

    device_id = request.args.get('device_id')
    device_readings = get_device_readings(device_id)

    responses = []
    for metric in LASER_EGG_METRICS:
        responses.append(RESPONSE_FORMAT.format(metric='%s_%s' % (METRIC_PREFIX, metric['name']),
                                                description=metric['description'],
                                                value=device_readings[metric['field']]))

    # compute and add aqi
    aqi_value = aqi.to_aqi([
        (aqi.POLLUTANT_PM25, device_readings['rpm25c']),
        (aqi.POLLUTANT_PM10, device_readings['rpm10c'])
    ])
    responses.append(RESPONSE_FORMAT.format(metric='%s_aqi' % (METRIC_PREFIX),
                                            description='US Air Quality Index',
                                            value=aqi_value))
    
    return Response('\n'.join(responses), mimetype='text/plain')

if __name__ == '__main__':
    main()
