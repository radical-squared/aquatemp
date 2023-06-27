from homeassistant.backports.enum import StrEnum


class AccountTypes(StrEnum):
    AquaTempAndroid = ("Aqua Temp (Android)",)
    AquaTempIOS = ("Aqua Temp (iOS)",)
    HiTemp = "HiTemp"
