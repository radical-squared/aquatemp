import voluptuous as vol
from voluptuous import Schema

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector

from ..common.api_types import API_TYPE_LEGACY, API_TYPES, APIType
from ..common.consts import CONF_API_TYPE, CONF_TITLE, DEFAULT_NAME

DATA_KEYS = [CONF_USERNAME, CONF_PASSWORD]


class ConfigData:
    _username: str | None
    _password: str | None
    _api_type: str | None

    def __init__(self):
        self._username = None
        self._password = None
        self._api_type = None

    @property
    def username(self) -> str:
        username = self._username

        return username

    @property
    def password(self) -> str:
        password = self._password

        return password

    @property
    def api_type(self) -> str:
        api_type = self._api_type

        return api_type

    def update(self, data: dict):
        self._password = data.get(CONF_PASSWORD)
        self._username = data.get(CONF_USERNAME)

        api_type = data.get(CONF_API_TYPE, str(APIType.AquaTempOld))

        if api_type in API_TYPE_LEGACY:
            api_type = str(API_TYPE_LEGACY.get(api_type))

        self._api_type = api_type

    def to_dict(self):
        obj = {
            CONF_USERNAME: self.username,
        }

        return obj

    def __repr__(self):
        to_string = f"{self.to_dict()}"

        return to_string

    @staticmethod
    def default_schema(user_input: dict | None) -> Schema:
        if user_input is None:
            user_input = {}

        new_user_input = {
            vol.Required(
                CONF_TITLE, default=user_input.get(CONF_TITLE, DEFAULT_NAME)
            ): str,
            vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME)): str,
            vol.Required(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD)): str,
            vol.Required(
                CONF_API_TYPE, default=user_input.get(CONF_API_TYPE)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=API_TYPES,
                    translation_key=CONF_API_TYPE,
                )
            ),
        }

        schema = vol.Schema(new_user_input)

        return schema
