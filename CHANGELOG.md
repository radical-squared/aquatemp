# Changelog

## v3.0.3

- Fix setting HVAC mode
- Support shared devices
- Support multiple product IDs

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
