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
