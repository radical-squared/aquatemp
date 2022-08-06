# Home Assistant Aquatemp Heat Pump Climate Entity (custom component) 

This is Home Assistant's custom climate entity to control Aquatemp-compatible heat pumps through Aquatemp cloud API. It allows controlling temperature, HVAC mode (heat, cool, auto, off) and fan mode (low, auto). It also reports faults through entity attributes. Aquatemp's cloud protocol is based on dst6se's https://github.com/dst6se/aquatemp project.

### Home Assistant Setup   [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Install by adding custom repository to HACS or copy the directory to your custom_components folder, restart HA and then add the following to your configuration.yaml file:
```
climate:
  - platform: aquatemp
    name: aquatemp
    username: your_username
    password: your_password
    min_temp: 20
    max_temp: 35
    temperature_unit: C
    unique_id: my_aquatemp
    expose_codes: true
    attribute_map:
      T05: ambient_temperature
      T03: outlet_temperature
      T02: inlet_temperature
      T01: suction_temperature  
  ```
  
