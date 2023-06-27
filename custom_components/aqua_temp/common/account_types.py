from custom_components.aqua_temp.common.consts import PRODUCT_IDS
from custom_components.aqua_temp.common.endpoints import Endpoints
from homeassistant.backports.enum import StrEnum


class AccountTypeParam(StrEnum):
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


class AccountType(StrEnum):
    AquaTemp = "1"
    HiTemp = "2"
    AquaTempOld = "99"


ACCOUNT_TYPES = {
    str(AccountType.AquaTemp): {
        AccountTypeParam.URL: "https://cloud.linked-go.com:449/crmservice/api",
        AccountTypeParam.Username: "userName",
        AccountTypeParam.UserId: "userId",
        AccountTypeParam.Suffix: "",
        AccountTypeParam.ObjectResult: "objectResult",
        AccountTypeParam.KeepAlive: False,
        AccountTypeParam.ProductId: "productId",
        AccountTypeParam.ProductIds: "productIds",
        AccountTypeParam.PageIndex: "pageIndex",
        AccountTypeParam.PageSize: "pageSize",
        AccountTypeParam.ToUser: "toUser",
        AccountTypeParam.DeviceCode: "deviceCode",
        AccountTypeParam.ProtocalCodes: "protocalCodes",
        AccountTypeParam.ProtocolCode: "protocolCode",
    },
    str(AccountType.HiTemp): {
        AccountTypeParam.URL: "https://cloud.linked-go.com/cloudservice/api",
        AccountTypeParam.Username: "user_name",
        AccountTypeParam.UserId: "user_id",
        AccountTypeParam.Suffix: ".json",
        AccountTypeParam.ObjectResult: "object_result",
        AccountTypeParam.KeepAlive: True,
        AccountTypeParam.ProductId: "product_id",
        AccountTypeParam.ProductIds: "product_ids",
        AccountTypeParam.PageIndex: "page_index",
        AccountTypeParam.PageSize: "page_size",
        AccountTypeParam.ToUser: "to_user",
        AccountTypeParam.DeviceCode: "device_code",
        AccountTypeParam.ProtocalCodes: "protocal_codes",
        AccountTypeParam.ProtocolCode: "protocol_code",
    },
    str(AccountType.AquaTempOld): {
        AccountTypeParam.URL: "https://cloud.linked-go.com/cloudservice/api",
        AccountTypeParam.Username: "user_name",
        AccountTypeParam.UserId: "user_id",
        AccountTypeParam.Suffix: ".json",
        AccountTypeParam.ObjectResult: "object_result",
        AccountTypeParam.KeepAlive: True,
        AccountTypeParam.ProductId: "product_id",
        AccountTypeParam.ProductIds: "product_ids",
        AccountTypeParam.PageIndex: "page_index",
        AccountTypeParam.PageSize: "page_size",
        AccountTypeParam.ToUser: "to_user",
        AccountTypeParam.DeviceCode: "device_code",
        AccountTypeParam.ProtocalCodes: "protocal_codes",
        AccountTypeParam.ProtocolCode: "protocol_code",
    },
}

DEVICE_REQUEST_PARAMETERS = {
    AccountTypeParam.ProductIds: PRODUCT_IDS,
    AccountTypeParam.PageIndex: 1,
    AccountTypeParam.PageSize: 999,
}

DEVICE_LISTS = {
    Endpoints.ListRegisteredDevices: [
        AccountTypeParam.ProductIds,
        AccountTypeParam.PageIndex,
        AccountTypeParam.PageSize,
    ],
    Endpoints.ListSharedTobeDevices: [
        AccountTypeParam.ProductIds,
        AccountTypeParam.ToUser,
    ],
    Endpoints.ListSharedAppectDevices: [
        AccountTypeParam.ProductIds,
        AccountTypeParam.ToUser,
        AccountTypeParam.PageIndex,
        AccountTypeParam.PageSize,
    ],
}
