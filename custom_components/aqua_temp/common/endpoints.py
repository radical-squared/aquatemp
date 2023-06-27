class Endpoints:
    LOGIN = "app/user/login"
    USER_INFO = "app/user/getUserInfo"
    LIST_REGISTERED_DEVICES = "app/device/deviceList"
    LIST_SHARED_APPECT_DEVICES = "app/device/getMyAppectDeviceShareDataList"
    LIST_SHARED_TOBE_DEVICES = "app/device/getMyTobeAppectDeviceShareDataList"
    DEVICE_STATUS = "app/device/getDeviceStatus"
    DEVICE_CONTROL = "app/device/control"
    DEVICE_FAULT = "app/device/getFaultDataByDeviceCode"
    DEVICE_DATA = "app/device/getDataByCode"
    DEVICE_PASSTHROUGH_INSTRUCTION = "device/sendDevicePassthroughInstruction"


ENDPOINT_SUFFIX = {"cloudservice": ".json"}
