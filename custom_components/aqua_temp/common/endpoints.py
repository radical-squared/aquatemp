class Endpoints:
    BASE_URL = "https://cloud.linked-go.com/cloudservice/api"
    # BASE_URL = "http://cloud.linked-go.com:84/cloudservice/api"

    LOGIN = "app/user/login.json"
    USER_INFO = "app/user/getUserInfo.json"
    LIST_REGISTERED_DEVICES = "app/device/deviceList.json"
    LIST_SHARED_APPECT_DEVICES = "app/device/getMyAppectDeviceShareDataList.json"
    LIST_SHARED_TOBE_DEVICES = "app/device/getMyTobeAppectDeviceShareDataList.json"
    DEVICE_STATUS = "app/device/getDeviceStatus.json"
    DEVICE_CONTROL = "app/device/control.json"
    DEVICE_FAULT = "app/device/getFaultDataByDeviceCode.json"
    DEVICE_DATA = "app/device/getDataByCode.json"
    DEVICE_PASSTHROUGH_INSTRUCTION = "device/sendDevicePassthroughInstruction.json"
