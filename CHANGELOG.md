# Changelog

## v3.0.13

- Add Account Type drop-down to configuration (Aqua Temp [Android],Aqua Temp [iOS], Hitemp)
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
