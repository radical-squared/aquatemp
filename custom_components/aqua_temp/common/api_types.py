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


class APIType(StrEnum):
    AquaTemp = "1"
    HiTemp = "2"
    AquaTempOld = "99"


API_TYPES = {
    str(APIType.AquaTemp): {
        APIParam.URL: "https://cloud.linked-go.com:449/crmservice/api",
        APIParam.Username: "userName",
        APIParam.UserId: "userId",
        APIParam.Suffix: "",
        APIParam.ObjectResult: "objectResult",
        APIParam.KeepAlive: False,
        APIParam.ProductId: "productId",
        APIParam.ProductIds: "productIds",
        APIParam.PageIndex: "pageIndex",
        APIParam.PageSize: "pageSize",
        APIParam.ToUser: "toUser",
        APIParam.DeviceCode: "deviceCode",
        APIParam.ProtocalCodes: "protocalCodes",
        APIParam.ProtocolCode: "protocolCode",
    },
    str(APIType.HiTemp): {
        APIParam.URL: "https://cloud.linked-go.com/cloudservice/api",
        APIParam.Username: "user_name",
        APIParam.UserId: "user_id",
        APIParam.Suffix: ".json",
        APIParam.ObjectResult: "object_result",
        APIParam.KeepAlive: True,
        APIParam.ProductId: "product_id",
        APIParam.ProductIds: "product_ids",
        APIParam.PageIndex: "page_index",
        APIParam.PageSize: "page_size",
        APIParam.ToUser: "to_user",
        APIParam.DeviceCode: "device_code",
        APIParam.ProtocalCodes: "protocal_codes",
        APIParam.ProtocolCode: "protocol_code",
    },
    str(APIType.AquaTempOld): {
        APIParam.URL: "https://cloud.linked-go.com/cloudservice/api",
        APIParam.Username: "user_name",
        APIParam.UserId: "user_id",
        APIParam.Suffix: ".json",
        APIParam.ObjectResult: "object_result",
        APIParam.KeepAlive: True,
        APIParam.ProductId: "product_id",
        APIParam.ProductIds: "product_ids",
        APIParam.PageIndex: "page_index",
        APIParam.PageSize: "page_size",
        APIParam.ToUser: "to_user",
        APIParam.DeviceCode: "device_code",
        APIParam.ProtocalCodes: "protocal_codes",
        APIParam.ProtocolCode: "protocol_code",
    },
}

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
