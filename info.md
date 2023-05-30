# Home Assistant Aquatemp Heat Pump Climate Entity (custom component)

This is Home Assistant's custom climate entity to control AquaTemp-compatible heat pumps through AquaTemp cloud API.
It allows controlling temperature, HVAC mode (heat, cool, auto, off) and fan mode (low, auto).
It also reports temperatures, status, faults through binary sensors and sensors.
AquaTemp's cloud protocol is based on dst6se's https://github.com/dst6se/aquatemp project with additional functionality.

[Changelog](https://github.com/radical-squared/aquatemp/blob/master/CHANGELOG.md)

## How to

#### Requirements

- Account for AquaTemp

#### Switching from 1.x/2.x to 3.x

Requires complete deletion of integration and reinstall after restart HA

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

| Entity Name                                                | Parameter        | Platform      | Protocol Code? |
| ---------------------------------------------------------- | ---------------- | ------------- | -------------- |
| {HA Device Name} Temperature Unit                          | temperature_unit | select        | False          |
| {HA Device Name} Fault                                     | is_fault         | binary_sensor | False          |
| {HA Device Name} Status                                    | device_status    | binary_sensor | False          |
| {HA Device Name} Power                                     | Power            | binary_sensor | True           |
| {HA Device Name} HVAC Mode                                 | Mode             | climate       | True           |
| {HA Device Name} Inlet water setting temperature (cooling) | R01              | sensor        | True           |
| {HA Device Name} Inlet water setting temperature (Heating) | R02              | sensor        | True           |
| {HA Device Name} Target setting temperature (Auto mode)    | R03              | sensor        | True           |
| {HA Device Name} Minimum set point in Cooling              | R08              | sensor        | True           |
| {HA Device Name} Maximum Cooling set point                 | R09              | sensor        | True           |
| {HA Device Name} Minimum Heating set point                 | R10              | sensor        | True           |
| {HA Device Name} Maximum Heating set point                 | R11              | sensor        | True           |
| {HA Device Name} Suction temperature                       | T01              | sensor        | True           |
| {HA Device Name} Inlet water temp.                         | T02              | sensor        | True           |
| {HA Device Name} Outlet water temp                         | T03              | sensor        | True           |
| {HA Device Name} Coil temperature                          | T04              | sensor        | True           |
| {HA Device Name} Ambient temperature                       | T05              | sensor        | True           |
| {HA Device Name} Antifreeze 1 temperature                  | T06              | sensor        | True           |
| {HA Device Name} Antifreeze 2 temperature                  | T07              | sensor        | True           |
| {HA Device Name} Suction 1 temperature                     | T08              | sensor        | True           |
| {HA Device Name} Suction 2 temperature                     | T09              | sensor        | True           |
| {HA Device Name} Exhaust 1 temperature                     | T10              | sensor        | True           |
| {HA Device Name} Exhaust 2 temperature                     | T11              | sensor        | True           |
| {HA Device Name} Hot water temperature                     | T12              | sensor        | True           |
| {HA Device Name} 4-way valve output                        | O06              | sensor        | True           |
| {HA Device Name} Electronic Expansion valve 1 output       | O10              | sensor        | True           |
| {HA Device Name} Electronic Expansion valve 2 output       | O11              | sensor        | True           |

[Protocol Codes](https://github.com/radical-squared/aquatemp/blob/master/PROTOCOL_CODES.md)

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
