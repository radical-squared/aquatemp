# Hot-water automation plan

- [x] Confirm the tank-average temperature entity and existing automation layout.
- [x] Add a 06:00 automation that sets `climate.e8fdf8a49500` to `heat`.
- [x] Add a 15:00 automation that turns the climate entity off.
- [x] Add a recovery automation for 15:00–23:00: start heating below 45 °C and stop at or above 57 °C.
- [x] Add a 23:00 switch-off to end the recovery window, including after a Home Assistant restart.
- [x] Validate YAML, deploy `automations.yaml`, restart Home Assistant, and confirm the automations are loaded.

## Behavioural details

- The scheduled 15:00 off action takes precedence. The first recovery evaluation runs at 15:01; it turns the system back on only when the tank average is below 45 °C.
- The recovery automation also evaluates on Home Assistant startup so it resumes correctly after a restart within the 15:00–23:00 window.
- It switches the system off immediately when the average reaches 57 °C or at 23:00, whichever comes first.

# Controller operating-mode selector plan

- [x] Capture the live controller values from the Aqua Temp cloud API: Intelligent `0`, Eco `2`, Hybrid `3`, Fast Heating `4`.
- [x] Add the profile mapping for product `1245226668902080512`.
- [x] Add a dedicated Home Assistant select entity that reads `mode_real` and writes the selected profile value.
- [x] Keep the climate entity limited to power and temperature behaviour.
- [x] Treat each recognised controller profile as active `heat` for the existing climate entity.
- [x] Validate the implementation, deploy it to Home Assistant, and verify the new select state and options.

# Native climate presets and Essentials controls plan

- [x] Expose the four verified controller profiles as `preset_modes` on the Hot water climate entity.
- [x] Route climate preset changes through the existing verified `mode_real` control path.
- [x] Retain the separate Controller Mode select entity for backwards compatibility, without putting it on the dashboard.
- [x] Add Essentials Water Heater controls below the graph in this order: Heat/Off, preset selector, fan controls.
- [x] Validate, deploy the integration and storage dashboard, then verify the native climate preset state and card configuration.

# Essentials average-temperature controls plan

- [x] Remove the Water Heater history graph from Essentials.
- [x] Keep the full-width Water Heater climate controls with Heat/Off, preset, then fan controls.
- [x] Display `sensor.water_heater_tank_average_temperature` as the Water Heater temperature in the controls area.
- [x] Preserve the selected controller preset when the climate entity or hot-water automations turn heating on.
- [x] Validate and deploy the storage dashboard, then verify the live card configuration.
