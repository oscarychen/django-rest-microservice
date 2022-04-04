from django.conf import settings
from django.test.signals import setting_changed
from django.utils.module_loading import import_string

USER_SETTINGS = getattr(settings, "REST_FRAMEWORK_MICROSERVICE", None)

DEFAULTS = {
    "REFRESH_COOKIE_NAME": "refresh_cookie",
    "REFRESH_COOKIE_PATH": "/auth",
    "IDP": {
        "PROVIDER": "aws",
        "REGION": "us-west-2",
        "USER_POOL": "us-west-2_abcdefg",
        "CLIENT_ID": "abcdefg",
    },
    "CUSTOM_TOKEN_USER_ATTRIBUTES": [],
    "CUSTOM_TOKEN_CALLABLE_ATTRIBUTES": [],
    "COOKIE_SALT": "extra",
    "USER_SERIALIZER_CLASS": None,
    "USER_MODEL_UUID_FIELD": None,
}

IMPORT_STRINGS = [
    'USER_SERIALIZER_CLASS'
]


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import '%s' for API setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class RestFrameworkMicroserviceSettings:
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        self._user_settings = user_settings or {}
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "REST_FRAMEWORK_MICROSERVICE", {})
        return self._user_settings

    def __getattr__(self, attr):

        # check the setting is accepted attribute
        if attr not in self.defaults:
            raise AttributeError(f"Invalid REST_FRAMEWORK_MICROSERVICE setting: {attr}")

        # get from user settings or default value
        try:
            val = self.user_settings[attr]
        except KeyError:
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


rest_microservice_settings = RestFrameworkMicroserviceSettings(USER_SETTINGS, DEFAULTS)


def reload_rest_framework_microservice_settings(*args, **kwargs):
    print("Reloading rest_framework_microservice settings")
    setting = kwargs["setting"]
    if setting == "REST_FRAMEWORK_MICROSERVICE":
        rest_microservice_settings.reload()


setting_changed.connect(reload_rest_framework_microservice_settings)
