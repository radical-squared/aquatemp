# Home Assistant Aquatemp Heat Pump sensor (Custom component) 

This is Home Assistant's custom sensor that retrieves data from Aquatemp cloud and makes it available in Home Assistant. It creates sensor.aquatemp entity that shows heat pump's online/offline status, as well as water inlet and outlet temperatures and is_fault status as attributes. Aquatemp's cloud protocol is based on dst6se's https://github.com/dst6se/aquatemp project.

### Home Assistant Setup
To install copy the directory to your custom_components folder, restart HA and then add the following to your configuration.yaml file:
```
sensor:
  - platform: aquatemp
    name: aquatemp
    username: your_username
    password: your_password
    
  - platform: template
    sensors:
      pool_temperature:
        unit_of_measurement: "C"
        value_template: "{{state_attr('sensor.aquatemp','in')}}"
  ```
  
