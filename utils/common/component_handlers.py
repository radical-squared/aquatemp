from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    Platform,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)


class ComponentHandlers:
    def __init__(self):
        self._category_handlers = {
            "bar": self.get_sensor_bar,
            "frequency": self.get_sensor_frequency,
            "amper": self.get_sensor_amper,
            "temperature": self.get_sensor_temperature,
            "duration_min": self.get_sensor_duration_min,
            "duration_h": self.get_sensor_duration_h,
            "percentage": self.get_sensor_percentage,
            "rotation": self.get_sensor_rotation,
            "volt": self.get_sensor_volt,
        }

    def get_description(self, index, key, name, config):
        full_name = f"{name} [{key}]"

        data = self.get_sensor_default(key, full_name)

        for component in self._category_handlers:
            component_mapping = config.get(component, [])
            is_relevant = index in component_mapping

            if is_relevant:
                data = self._category_handlers[component](key, full_name)

        return data

    @staticmethod
    def get_sensor_bar(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": str(SensorDeviceClass.PRESSURE),
            "unit_of_measurement": str(UnitOfPressure.BAR)
        }

        return data

    @staticmethod
    def get_sensor_frequency(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": str(SensorDeviceClass.FREQUENCY),
            "unit_of_measurement": str(UnitOfFrequency.HERTZ)
        }

        return data

    @staticmethod
    def get_sensor_amper(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": str(SensorDeviceClass.CURRENT),
            "unit_of_measurement": str(UnitOfElectricCurrent.AMPERE)
        }

        return data

    @staticmethod
    def get_sensor_temperature(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": str(SensorDeviceClass.TEMPERATURE),
            "unit_of_measurement": str(UnitOfTemperature.CELSIUS)
        }

        return data

    @staticmethod
    def get_sensor_duration_min(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": str(SensorDeviceClass.DURATION),
            "unit_of_measurement": str(UnitOfTime.MINUTES)
        }

        return data

    @staticmethod
    def get_sensor_duration_h(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": str(SensorDeviceClass.DURATION),
            "unit_of_measurement": str(UnitOfTime.HOURS)
        }

        return data

    @staticmethod
    def get_sensor_percentage(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": None,
            "unit_of_measurement": "%"
        }

        return data

    @staticmethod
    def get_sensor_rotation(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": None,
            "unit_of_measurement": "r"
        }

        return data

    @staticmethod
    def get_sensor_volt(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": str(SensorDeviceClass.VOLTAGE),
            "unit_of_measurement": str(UnitOfElectricPotential.VOLT)
        }

        return data

    @staticmethod
    def get_sensor_default(parameter, name):
        data = {
            "key": parameter,
            "name": name,
            "platform": str(Platform.SENSOR),
            "device_class": None,
            "unit_of_measurement": None
        }

        return data
