from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _


def deprecated_property(property_name, instead_property_name):
    assert property_name != instead_property_name

    def getter(self):
        user_system_log.warn(_(
            "\"{}\" is deprecated, please use \"{}\" instead, check the document for more information"
        ).format(property_name, instead_property_name))
        return getattr(self, instead_property_name)
    return property(getter)
