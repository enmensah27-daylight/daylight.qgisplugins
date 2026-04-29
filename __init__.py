def classFactory(iface):
    from .copy_fields import CopyFieldsPlugin
    return CopyFieldsPlugin(iface)