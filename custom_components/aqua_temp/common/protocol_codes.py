from homeassistant.backports.enum import StrEnum


class ProtocolCode(StrEnum):
    MODE = "Mode"
    POWER = "Power"
    SET_TEMP = "Set_Temp"
    MANUAL_MUTE = "Manual-mute"
    CURRENT_TEMPERATURE = "T02"
    TARGET_TEMPERATURE_COOL = "R01"
    TARGET_TEMPERATURE_HEAT = "R02"
    TARGET_TEMPERATURE_AUTO = "R03"
    MINIMUM_TEMPERATURE_COOL = "R08"
    MAXIMUM_TEMPERATURE_COOL = "R09"
    MINIMUM_TEMPERATURE_HEAT = "R10"
    MAXIMUM_TEMPERATURE_HEAT = "R11"
