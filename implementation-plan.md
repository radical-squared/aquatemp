# Aqua Temp power and mode support

## Evidence

- The climate entity advertises `TURN_ON` and `TURN_OFF`, but implements neither
  `async_turn_on` nor `async_turn_off`.
- The API layer already has the required protocol operation: `set_hvac_mode(...,
  HVACMode.OFF)` sends the configured power-off value, and setting another HVAC
  mode first sends the configured power-on value.
- Mode options are mapping-driven. The default and product `1442284873216843776`
  mappings expose `cool`, `heat`, and `auto`; product `1245226668902080512`
  exposes only `heat`. Live validation identified this controller as product
  `1245226668902080512`. Selecting Heat sent power code `mo6` although the
  mapping specifies `MO6`, then sent target-temperature code `R01` with a null
  value.
- A read-only raw API probe while the controller is on returned `Power=1` with
  an enumerated `0-1` range, while `MO6` is empty and has no type or range.
  The product mapping must use `Power` for both state and control.
- With the corrected mapping deployed, the live data refresh returns
  `Power="1"` and `mode_real="0"`, but the climate entity still calculates
  `off`. A targeted debug record shows `Power` is correctly calculated as on;
  the integration never requests `mode_real`, so it maps its missing value to
  the configured off state.

## Tasks

- [x] Add explicit climate `async_turn_on` and `async_turn_off` handlers.
  Turning on must select a valid configured non-off HVAC mode, preferring the
  last reported valid mode and then the first supported mode. Turning off must
  use the existing API power-off path.
- [x] Keep the public mode list mapping-driven. Do not claim modes that the
  controller mapping does not support.
- [ ] Add focused tests for turn-off and turn-on delegation, including a
  heat-only mapping and a multi-mode mapping. No climate test harness exists
  in this checkout.
- [x] Run the available static syntax checks and review the diff. `py_compile`
  and `git diff --check` pass; Black is not installed in this environment.
- [x] Preserve protocol-code casing in the power-control request.
- [x] Omit the target-temperature parameter from a mode command when no target
  temperature is available.
- [x] Deploy the command-path fixes and verify that Aqua Temp loads after the
  live Home Assistant restart.
- [ ] Correct product `1245226668902080512` to use `Power`, then deploy and
  test power off and on from Home Assistant.
- [x] Add and use a power-state calculation debug record to resolve the
  remaining climate-state mismatch.
- [x] Ensure the API fetch list includes every state protocol code referenced
  by the product mapping, including mode, power, target temperature, fan, and
  HVAC temperature bounds.

## Live validation required

- [x] Identify the controller product ID and installed integration version.
- [x] Deploy the explicit Home Assistant power handlers and restart Home
  Assistant.
- [ ] Test Climate `Turn off` and `Turn on` after the command-path fixes.
