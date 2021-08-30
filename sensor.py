"""Platform for sensor integration."""
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

import requests
import json
from time import sleep
from datetime import datetime



URL_LOGIN="https://cloud.linked-go.com/cloudservice/api/app/user/login.json"
URL_DEVICELIST="https://cloud.linked-go.com/cloudservice/api/app/device/deviceList.json"
URL_GETDATABYCODE="https://cloud.linked-go.com/cloudservice/api/app/device/getDataByCode.json"
URL_GETDEVICESTATUS="https://cloud.linked-go.com/cloudservice/api/app/device/getDeviceStatus.json"

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities([Aquatemp(config)])


class Aquatemp(Entity):
    """Representation of a Sensor."""

    def __init__(self, config):
        """Initialize the sensor."""
        self._state = None
        self._name = config['name']
        self._token = None
        self._device_code = None
        self._username = config['username']
        self._password = config['password']

        self._attributes = {}


        self._headers = {"Content-Type": "application/json; charset=utf-8"}
        
        # GET X-TOKEN
        data = {"user_name":self._username, "password":self._password,"type":"2"}
        r = requests.post(URL_LOGIN, headers=self._headers, data=json.dumps(data)).json()
        self._token = r['object_result']['x-token']        
        self._headers['x-token'] = self._token

        # GET DEVICE CODE
        s = requests.post(URL_DEVICELIST, headers = self._headers).json()
        self._device_code = s['object_result'][0]['device_code']

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name  

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        data = {"device_code":self._device_code,"protocal_codes":["Power","Mode","Manual-mute","T01","T02","2074","2075","2076","2077","H03","Set_Temp","R08","R09","R10","R11","R01","R02","R03","T03","1158","1159","F17","H02","T04","T05"]}
        t = requests.post(URL_GETDATABYCODE, headers = self._headers, data=json.dumps(data)).json()
        for i in t['object_result']:
            if i['code'] == 'T02':
                self._attributes['in'] = i['value']
            elif i['code'] == 'T03':
                self._attributes['out'] = i['value']
            elif i['code'] == 'R02':
                self._attributes['target'] = i['value']                


        data.pop('protocal_codes')
        u = requests.post(URL_GETDEVICESTATUS, headers = self._headers, data=json.dumps(data)).json()
        self._attributes['is_fault'] = u['object_result']['is_fault']
        self._state = u['object_result']['status']
