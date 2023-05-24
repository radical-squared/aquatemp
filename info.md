# Home Assistant Aquatemp Heat Pump Climate Entity (custom component)

This is Home Assistant's custom climate entity to control AquaTemp-compatible heat pumps through AquaTemp cloud API.
It allows controlling temperature, HVAC mode (heat, cool, auto, off) and fan mode (low, auto).
It also reports temperatures, status, faults through binary sensors and sensors.
AquaTemp's cloud protocol is based on dst6se's https://github.com/dst6se/aquatemp project with additional functionality.

[Changelog](https://github.com/radical-squared/aquatemp/blob/master/CHANGELOG.md)

## How to

#### Requirements

- Account for AquaTemp

#### Installations via HACS [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

- In HACS, look for "Aqua Temp" and install and restart
- If integration was not found, please add custom repository `radical-squared/aquatemp` as integration
- In Settings --> Devices & Services - (Lower Right) "Add Integration"

#### Setup

To add integration use Configuration -> Integrations -> Add `Aqua Temp`
Integration supports **multiple** accounts and devices

| Fields name | Type    | Required | Default | Description                       |
| ----------- | ------- | -------- | ------- | --------------------------------- |
| Username    | Textbox | +        | -       | Username of AquaTemp account      |
| Password    | Textbox | +        | -       | Password for the AquaTemp account |

###### Validation errors

| Errors                    |
| ------------------------- |
| Invalid credentials (403) |

## HA Device

Device scheme is according to data from the API

```json
{
  "identifiers": ["aqua_temp", "{DEVICE ID}"],
  "name": "{DEVICE NICK NAME or DEVICE CODE}",
  "device_type": "{DEVICE TYPE}"
}
```

## HA Components

Per device the following components will be generated:

| Entity Name                               | Type          | Source              | Parameter        | Description                                                                                       |
| ----------------------------------------- | ------------- | ------------------- | ---------------- | ------------------------------------------------------------------------------------------------- |
| {HA Device Name} Status                   | Binary Sensor | Devices list        | device_status    | Represents whether device is online or not                                                        |
| {HA Device Name} Fault                    | Binary Sensor | Devices status      | is_fault         | Represents whether device has an issue, in case it has, attribute `fault` will hold the details   |
| {HA Device Name} Power                    | Binary Sensor | Protocol Codes      | Power            | Represents whether device is on or off                                                            |
| {HA Device Name} Power                    | Climate       | Protocol Codes      | Power            | Controls heat pump - HVAC Modes (Off, Cool, Heat, Auto), Fan Mode (Low, Auto), Target temperature |
| {HA Device Name} Suction temperature      | Sensor        | Protocol Codes      | T01              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Inlet water temp.        | Sensor        | Protocol Codes      | T02              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Outlet water temp        | Sensor        | Protocol Codes      | T03              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Coil temperature         | Sensor        | Protocol Codes      | T04              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Ambient temperature      | Sensor        | Protocol Codes      | T05              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Antifreeze 1 temperature | Sensor        | Protocol Codes      | T06              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Antifreeze 2 temperature | Sensor        | Protocol Codes      | T07              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Suction 1 temperature    | Sensor        | Protocol Codes      | T08              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Suction 2 temperature    | Sensor        | Protocol Codes      | T08              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Exhaust 1 temperature    | Sensor        | Protocol Codes      | T09              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Exhaust 1 temperature    | Sensor        | Protocol Codes      | T10              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Hot water temperature    | Sensor        | Protocol Codes      | T12              | Represents the temperature according to the name of the component                                 |
| {HA Device Name} Temperature Unit         | Select        | Local configuration | temperature_unit | Controls the unit of temperature to match the one configured in the Aqua Temp device              |

## Protocol Codes

Protocol Codes first character represent a category, below are the categories:

| Character | Description           | Parameters |
| --------- | --------------------- | ---------- |
| /         | Hardware parameter    | /01-/28    |
| A         | Protection parameter  | A01-A09    |
| C         | Compressor parameter  | C01-C04    |
| D         | Defrost parameter     | D01-D08    |
| E         | EEV parameter         | E01-E11    |
| F         | Fan parameter         | F01-F11    |
| H         | System parameter      | H01-H13    |
| P         | Water pump parameter  | P01-P09    |
| R         | Temp parameter        | R01-R28    |
| U         | Water flow parameter  | U01-U04    |
| S         | Switch state checking | S01-S13    |
| T         | Temp. checking        | T01-T12    |
| O         | Load output           | O01-O11    |

Integration is collecting the following

```json
{
    "Power": "0 - Off or 1 - On",
    "Mode": "HVAC mode (Off, Cool, Heat, Auto)",
    "Manual-mode": "Fan speed (Low, Auto)",
    "2074": "Unknown",
    "2075": "Unknown",
    "2076": "Unknown",
    "2077": "Unknown",
    "Set_Temp": "Set Target temperature",
    "1158": "Unknown",
    "1159": "Unknown",
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
    "F11": "Fan speed control temp."
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
    "T12": "Hot water temperature"
}
```

## Run API over CLI

### Requirements

- Python 3.10
- Python virtual environment
- Install all dependencies, using `pip install -r requirements.txt` command

### Environment variables

| Environment Variable | Type    | Default | Description                                                                                                               |
| -------------------- | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| Username             | String  | -       | Username used for Aqua Temp                                                                                               |
| Password             | String  | -       | Password used for Aqua Temp                                                                                               |
| DEBUG                | Boolean | False   | Setting to True will present DEBUG log level message while testing the code, False will set the minimum log level to INFO |

### Execution

Run file located in `tests/main.py`

## Troubleshooting

Before opening an issue, please provide logs related to the issue,
For debug log level, please add the following to your config.yaml

```yaml
logger:
  default: warning
  logs:
    custom_components.aqua_temp: debug
```

Please attach also diagnostic details of the integration, available in:
Settings -> Devices & Services -> Aqua Temp -> 3 dots menu -> Download diagnostics
