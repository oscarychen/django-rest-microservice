from django.conf import settings
from django.test.signals import setting_changed

USER_SETTINGS = getattr(settings, "REST_FRAMEWORK_MICROSERVICE", None)

DEFAULTS = {
    "TOKEN_CUSTOM_USER_CLAIMS":  [],

}


class RestFrameworkMicroserviceSettings:
    def __init__(self, user_settings=None, defaults=None):
        self._user_settings = user_settings or {}
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "REST_FRAMEWORK_MICROSERVICE", {})
        return self._user_settings

    def __getattr__(self, attr):

        # check the setting is accepted
        if attr not in self.defaults:
            raise AttributeError(f"Invalid REST_FRAMEWORK_MICROSERVICE setting: {attr}")

        # get from user settings or default value
        try:
            val = self.user_settings[attr]
        except KeyError:
            val = self.defaults[attr]

        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


drf_stripe_settings = DrfStripeSettings(USER_SETTINGS, DEFAULTS)


def reload_rest_framework_microservice_settings(*args, **kwargs):
    print("Reloading rest_framework_microservice settings")
    setting = kwargs["setting"]
    if setting == "REST_FRAMEWORK_MICROSERVICE":
        drf_stripe_settings.reload()


setting_changed.connect(reload_rest_framework_microservice_settings)
