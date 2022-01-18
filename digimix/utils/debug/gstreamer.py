# based on https://github.com/voc/voctomix/blob/3156f3546890e6ae8d379df17e5cc718eee14b15/vocto/debug.py

import logging
import os

from digimix.audio import Gst

log = logging.getLogger(__name__)


def gst_generate_dot(pipeline, name):
    if "GST_DEBUG_DUMP_DOT_DIR" in os.environ:
        dotfile = os.path.join(os.environ["GST_DEBUG_DUMP_DOT_DIR"], "%s.dot" % name)
        log.debug("Generating DOT image of pipeline '{name}' into '{file}'".format(name=name, file=dotfile))
        Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails(15), name)


gst_log_messages_lastmessage = None
gst_log_messages_lastlevel = None
gst_log_messages_repeat = 0


def gst_log_messages(level):
    gst_log = logging.getLogger("Gst")

    def log(level, msg):
        if level == Gst.DebugLevel.WARNING:
            gst_log.warning(msg)
        if level == Gst.DebugLevel.FIXME:
            gst_log.warning(msg)
        elif level == Gst.DebugLevel.ERROR:
            gst_log.error(msg)
        elif level == Gst.DebugLevel.INFO:
            gst_log.info(msg)
        elif level == Gst.DebugLevel.DEBUG:
            gst_log.debug(msg)

    def log_function(category, level, file, function, line, object, message, *user_data):
        global gst_log_messages_lastmessage, gst_log_messages_lastlevel, gst_log_messages_repeat

        msg = message.get()
        if gst_log_messages_lastmessage != msg:
            if gst_log_messages_repeat > 2:
                log(
                    gst_log_messages_lastlevel,
                    "%s [REPEATING %d TIMES]" % (gst_log_messages_lastmessage, gst_log_messages_repeat),
                )

            gst_log_messages_lastmessage = msg
            gst_log_messages_repeat = 0
            gst_log_messages_lastlevel = level
            log(
                level,
                "%s: %s (in function %s() in file %s:%d)" % (object.name if object else "", msg, function, file, line),
            )
        else:
            gst_log_messages_repeat += 1

    Gst.debug_remove_log_function(None)
    Gst.debug_add_log_function(log_function, None)
    Gst.debug_set_default_threshold(level)
    Gst.debug_set_active(True)
