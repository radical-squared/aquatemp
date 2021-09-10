"""Platform for climate integration."""
from homeassistant.const import (TEMP_CELSIUS, TEMP_FAHRENHEIT,)
from homeassistant.helpers.entity import Entity
from homeassistant.components.climate import ClimateEntity

import requests
import json
from datetime import datetime


from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_AUTO,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_FAN_MODE,
    FAN_AUTO,
    FAN_LOW,
)

URL_LOGIN="https://cloud.linked-go.com/cloudservice/api/app/user/login.json"
URL_DEVICELIST="https://cloud.linked-go.com/cloudservice/api/app/device/deviceList.json"
URL_GETDATABYCODE="https://cloud.linked-go.com/cloudservice/api/app/device/getDataByCode.json"
URL_GETDEVICESTATUS="https://cloud.linked-go.com/cloudservice/api/app/device/getDeviceStatus.json"
URL_CONTROL="https://cloud.linked-go.com/cloudservice/api/app/device/control.json"
URL_GETFAULT="https://cloud.linked-go.com/cloudservice/api/app/device/getFaultDataByDeviceCode.json"



def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the climate platform."""
    add_entities([Aquatemp(config)])


class Aquatemp(ClimateEntity):
    """Representation of a climate entity."""

    def __init__(self, config):
        """Initialize the climate entity."""
        # self._state = None
        self._name = config['name']
        self._token = None
        self._device_code = None
        self._username = config['username']
        self._password = config['password']
        self._min_temp = config['min_temp']
        self._max_temp = config['max_temp']        
        self._temperature_unit = TEMP_CELSIUS if config['temperature_unit'] == "C" else TEMP_FAHRENHEIT


        self._current_temperature = None
        self._target_temperature = None
        self._hvac_mode = None
        self._fan_mode = None

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

        self.update()


    @property
    def fan_modes(self):
        """Returns the list of available fan modes. Requires SUPPORT_FAN_MODE."""
        return [FAN_AUTO, FAN_LOW]

    @property
    def fan_mode(self):
        """Returns the current fan mode. Requires SUPPORT_FAN_MODE."""
        return self._fan_mode


    @property
    def supported_features(self):
        """Bitmap of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

    @property
    def hvac_mode(self):
        """The current operation (e.g. heat, cool, idle). Used to determine state."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        return [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_AUTO]

    @property
    def current_temperature(self):
        """The current temperature."""
        return self._current_temperature

    @property
    def temperature_unit(self):
        """Return temperature unit."""
        return self._temperature_unit

    @property
    def target_temperature(self):
        """The temperature currently set to be reached."""
        return self._target_temperature

    @property
    def max_temp(self):
        """Returns the maximum temperature."""
        return self._max_temp

    @property
    def min_temp(self):
        """Returns the minimum temperature."""
        return self._min_temp

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name  

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes


    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")

        if self._hvac_mode == HVAC_MODE_COOL:
            mode = 'R01'
        elif self._hvac_mode == HVAC_MODE_AUTO:
            mode = 'R03'
        else:
            mode = 'R02'

        data = {"param":[{"device_code":self._device_code,"protocol_code":mode,"value":temperature},{"device_code":self._device_code,"protocol_code":"Set_Temp","value":temperature}]} 
        t = requests.post(URL_CONTROL, headers = self._headers, data=json.dumps(data)).json()

        if t['error_msg'] == "Success":
            self._target_temperature = temperature

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

        code = 'mode'
        value = None
        hm = None

        if self._hvac_mode == HVAC_MODE_OFF and hvac_mode != HVAC_MODE_OFF:
            data = {"param":[{"device_code":self._device_code,"protocol_code":"power","value":"1"}]}
            t = requests.post(URL_CONTROL, headers = self._headers, data=json.dumps(data)).json()
            if t['error_msg'] == "Success":
                self._attributes['power'] = 'off' if hvac_mode == HVAC_MODE_OFF else 'on'

        if hvac_mode == HVAC_MODE_COOL:
            value = "0"
            hm = HVAC_MODE_COOL
        elif hvac_mode == HVAC_MODE_HEAT:
            value = "1"
            hm = HVAC_MODE_HEAT
        elif hvac_mode == HVAC_MODE_AUTO:
            value = "2"
            hm = HVAC_MODE_AUTO
        elif hvac_mode == HVAC_MODE_OFF:
            code = "power"
            value = "0"
            hm = HVAC_MODE_OFF            

        data = {"param":[{"device_code":self._device_code,"protocol_code":code,"value":value}]}
        t = requests.post(URL_CONTROL, headers = self._headers, data=json.dumps(data)).json()

        if t['error_msg'] == "Success":
            self._hvac_mode = hm
            self._attributes['power'] = 'off' if hvac_mode == HVAC_MODE_OFF else 'on'

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""            

        mode = 0
        fm = 0

        if fan_mode == FAN_AUTO:
            mode = "0"
            fm = FAN_AUTO
        elif fan_mode == FAN_LOW:
            mode = "1"
            fm = FAN_LOW

        data = {"param":[{"device_code":self._device_code,"protocol_code":"Manual-mute","value":mode}]}
        t = requests.post(URL_CONTROL, headers = self._headers, data=json.dumps(data)).json()

        if t['error_msg'] == "Success":
            self._fan_mode = fm        



    def update(self):
        """Fetch new state data for the sensor."""
        
        self.fetch_data()

        # Check Power
        self._attributes['power'] = 'on' if self.get_value('Power') == '1' else 'off'

        # Check hvac_mode & target temperature
        if self._attributes['power'] == 'off':
            self._hvac_mode = HVAC_MODE_OFF
        else:
            mode = self.get_value('Mode')
            if mode == '0':
                self._hvac_mode = HVAC_MODE_COOL
                self._target_temperature = float(self.get_value('R01'))
            elif mode == '1':
                self._hvac_mode = HVAC_MODE_HEAT
                self._target_temperature = float(self.get_value('R02'))             
            elif mode == '2':
                self._hvac_mode = HVAC_MODE_AUTO     
                self._target_temperature = float(self.get_value('R03'))

        self._fan_mode = FAN_AUTO if self.get_value('Manual-mute') == '0' else FAN_LOW
        self._current_temperature = float(self.get_value('T02'))
        self._attributes['ambient_temperature'] = float(self.get_value('T05'))
        self._attributes['outlet_temperature'] = float(self.get_value('T03'))

        self.fetch_errors()

    def get_value(self, code):
        if 'codes' in self._attributes:
            for c in self._attributes['codes']:
                if c['code'] == code:
                    return c['value']
        return None

    def fetch_data(self):

        data = {"device_code":self._device_code,"protocal_codes":["Power","Mode","Manual-mute","T01","T02","2074","2075","2076","2077","H03","Set_Temp","R08","R09","R10","R11","R01","R02","R03","T03","1158","1159","F17","H02","T04","T05"]}
        t = requests.post(URL_GETDATABYCODE, headers = self._headers, data=json.dumps(data)).json()
        
        if t['error_msg'] == "Success":
            self._attributes['codes'] = t['object_result']

    def fetch_errors(self):
        
        u = requests.post(URL_GETDEVICESTATUS, headers = self._headers, data=json.dumps({"device_code":self._device_code})).json()
        self._attributes['is_fault'] = bool(u['object_result']['is_fault'])

        if self._attributes['is_fault'] == True:
            v = requests.post(URL_GETFAULT, headers = self._headers, data=json.dumps({"device_code":self._device_code})).json()
            self._attributes['fault'] = v['object_result'][0]['description']
        else:
            if "fault" in self._attributes:
                self._attributes.pop('fault')
