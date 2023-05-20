from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import FAN_AUTO, FAN_LOW, HVACMode
from homeassistant.const import (
    CONF_TEMPERATURE_UNIT,
    STATE_OFF,
    STATE_ON,
    Platform,
    UnitOfTemperature,
)

DOMAIN = "aqua_temp"
DEFAULT_NAME = "Aqua Temp"

SERVER_URL = "https://cloud.linked-go.com"
LOGIN_PATH = "/cloudservice/api/app/user/login.json"
DEVICELIST_PATH = "/cloudservice/api/app/device/deviceList.json"
GETDATABYCODE_PATH = "/cloudservice/api/app/device/getDataByCode.json"
GETDEVICESTATUS_PATH = "/cloudservice/api/app/device/getDeviceStatus.json"
CONTROL_PATH = "/cloudservice/api/app/device/control.json"
GETFAULT_PATH = "/cloudservice/api/app/device/getFaultDataByDeviceCode.json"


HVAC_PC_COOL = "0"
HVAC_PC_HEAT = "1"
HVAC_PC_AUTO = "2"

MODE_SET_TEMPERATURE_OFF = "0"
MODE_SET_TEMPERATURE_COOL = "1"
MODE_SET_TEMPERATURE_HEAT = "2"
MODE_SET_TEMPERATURE_AUTO = "3"

HVAC_MODE_MAPPING = {
    HVACMode.OFF: MODE_SET_TEMPERATURE_OFF,
    HVACMode.COOL: MODE_SET_TEMPERATURE_COOL,
    HVACMode.HEAT: MODE_SET_TEMPERATURE_HEAT,
    HVACMode.AUTO: MODE_SET_TEMPERATURE_AUTO,
}

HVAC_PC_MAPPING = {
    HVAC_PC_COOL: HVACMode.COOL,
    HVAC_PC_HEAT: HVACMode.HEAT,
    HVAC_PC_AUTO: HVACMode.AUTO,
}

HVAC_MODE_MIN_TEMP = {HVACMode.COOL: "R08", HVACMode.HEAT: "R10"}

HVAC_MODE_MAX_TEMP = {HVACMode.COOL: "R09", HVACMode.HEAT: "R11"}

MANUAL_MUTE_AUTO = "0"
MANUAL_MUTE_LOW = "1"

FAN_MODE_MAPPING = {FAN_AUTO: MANUAL_MUTE_AUTO, FAN_LOW: MANUAL_MUTE_LOW}

POWER_MODE_OFF = "0"
POWER_MODE_ON = "1"

POWER_MODE_MAPPING = {POWER_MODE_OFF: STATE_OFF, POWER_MODE_ON: STATE_ON}

MANUAL_MUTE_MAPPING = {MANUAL_MUTE_AUTO: FAN_AUTO, MANUAL_MUTE_LOW: FAN_LOW}

PROTOCOL_CODE_POWER = "Power"
PROTOCOL_CODE_HVAC_MODE = "Mode"
PROTOCOL_CODE_FAN_MODE = "Manual-mute"
PROTOCOL_CODE_CURRENT_TEMP = "T02"

PROTOCOL_CODES = {
    PROTOCOL_CODE_POWER: None,
    PROTOCOL_CODE_HVAC_MODE: None,
    PROTOCOL_CODE_FAN_MODE: None,
    "2074": None,
    "2075": None,
    "2076": None,
    "2077": None,
    "Set_Temp": None,
    "1158": None,
    "1159": None,
    "D01": "Start defrosting temperature",
    "D02": "End defrost temperature",
    "D03": "defrosting cycle",
    "D04": "Maximum defrosting time",
    "D05": "Minimum defrosting time",
    "D06": "Defrost mode",
    "D07": "Defrost heater control",
    "D08": "Defrost AUTO set",
    "E01": "EEV 1 mode",
    "E02": "Super heat 1",
    "E03": "Initial place 1",
    "E04": "EEV 2 mode",
    "E05": "Super heat 2",
    "E06": "Initial place 2",
    "E07": "Minimum place",
    "E08": "Defrost place",
    "E09": "Cooling place",
    "E10": "Low exhaust",
    "E11": "High exhaust",
    "F01": "Fan parameter",
    "F02": "Coil temperature in high speed fan mode (Cooling)",
    "F03": "Coil temperature in low speed fan mode (Cooling)",
    "F04": "Coil temperature when the fan stop (Cooling)",
    "F05": "Coil temperature in high speed fan mode (Heating)",
    "F06": "Coil temperature in low speed fan mode (Heating)",
    "F07": "Coil temperature when the fan stop (Heating)",
    "F08": "Fan start low speed running time",
    "F09": "Fan stop low speed running time",
    "F10": "Fan quantity",
    "F11": "Fan speed control temp.",
    "F17": None,
    "H02": "System quantity",
    "H03": "4-way valve polarity",
    "H04": "4-way valve control",
    "R01": "Inlet water setting temperature (cooling)",
    "R02": "Inlet water setting temperature (Heating)",
    "R03": "Target setting temperature (Auto mode)",
    "R08": "Minimum set point in Cooling",
    "R09": "Maximum Cooling set point",
    "R10": "Minimum Heating set point",
    "R11": "Maximum Heating set point",
    "U02": "Pulse",
    "T01": "Suction temperature",
    "T02": "Inlet water temp.",
    "T03": "Outlet water temp",
    "T04": "Coil temperature",
    "T05": "Ambient temperature",
    "T06": "Antifreeze 1 temperature",
    "T07": "Antifreeze 2 temperature",
    "T08": "Suction 1 temperature",
    "T09": "Suction 2 temperature",
    "T10": "Exhaust 1 temperature",
    "T11": "Exhaust 2 temperature",
    "T12": "Hot water temperature",
    "T14": None,
}

BINARY_SENSOR_CONFIG = {
    "Power": {
        "value": "1",
        "name": "Power",
        "device_class": BinarySensorDeviceClass.POWER,
        "attributes": None,
    },
    "device_status": {
        "value": "ONLINE",
        "name": "Status",
        "device_class": BinarySensorDeviceClass.CONNECTIVITY,
        "attributes": None,
    },
    "is_fault": {
        "value": True,
        "name": "Fault",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "attributes": ["fault"],
    },
}

HEADERS = {"Content-Type": "application/json; charset=utf-8"}

CONFIG_FIELDS = [CONF_TEMPERATURE_UNIT]

DATA_ITEM_API = "data"
DATA_ITEM_FAULT = "fault"
DATA_ITEM_CONFIG = "configuration"

DEFAULT_TEMPERATURE_UNIT = UnitOfTemperature.CELSIUS

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CLIMATE, Platform.SENSOR, Platform.SELECT]
