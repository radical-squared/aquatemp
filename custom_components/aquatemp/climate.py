"""Platform for climate integration."""
from operator import attrgetter
from homeassistant.const import (TEMP_CELSIUS, TEMP_FAHRENHEIT,)
from homeassistant.helpers.entity import Entity
from homeassistant.components.climate import ClimateEntity

# from aiohttp import ClientSession, ClientResponse
import aiohttp
import json
from datetime import datetime
import asyncio

import logging


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
SERVER_URL="https://cloud.linked-go.com"
LOGIN_PATH="/cloudservice/api/app/user/login.json"
DEVICELIST_PATH="/cloudservice/api/app/device/deviceList.json"
GETDATABYCODE_PATH="/cloudservice/api/app/device/getDataByCode.json"
GETDEVICESTATUS_PATH="/cloudservice/api/app/device/getDeviceStatus.json"
CONTROL_PATH="/cloudservice/api/app/device/control.json"
GETFAULT_PATH="/cloudservice/api/app/device/getFaultDataByDeviceCode.json"


_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the climate platform."""
    async_add_entities([Aquatemp(config)],True)


class Aquatemp(ClimateEntity):
    """Representation of a climate entity."""

    def __init__(self, config):
        """Initialize the climate entity."""
        self._name = config['name']
        self._token = None
        self._device_code = None
        self._uid = config['unique_id']
        self._username = config['username']
        self._password = config['password']
        self._min_temp = config['min_temp']
        self._max_temp = config['max_temp']        
        self._inlet_temp = None
        self._outlet_temp = None 
        self._temperature_unit = TEMP_CELSIUS if config['temperature_unit'] == "C" else TEMP_FAHRENHEIT
        self._attribute_map = config['attribute_map']
        self._expose_codes = bool(config['expose_codes'])


        self._current_temperature = None
        self._target_temperature = None
        self._hvac_mode = None
        self._fan_mode = None

        self._attributes = {}
        self._codes = {}

        self._headers = {'Content-Type': 'application/json; charset=utf-8'}
        # _LOGGER.debug(config['attribute_map'])


    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes

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
    def inlet_temp(self):
        """Returns the inlet temperature."""
        return self._inlet_temp
    
    @property
    def outlet_temp(self):
        """Returns the outlet temperature."""
        return self._outlet_temp

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name  

    @property
    def unique_id(self):
        """Return the device code of the sensor as a unique ID to allow the devices to be edited on the dashboard."""
        return self._uid  

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes


    def get_value(self, code):
        if len(self._codes) > 0:
            for c in self._codes:
                if c['code'] == code:
                    return c['value']
        return None

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")

        if self._hvac_mode == HVAC_MODE_COOL:
            mode = 'R01'
        elif self._hvac_mode == HVAC_MODE_AUTO:
            mode = 'R03'
        else:
            mode = 'R02'

        data = {'param':[{'device_code':self._device_code,'protocol_code':mode,'value':temperature},{'device_code':self._device_code,'protocol_code':'Set_Temp','value':temperature}]} 
        
        async with aiohttp.ClientSession(SERVER_URL) as session:
            async with session.post(CONTROL_PATH, headers = self._headers, json=data) as response:
                if response:
                    response_json = await response.json()
                    if response_json['error_msg'] == "Success":
                        self._target_temperature = temperature

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

        code = 'mode'
        value = None
        hm = None

        if self._hvac_mode == HVAC_MODE_OFF and hvac_mode != HVAC_MODE_OFF:
            data = {'param':[{'device_code':self._device_code,'protocol_code':'power','value':'1'}]}
            async with aiohttp.ClientSession(SERVER_URL) as session:
                async with session.post(CONTROL_PATH, headers = self._headers, json=data) as response:
                    # _LOGGER.debug(response)
                    if response.status:
                        response_json = await response.json()
                        _LOGGER.debug(response_json)
                        if response_json['error_msg'] == "Success":
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
        async with aiohttp.ClientSession(SERVER_URL) as session:
            async with session.post(CONTROL_PATH, headers = self._headers, json=data) as response:
                # _LOGGER.debug(response)
                if response:
                    response_json = await response.json()
                    _LOGGER.debug(response_json)
                    if response_json['error_msg'] == "Success":
                        self._hvac_mode = hm
                        self._attributes['power'] = 'off' if hvac_mode == HVAC_MODE_OFF else 'on'

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""            

        mode = 0
        fm = 0

        if fan_mode == FAN_AUTO:
            mode = "0"
            fm = FAN_AUTO
        elif fan_mode == FAN_LOW:
            mode = "1"
            fm = FAN_LOW

        data = {'param':[{'device_code':self._device_code,'protocol_code':'Manual-mute','value':mode}]}
        async with aiohttp.ClientSession(SERVER_URL) as session:
            async with session.post(CONTROL_PATH, headers = self._headers, json=data) as response:
                _LOGGER.debug(response.status)
                if response.status == 200:
                    response_json = await response.json()
                    _LOGGER.debug(response_json)
                    if response_json['error_msg'] == "Success":
                        self._fan_mode = fm        


    async def async_update(self):
        """Fetch new state data for the sensor."""

        if self._token == None:
            async with aiohttp.ClientSession(SERVER_URL) as session:
                try:
                    await self.login(session)
                except:
                    self._token = None
                    _LOGGER.error("Error logging in. Will keep on trying.")
                    return   
                
        try:
            await self.fetch_data()
        except:
            self._token = None
            _LOGGER.error("Error fetching data. Reconnecting.")
            return
        
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

        if self.get_value('T02') is not None:
            self._current_temperature = float(self.get_value('T02'))

        for code in self._attribute_map:
            if self.get_value(code) is not None:
                self._attributes[self._attribute_map[code]] = float(self.get_value(code))

        try:
            await self.fetch_errors()
        except:
            self._token = None
            _LOGGER.error("Error fetching errors. Reconnecting.")
            return            

    async def fetch_data(self):

        data = {'device_code':self._device_code,'protocal_codes':['Power','Mode','Manual-mute','T01','T02','2074','2075','2076','2077','H03','Set_Temp','R08','R09','R10','R11','R01','R02','R03','T03','1158','1159','F17','H02','T04','T05','T06','T07','T12','T14']}

        async with aiohttp.ClientSession(SERVER_URL) as session:
            async with session.post(GETDATABYCODE_PATH, headers = self._headers, json=data) as response:
                if response.status == 200:
                    response_json = await response.json()
                    _LOGGER.debug(response_json)
                    if response_json['error_msg'] == "Success":
                        self._codes = response_json['object_result']
                    if self._expose_codes:
                        self._attributes['codes'] = response_json['object_result']
                else:
                    await self.login(session)

    async def fetch_errors(self):

        async with aiohttp.ClientSession(SERVER_URL) as session:
            async with session.post(GETDEVICESTATUS_PATH, headers = self._headers, json={"device_code":self._device_code}) as response:
                if response:
                    response_json = await response.json()
                    _LOGGER.debug(response_json)
                    self._attributes['is_fault'] = bool(response_json['object_result']['is_fault'])
                else:
                    await self.login(session)

            if self._attributes['is_fault'] == True:
                async with session.post(GETFAULT_PATH, headers = self._headers, json={"device_code":self._device_code}) as response:
                    if response:
                        response_json = await response.json()
                        _LOGGER.debug(response_json)
                        self._attributes['fault'] = response_json['object_result'][0]['description']
                    else:
                        await self.login(session)
            else:
                if "fault" in self._attributes:
                    self._attributes.pop('fault')



    async def login(self, session):

        # GET X-TOKEN
        # _LOGGER.debug("inside login")
        data = {'user_name':self._username, 'password':self._password,'type':'2'}
        async with session.post(LOGIN_PATH, headers = self._headers, json=data) as response:
            response_json = await response.json()
            _LOGGER.debug(response_json)
            self._token = response_json['object_result']['x-token']        
            self._headers['x-token'] = self._token
            

        # GET DEVICE CODE
        async with session.post(DEVICELIST_PATH, headers = self._headers) as response:
            response_json = await response.json()
            _LOGGER.debug(response_json)
            self._device_code = response_json['object_result'][0]['device_code']
