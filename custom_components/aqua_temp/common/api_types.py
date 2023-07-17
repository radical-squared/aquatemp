from custom_components.aqua_temp.common.consts import PRODUCT_IDS
from custom_components.aqua_temp.common.endpoints import Endpoints
from homeassistant.backports.enum import StrEnum


class APIParam(StrEnum):
    URL = "url"
    Username = "user_name"
    UserId = "user_id"
    Suffix = "suffix"
    ObjectResult = "object_result"
    KeepAlive = "keep_alive"
    ProductId = "product_id"
    ProductIds = "product_ids"
    PageIndex = "page_index"
    PageSize = "page_size"
    ToUser = "to_user"
    DeviceCode = "device_code"
    ProtocalCodes = "protocal_codes"
    ProtocolCode = "protocol_code"
    IsFault = "is_fault"
    ErrorMessage = "error_msg"
    ErrorCode = "error_code"
    Nickname = "device_nick_name"
    DeviceId = "device_id"
    CustomModel = "cust_model"


class APIType(StrEnum):
    AquaTemp = "aqua_temp"
    HiTemp = "hi_temp"
    AquaTempOld = "aqua_temp_old"


API_TYPE_LEGACY = {
    "1": APIType.AquaTemp,
    "2": APIType.HiTemp,
    "99": APIType.AquaTempOld,
}

API_TYPES = [str(t) for t in list(API_TYPE_LEGACY.values())]

DEVICE_REQUEST_PARAMETERS = {
    APIParam.ProductIds: PRODUCT_IDS,
    APIParam.PageIndex: 1,
    APIParam.PageSize: 999,
}

DEVICE_LISTS = {
    Endpoints.ListRegisteredDevices: [
        APIParam.ProductIds,
        APIParam.PageIndex,
        APIParam.PageSize,
    ],
    Endpoints.ListSharedTobeDevices: [
        APIParam.ProductIds,
        APIParam.ToUser,
    ],
    Endpoints.ListSharedAppectDevices: [
        APIParam.ProductIds,
        APIParam.ToUser,
        APIParam.PageIndex,
        APIParam.PageSize,
    ],
}
