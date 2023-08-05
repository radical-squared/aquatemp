# Changelog

## v3.0.25

### Breaking Change

Password store format changed, up until now, password saved as the hash being send to the API,

To allow the enhanced functionality added, to edit Credentials and API Type, the password is now being saved encrypted and decrypted in 2 flows:

1. Edit integration details
2. On startup (hashed and sent to the API)

As result of that process, you need to re-setup the integration.

### Changes

- Add to set up configuration form new field of title to define the name of the integration
- Add edit integration details - Title, Credentials and API Type
- Refactor component initialization code to simplify process

## v3.0.24

- Add missing configuration for API param 'error_code'

## v3.0.23

- Fix APIParam class, caused corrupted data on component creation and error code handling

## v3.0.22

- Fix binary sensor state evaluation

## v3.0.21

- Fix vacuum entity name
- Fix add integration (config) error handling

## v3.0.20

- Fix error handling when performing an action
- Optimize components loading

## v3.0.19

- Fix error handling when fetch data failed

## v3.0.18

- Add more parameters to API type configuration
- Extract model for HA DeviceInfo from API
- Add translation key to all components with name ready for translation

## v3.0.17

- Fix logic to extract protocol codes
- Fix mappings of product ID 1442284873216843776

## v3.0.16

- Optimize error handling for fetch device data

## v3.0.15

- Add log to update device

## v3.0.14

- Fix for the new capability of AquaTemp of single app to login, will re-login on every attempt to perform action / refresh
- Add new binary sensor of `API Status` represents whether the API is authenticated (logged in) or not

## v3.0.13

- Add API Type drop-down to configuration (Aqua Temp, Hitemp, Aqua Temp [=<1.5.8])
- Update authentication process

## v3.0.12

- Fix config flow, API manager constructor requires three parameters but only two are passed when creating it

## v3.0.11

- Per device's product ID parameters support

## v3.0.10

- Handling expired token error (401) more gracefully (re-login)

## v3.0.9

- Add support for product ID `1245226668902080512` [#25](https://github.com/radical-squared/aquatemp/issues/25)

## v3.0.8

- Fix missing `Off` mode for climate

## v3.0.7

- Improve support for devices of product ID `1442284873216843776`

## v3.0.6

- Fix device's empty values as `None` handling

## v3.0.5

- Set device's empty values as `None`

## v3.0.4

- Add device discovery for new devices without need to reload integration
- Fix integration reload issue
- Entities code clean up
- API stabilization after timeout
- Fix target temperature parameter mapping (Heat, Cool and Auto)
- Fix parameter mapping for P01 (Water pump mode)

## v3.0.3

- Fix setting HVAC mode
- Support shared devices
- Support multiple product IDs, Solution provided by [sjtrny](https://github.com/sjtrny) for issue [#25](https://github.com/radical-squared/aquatemp/issues/25)

## v3.0.2

- Fix configuration saving, without credentials
- Fix socket timeouts
- Add `suggested_unit_of_measurement=UnitOfElectricPotential.VOLT` to sensors of `SensorDeviceClass.VOLTAGE`
- Fix token clean-up
- Code clean up for entities
- HVAC Mode Mapping in v3.0.1 is mixed up [#29](https://github.com/radical-squared/aquatemp/issues/29)
- Block API operations if initial login failed

## v3.0.1

- Refactor entity's creation (using EntityDescription)
- Mapped all protocol codes to `EntityDescription`
- Add more entities (updated list in README)
- Create [Protocol Codes](https://github.com/radical-squared/aquatemp/blob/master/PROTOCOL_CODES.md) document
- Fix `climate` HVAC Modes

## v3.0.0

- Major refactor to the code - Breaking changes
- Configuration is available only from UI
- Supports multiple accounts (different credentials)
- Supports multiple devices (different devices on the same account)
- Add centralized `DataUpdateCoordinator` to communicate with the API and post updates to HA components
- Set minimum and maximum temperature based on the current HVAC mode relevant for the device (from API)
- Add `diagnostic` component to output data from API and configuration for troubleshooting (replacing the need for extra codes attributes)
- Add `binary_sensor` components for Power (Is on), Status (Is online) and Fault (Has fault)
- Add `select` component for choosing the Temperature Unit (C/F)
- Add `sensor` components for each of the temperature reading (T01-T03)
- Simplified `climate` component to include just its functionality without additional attributes (moved to dedicated components)
- Add mapping of more Protocol Codes (Parameters) for later support of more sensors/binary_sensors
