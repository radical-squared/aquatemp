from homeassistant.backports.enum import StrEnum
from homeassistant.components.climate.const import FAN_AUTO, FAN_LOW, HVACMode

DOMAIN = "aqua_temp"
DEFAULT_NAME = "Aqua Temp"
SIGNAL_AQUA_TEMP_DEVICE_NEW = f"signal_{DOMAIN}_device_new"

HTTP_HEADER_X_TOKEN = "x-token"

CONF_API_TYPE = "api_type"

PRODUCT_IDS = [
    "1132174963097280512",  # Aqua Temp
    "1245226668902080512",  # Hitemp
    "1186904563333062656",  # Aqua Temp
    "1158905952238313472",  # Aqua Temp
    "1442284873216843776",  # Aqua Temp
    "1548963836789501952",  # Aqua Temp
]

MANUAL_MUTE_AUTO = "0"
MANUAL_MUTE_LOW = "1"

FAN_MODE_MAPPING = {FAN_AUTO: MANUAL_MUTE_AUTO, FAN_LOW: MANUAL_MUTE_LOW}

POWER_MODE_OFF = "0"
POWER_MODE_ON = "1"

HEADERS = {"Content-Type": "application/json; charset=utf-8"}

API_MAX_ATTEMPTS = 3

DATA_ITEM_DEVICES = "device"
DATA_ITEM_LOGIN_DETAILS = "login-details"
DATA_ITEM_CONFIG = "configuration"

CONFIG_SET_MODE = "mode"
CONFIG_SET_POWER = "power"
CONFIG_SET_TEMPERATURE = "temperature"
CONFIG_SET_FAN = "fan"
CONFIG_SET_CURRENT_TEMPERATURE = "current_temperature"

API_STATUS = "api_status"

PRODUCT_ID_DEFAULT = "default"

CONFIG_HVAC_MODES = "hvac_modes"
CONFIG_HVAC_OFF = str(HVACMode.OFF)
CONFIG_HVAC_HEAT = str(HVACMode.HEAT)
CONFIG_HVAC_COOL = str(HVACMode.COOL)
CONFIG_HVAC_AUTO = str(HVACMode.AUTO)
CONFIG_HVAC_SET = "set"
CONFIG_HVAC_TARGET = "target"
CONFIG_HVAC_MINIMUM = "minimum"
CONFIG_HVAC_MAXIMUM = "maximum"

CONFIG_FAN_MODES = "fan_modes"
CONFIG_FAN_AUTO = "auto"
CONFIG_FAN_LOW = "low"

DEVICE_CONTROL_VALUE = "value"
DEVICE_CONTROL_PARAM = "param"


class ProductParameter(StrEnum):
    MAPPING = "mapping"
    ENTITY_DESCRIPTION = "entity_description"
