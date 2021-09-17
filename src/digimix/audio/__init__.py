import gi

gi.require_version('GLib', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstAudio', '1.0')

# noinspection PyUnresolvedReferences
from gi.repository import GLib, Gst, GstAudio

minGst = (1, 18)

Gst.init([])
if Gst.version() < minGst:
    raise Exception('GStreamer version', Gst.version(), 'is too old, at least', minGst, 'is required')
