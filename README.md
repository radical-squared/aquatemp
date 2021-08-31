# Home Assistant Aquatemp Heat Pump Climate Entity (custom component) 

This is Home Assistant's custom climate entity to control Aquatemp-compatible heat pumps through Aquatemp cloud API. It allows controlling temperature, HVAC mode (heat, cool, auto, off) and fan mode (low, auto). It also reports faults through entity attributes. Aquatemp's cloud protocol is based on dst6se's https://github.com/dst6se/aquatemp project.

### Home Assistant Setup
To install copy the directory to your custom_components folder, restart HA and then add the following to your configuration.yaml file:
```
climate:
  - platform: aquatemp
    name: aquatemp
    username: your_username
    password: your_password
    min_temp: 20
    max_temp: 35
    temperature_unit: C
  ```
  
