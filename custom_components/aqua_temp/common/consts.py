from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import FAN_AUTO, FAN_LOW, HVACMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
)

from .endpoints import Endpoints
from .entity_descriptions import (
    AquaTempBinarySensorEntityDescription,
    AquaTempClimateEntityDescription,
    AquaTempEntityDescription,
    AquaTempSelectEntityDescription,
    AquaTempSensorEntityDescription,
)

DOMAIN = "aqua_temp"
DEFAULT_NAME = "Aqua Temp"
SIGNAL_AQUA_TEMP_DEVICE_NEW = f"signal_{DOMAIN}_device_new"

HTTP_HEADER_X_TOKEN = "x-token"

SUPPORTED_PRODUCT_ID = [
    "1132174963097280512",
    "1186904563333062656",
    "1158905952238313472",
    "1442284873216843776",
    "1548963836789501952",
]

DEVICE_REQUEST_PRODUCT_IDS = "product_ids"
DEVICE_REQUEST_PAGE_INDEX = "page_index"
DEVICE_REQUEST_PAGE_SIZE = "page_size"
DEVICE_REQUEST_TO_USER = "to_user"

DEVICE_CODE = "device_code"
PROTOCAL_CODES = "protocal_codes"

DEVICE_CONTROL_PARAM = "param"

DEVICE_CONTROL_PROTOCOL_CODE = "protocol_code"
DEVICE_CONTROL_VALUE = "value"

DEVICE_REQUEST_PARAMETERS = {
    DEVICE_REQUEST_PRODUCT_IDS: SUPPORTED_PRODUCT_ID,
    DEVICE_REQUEST_PAGE_INDEX: 1,
    DEVICE_REQUEST_PAGE_SIZE: 999,
}

DEVICE_LISTS = {
    Endpoints.LIST_REGISTERED_DEVICES: [
        DEVICE_REQUEST_PRODUCT_IDS,
        DEVICE_REQUEST_PAGE_INDEX,
        DEVICE_REQUEST_PAGE_SIZE,
    ],
    Endpoints.LIST_SHARED_TOBE_DEVICES: [
        DEVICE_REQUEST_PRODUCT_IDS,
        DEVICE_REQUEST_TO_USER,
    ],
    Endpoints.LIST_SHARED_APPECT_DEVICES: [
        DEVICE_REQUEST_PRODUCT_IDS,
        DEVICE_REQUEST_TO_USER,
        DEVICE_REQUEST_PAGE_INDEX,
        DEVICE_REQUEST_PAGE_SIZE,
    ],
}

MODE_TEMPERATURE_COOL = "0"
MODE_TEMPERATURE_HEAT = "1"
MODE_TEMPERATURE_AUTO = "2"

HVAC_MODE_MAPPING = {
    HVACMode.OFF: None,
    HVACMode.COOL: MODE_TEMPERATURE_COOL,
    HVACMode.HEAT: MODE_TEMPERATURE_HEAT,
    HVACMode.AUTO: MODE_TEMPERATURE_AUTO,
}

HVAC_MODE_TARGET_TEMPERATURE = {
    HVACMode.OFF: None,
    HVACMode.COOL: "R01",
    HVACMode.HEAT: "R02",
    HVACMode.AUTO: "R03",
}

MANUAL_MUTE_AUTO = "0"
MANUAL_MUTE_LOW = "1"

FAN_MODE_MAPPING = {FAN_AUTO: MANUAL_MUTE_AUTO, FAN_LOW: MANUAL_MUTE_LOW}

POWER_MODE_OFF = "0"
POWER_MODE_ON = "1"

HEADERS = {"Content-Type": "application/json; charset=utf-8"}

DATA_ITEM_DEVICES = "device"
DATA_ITEM_LOGIN_DETAILS = "login-details"
DATA_ITEM_CONFIG = "configuration"

ALL_ENTITIES = [
    AquaTempSelectEntityDescription(
        key="temperature_unit",
        name="Temperature Unit",
        category="Status parameters",
        options=[UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT],
        entity_category=EntityCategory.CONFIG,
        is_protocol_code=False,
    ),
    AquaTempBinarySensorEntityDescription(
        key="is_fault",
        name="Fault",
        category="Status parameters",
        on_value=POWER_MODE_ON,
        is_protocol_code=False,
        device_class=BinarySensorDeviceClass.PROBLEM,
        attributes=["fault"],
    ),
    AquaTempBinarySensorEntityDescription(
        key="device_status",
        name="Status",
        category="Status parameters",
        on_value="ONLINE",
        is_protocol_code=False,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    AquaTempBinarySensorEntityDescription(
        key="Power",
        name="Power",
        category="Control parameters",
        on_value=POWER_MODE_ON,
        device_class=BinarySensorDeviceClass.POWER,
    ),
    AquaTempClimateEntityDescription(
        key="Mode",
        name="HVAC Mode",
        category="Control parameters",
        fan_modes=list(FAN_MODE_MAPPING.keys()),
        hvac_modes=list(HVAC_MODE_MAPPING.keys()),
        minimum_temperature_keys={HVACMode.COOL: "R08", HVACMode.HEAT: "R10"},
        maximum_temperature_keys={HVACMode.COOL: "R09", HVACMode.HEAT: "R11"},
    ),
    AquaTempEntityDescription(
        key="Manual-mute", name="Fan Mode", category="Control parameters"
    ),
    AquaTempEntityDescription(key="2074", name="2074", category="Control parameters"),
    AquaTempEntityDescription(key="2075", name="2075", category="Control parameters"),
    AquaTempEntityDescription(key="2076", name="2076", category="Control parameters"),
    AquaTempEntityDescription(key="2077", name="2077", category="Control parameters"),
    AquaTempEntityDescription(
        key="Set_Temp", name="Set Temperature", category="Control parameters"
    ),
    AquaTempEntityDescription(key="1158", name="1158", category="Control parameters"),
    AquaTempEntityDescription(key="1159", name="1159", category="Control parameters"),
    AquaTempEntityDescription(
        key="/01",
        name="Whether enable system 1 high pressure switch",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/02",
        name="Whether enable system 2 high pressure switch",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/03",
        name="Whether enable system 1 low pressure switch",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/04",
        name="Whether enable system 2 low pressure switch",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/05",
        name="Whether enable phase monitor protection",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/06",
        name="Whether enable water flow protection",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/07",
        name="Whether enable electrical heater Overload protection",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/08",
        name="Whether enable system 1 overload protection",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/09",
        name="Whether enable system 2 overload protection",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/10",
        name="Whether enable remote on/off switch",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="/11", name="Whether enable system protect", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/12", name="Whether enable Outlet probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/13", name="Whether enable Coil 1 probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/14", name="Whether enable Coil 2 probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/15", name="Whether enable Ambient probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/16", name="Whether enable deice 1 probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/17", name="Whether enable deice 2 probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/18", name="Whether enable Suction 1 probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/19", name="Whether enable Suction 2 probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/20", name="Whether enable exhaust 1 probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/21", name="Whether enable exhaust 2 probe", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/22", name="Whether enable ΔT1 protect", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/23", name="Whether enable Cooling mode", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/24", name="Whether enable Economic heating", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/25", name="Whether enable AUTO mode", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/26", name="Whether enable Heating mode", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/27", name="Whether enable High demand", category="Hardware parameter"
    ),
    AquaTempEntityDescription(
        key="/28",
        name="Whether enable heat recovery temperature",
        category="Hardware parameter",
    ),
    AquaTempEntityDescription(
        key="A01",
        name="High pressure alarm time delay",
        category="Protection parameter",
    ),
    AquaTempEntityDescription(
        key="A02", name="Low pressure alarm time delay", category="Protection parameter"
    ),
    AquaTempEntityDescription(
        key="A03", name="Stop unit air temperature", category="Protection parameter"
    ),
    AquaTempEntityDescription(
        key="A04",
        name="Antifreeze setting temperature",
        category="Protection parameter",
    ),
    AquaTempEntityDescription(
        key="A05",
        name="Antifreeze differential protection",
        category="Protection parameter",
    ),
    AquaTempEntityDescription(
        key="A06",
        name="Discharge temp. protection setting",
        category="Protection parameter",
    ),
    AquaTempEntityDescription(
        key="A07",
        name="Discharge temp. differential protection",
        category="Protection parameter",
    ),
    AquaTempEntityDescription(
        key="A08",
        name="Inlet/Out differential protection setting value",
        category="Protection parameter",
    ),
    AquaTempEntityDescription(
        key="A09",
        name="Start spraying air temperature",
        category="Protection parameter",
    ),
    AquaTempEntityDescription(
        key="C01", name="Minimum on time", category="Compressor parameter"
    ),
    AquaTempEntityDescription(
        key="C02", name="Minimum off time", category="Compressor parameter"
    ),
    AquaTempEntityDescription(
        key="C03",
        name="Delay between starts of the 2 compressors",
        category="Compressor parameter",
    ),
    AquaTempEntityDescription(
        key="C04", name="Rotation", category="Compressor parameter"
    ),
    AquaTempEntityDescription(
        key="D01", name="Start defrosting temperature", category="Defrost parameter"
    ),
    AquaTempEntityDescription(
        key="D02", name="End defrost temperature", category="Defrost parameter"
    ),
    AquaTempEntityDescription(
        key="D03", name="defrosting cycle", category="Defrost parameter"
    ),
    AquaTempEntityDescription(
        key="D04", name="Maximum defrosting time", category="Defrost parameter"
    ),
    AquaTempEntityDescription(
        key="D05", name="Minimum defrosting time", category="Defrost parameter"
    ),
    AquaTempEntityDescription(
        key="D06", name="Defrost mode", category="Defrost parameter"
    ),
    AquaTempEntityDescription(
        key="D07", name="Defrost heater control", category="Defrost parameter"
    ),
    AquaTempEntityDescription(
        key="D08", name="Defrost AUTO set", category="Defrost parameter"
    ),
    AquaTempEntityDescription(key="E01", name="EEV 1 mode", category="EEV parameter"),
    AquaTempEntityDescription(key="E02", name="Super heat 1", category="EEV parameter"),
    AquaTempEntityDescription(
        key="E03", name="Initial place 1", category="EEV parameter"
    ),
    AquaTempEntityDescription(key="E04", name="EEV 2 mode", category="EEV parameter"),
    AquaTempEntityDescription(key="E05", name="Super heat 2", category="EEV parameter"),
    AquaTempEntityDescription(
        key="E06", name="Initial place 2", category="EEV parameter"
    ),
    AquaTempEntityDescription(
        key="E07", name="Minimum place", category="EEV parameter"
    ),
    AquaTempEntityDescription(
        key="E08", name="Defrost place", category="EEV parameter"
    ),
    AquaTempEntityDescription(
        key="E09", name="Cooling place", category="EEV parameter"
    ),
    AquaTempEntityDescription(key="E10", name="Low exhaust", category="EEV parameter"),
    AquaTempEntityDescription(key="E11", name="High exhaust", category="EEV parameter"),
    AquaTempEntityDescription(
        key="F01", name="Fan parameter", category="Fan parameter"
    ),
    AquaTempEntityDescription(
        key="F02",
        name="Coil temperature in high speed fan mode (Cooling)",
        category="Fan parameter",
    ),
    AquaTempEntityDescription(
        key="F03",
        name="Coil temperature in low speed fan mode (Cooling)",
        category="Fan parameter",
    ),
    AquaTempEntityDescription(
        key="F04",
        name="Coil temperature when the fan stop (Cooling)",
        category="Fan parameter",
    ),
    AquaTempEntityDescription(
        key="F05",
        name="Coil temperature in high speed fan mode (Heating)",
        category="Fan parameter",
    ),
    AquaTempEntityDescription(
        key="F06",
        name="Coil temperature in low speed fan mode (Heating)",
        category="Fan parameter",
    ),
    AquaTempEntityDescription(
        key="F07",
        name="Coil temperature when the fan stop (Heating)",
        category="Fan parameter",
    ),
    AquaTempEntityDescription(
        key="F08", name="Fan start low speed running time", category="Fan parameter"
    ),
    AquaTempEntityDescription(
        key="F09", name="Fan stop low speed running time", category="Fan parameter"
    ),
    AquaTempEntityDescription(key="F10", name="Fan quantity", category="Fan parameter"),
    AquaTempEntityDescription(
        key="F11", name="Fan speed control temp.", category="Fan parameter"
    ),
    AquaTempEntityDescription(
        key="H01", name="Automatic restarting", category="System parameter"
    ),
    AquaTempEntityDescription(
        key="H02", name="System quantity", category="System parameter"
    ),
    AquaTempEntityDescription(
        key="H03", name="4-way valve polarity", category="System parameter"
    ),
    AquaTempEntityDescription(
        key="H04", name="4-way valve control", category="System parameter"
    ),
    AquaTempEntityDescription(key="H05", name="Model", category="System parameter"),
    AquaTempEntityDescription(key="H06", name="Type", category="System parameter"),
    AquaTempEntityDescription(key="H07", name="Class", category="System parameter"),
    AquaTempEntityDescription(
        key="H08", name="Capacity Control", category="System parameter"
    ),
    AquaTempEntityDescription(
        key="H09", name="Coil sensor function", category="System parameter"
    ),
    AquaTempEntityDescription(
        key="H10", name="Physical address", category="System parameter"
    ),
    AquaTempEntityDescription(key="H11", name="Baud rate", category="System parameter"),
    AquaTempEntityDescription(
        key="H12", name="Parity bit", category="System parameter"
    ),
    AquaTempEntityDescription(key="H13", name="Stop bit", category="System parameter"),
    AquaTempEntityDescription(
        key="P01", name="Water pump mode", category="Water pump parameter"
    ),
    AquaTempEntityDescription(
        key="P02", name="Water pump running cycle", category="Water pump parameter"
    ),
    AquaTempEntityDescription(
        key="P03", name="Water pump running time", category="Water pump parameter"
    ),
    AquaTempEntityDescription(
        key="P04",
        name="Delay in switching on the compressor after switching on the pump",
        category="Water pump parameter",
    ),
    AquaTempEntityDescription(
        key="P05", name="Filter", category="Water pump parameter"
    ),
    AquaTempEntityDescription(
        key="P06", name="Start filter 1", category="Water pump parameter"
    ),
    AquaTempEntityDescription(
        key="P07", name="Stop filter 1", category="Water pump parameter"
    ),
    AquaTempEntityDescription(
        key="P08", name="Start filter 2", category="Water pump parameter"
    ),
    AquaTempEntityDescription(
        key="P09", name="Stop filter 2", category="Water pump parameter"
    ),
    AquaTempSensorEntityDescription(
        key="R01",
        name="Inlet water setting temperature (cooling)",
        category="Temp parameter",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempSensorEntityDescription(
        key="R02",
        name="Inlet water setting temperature (Heating)",
        category="Temp parameter",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempSensorEntityDescription(
        key="R03",
        name="Target setting temperature (Auto mode)",
        category="Temp parameter",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempEntityDescription(
        key="R04", name="Cooling differential", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R05", name="Cooling stop differential", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R06", name="Heating differential", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R07", name="Heating stop differential", category="Temp parameter"
    ),
    AquaTempSensorEntityDescription(
        key="R08",
        name="Minimum set point in Cooling",
        category="Temp parameter",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempSensorEntityDescription(
        key="R09",
        name="Maximum Cooling set point",
        category="Temp parameter",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempSensorEntityDescription(
        key="R10",
        name="Minimum Heating set point",
        category="Temp parameter",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempSensorEntityDescription(
        key="R11",
        name="Maximum Heating set point",
        category="Temp parameter",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempEntityDescription(
        key="R12", name="Electrical ΔT6", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R13", name="Electrical Ambient", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R14", name="Electrical Delay", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R15", name="Electrical force", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R16", name="Compensation", category="Temp parameter"
    ),
    AquaTempEntityDescription(key="R17", name="Maximum ΔT7", category="Temp parameter"),
    AquaTempEntityDescription(
        key="R18", name="Cooling compensation constant", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R19",
        name="Cooling compensation start air temperature",
        category="Temp parameter",
    ),
    AquaTempEntityDescription(
        key="R20",
        name="Heating compensation start air temperature",
        category="Temp parameter",
    ),
    AquaTempEntityDescription(
        key="R21", name="Whether enable heat recovery", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R22",
        name="The target temperature Of heat recovery",
        category="Temp parameter",
    ),
    AquaTempEntityDescription(
        key="R23",
        name="Temperature differential of heat recovery",
        category="Temp parameter",
    ),
    AquaTempEntityDescription(
        key="R24", name="Temperature to stop heat recovery", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R25",
        name="Temperature differential to stop heat recovery",
        category="Temp parameter",
    ),
    AquaTempEntityDescription(
        key="R26", name="Electric heater mode", category="Temp parameter"
    ),
    AquaTempEntityDescription(
        key="R27",
        name="Ambient temperature to start up antifreezing heater",
        category="Temp parameter",
    ),
    AquaTempEntityDescription(
        key="R28",
        name="Temperature differential to stop antifreezing heater",
        category="Temp parameter",
    ),
    AquaTempEntityDescription(
        key="U01", name="Flow meter", category="Water flow parameter"
    ),
    AquaTempEntityDescription(key="U02", name="Pulse", category="Water flow parameter"),
    AquaTempEntityDescription(
        key="U03", name="Flow protect", category="Water flow parameter"
    ),
    AquaTempEntityDescription(
        key="U04", name="Flow alarm", category="Water flow parameter"
    ),
    AquaTempEntityDescription(
        key="S01", name="System1 HP", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S02", name="System2 HP", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S03", name="System1 LP", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S04", name="System2 LP", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S05", name="Phase monitor", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S06", name="Water Flow switch", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S07", name="Electrical heater overload", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S08", name="COMP1 overload", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S09", name="COMP2 overload", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S10", name="On/Off switch", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S11", name="Mode switch", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S12", name="System protect", category="Switch state checking"
    ),
    AquaTempEntityDescription(
        key="S13", name="Water flow", category="Switch state checking"
    ),
    AquaTempSensorEntityDescription(
        key="T01",
        name="Suction temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T02",
        name="Inlet water temp.",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T03",
        name="Outlet water temp",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T04",
        name="Coil temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T05",
        name="Ambient temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T06",
        name="Antifreeze 1 temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T07",
        name="Antifreeze 2 temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T08",
        name="Suction 1 temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T09",
        name="Suction 2 temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T10",
        name="Exhaust 1 temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T11",
        name="Exhaust 2 temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempSensorEntityDescription(
        key="T12",
        name="Hot water temperature",
        category="Temp. checking",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AquaTempEntityDescription(key="T14", name="None", category="Temp. checking"),
    AquaTempEntityDescription(
        key="O01", name="Compressor 1 output", category="Load output"
    ),
    AquaTempEntityDescription(
        key="O02", name="Compressor 2 output", category="Load output"
    ),
    AquaTempEntityDescription(
        key="O03", name="Fan output (High speed)", category="Load output"
    ),
    AquaTempEntityDescription(
        key="O04", name="Fan output (Low speed)", category="Load output"
    ),
    AquaTempEntityDescription(
        key="O05", name="Circulate pump output", category="Load output"
    ),
    AquaTempSensorEntityDescription(
        key="O06",
        name="4-way valve output",
        category="Load output",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempEntityDescription(
        key="O07", name="Heat element output", category="Load output"
    ),
    AquaTempEntityDescription(key="O08", name="Alarm output", category="Load output"),
    AquaTempEntityDescription(
        key="O09", name="Spray valve output", category="Load output"
    ),
    AquaTempSensorEntityDescription(
        key="O10",
        name="Electronic Expansion valve 1 output",
        category="Load output",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AquaTempSensorEntityDescription(
        key="O11",
        name="Electronic Expansion valve 2 output",
        category="Load output",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]
