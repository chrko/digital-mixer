from digimix.audio import GstAudio

# thanks to ndufresne for the hints

# https://gitlab.freedesktop.org/gstreamer/gst-plugins-base/-/blob/master/gst-libs/gst/audio/audio-channels.c#L58-87
default_channel_order = (
    GstAudio.AudioChannelPosition.FRONT_LEFT,
    GstAudio.AudioChannelPosition.FRONT_RIGHT,
    GstAudio.AudioChannelPosition.FRONT_CENTER,
    GstAudio.AudioChannelPosition.LFE1,
    GstAudio.AudioChannelPosition.REAR_LEFT,
    GstAudio.AudioChannelPosition.REAR_RIGHT,
    GstAudio.AudioChannelPosition.FRONT_LEFT_OF_CENTER,
    GstAudio.AudioChannelPosition.FRONT_RIGHT_OF_CENTER,
    GstAudio.AudioChannelPosition.REAR_CENTER,
    GstAudio.AudioChannelPosition.LFE2,
    GstAudio.AudioChannelPosition.SIDE_LEFT,
    GstAudio.AudioChannelPosition.SIDE_RIGHT,
    GstAudio.AudioChannelPosition.TOP_FRONT_LEFT,
    GstAudio.AudioChannelPosition.TOP_FRONT_RIGHT,
    GstAudio.AudioChannelPosition.TOP_FRONT_CENTER,
    GstAudio.AudioChannelPosition.TOP_CENTER,
    GstAudio.AudioChannelPosition.TOP_REAR_LEFT,
    GstAudio.AudioChannelPosition.TOP_REAR_RIGHT,
    GstAudio.AudioChannelPosition.TOP_SIDE_LEFT,
    GstAudio.AudioChannelPosition.TOP_SIDE_RIGHT,
    GstAudio.AudioChannelPosition.TOP_REAR_CENTER,
    GstAudio.AudioChannelPosition.BOTTOM_FRONT_CENTER,
    GstAudio.AudioChannelPosition.BOTTOM_FRONT_LEFT,
    GstAudio.AudioChannelPosition.BOTTOM_FRONT_RIGHT,
    GstAudio.AudioChannelPosition.WIDE_LEFT,
    GstAudio.AudioChannelPosition.WIDE_RIGHT,
    GstAudio.AudioChannelPosition.SURROUND_LEFT,
    GstAudio.AudioChannelPosition.SURROUND_RIGHT,
    GstAudio.AudioChannelPosition.INVALID
)
# https://gitlab.freedesktop.org/gstreamer/gst-plugins-good/-/blob/master/ext/jack/gstjackutil.c#L23-84
jack_default_positions = (
    (
        GstAudio.AudioChannelPosition.MONO,
    ),
    (
        GstAudio.AudioChannelPosition.FRONT_LEFT,
        GstAudio.AudioChannelPosition.FRONT_RIGHT,
    ),
    (
        GstAudio.AudioChannelPosition.FRONT_LEFT,
        GstAudio.AudioChannelPosition.FRONT_RIGHT,
        GstAudio.AudioChannelPosition.LFE1,
    ),
    (
        GstAudio.AudioChannelPosition.FRONT_LEFT,
        GstAudio.AudioChannelPosition.FRONT_RIGHT,
        GstAudio.AudioChannelPosition.REAR_LEFT,
        GstAudio.AudioChannelPosition.REAR_RIGHT,
    ),
    (
        GstAudio.AudioChannelPosition.FRONT_LEFT,
        GstAudio.AudioChannelPosition.FRONT_RIGHT,
        GstAudio.AudioChannelPosition.REAR_LEFT,
        GstAudio.AudioChannelPosition.REAR_RIGHT,
        GstAudio.AudioChannelPosition.FRONT_CENTER,
    ),
    (
        GstAudio.AudioChannelPosition.FRONT_LEFT,
        GstAudio.AudioChannelPosition.FRONT_RIGHT,
        GstAudio.AudioChannelPosition.REAR_LEFT,
        GstAudio.AudioChannelPosition.REAR_RIGHT,
        GstAudio.AudioChannelPosition.FRONT_CENTER,
        GstAudio.AudioChannelPosition.LFE1,
    ),
    (
        GstAudio.AudioChannelPosition.FRONT_LEFT,
        GstAudio.AudioChannelPosition.FRONT_RIGHT,
        GstAudio.AudioChannelPosition.REAR_LEFT,
        GstAudio.AudioChannelPosition.REAR_RIGHT,
        GstAudio.AudioChannelPosition.FRONT_CENTER,
        GstAudio.AudioChannelPosition.LFE1,
        GstAudio.AudioChannelPosition.REAR_CENTER,
    ),
    (
        GstAudio.AudioChannelPosition.FRONT_LEFT,
        GstAudio.AudioChannelPosition.FRONT_RIGHT,
        GstAudio.AudioChannelPosition.REAR_LEFT,
        GstAudio.AudioChannelPosition.REAR_RIGHT,
        GstAudio.AudioChannelPosition.FRONT_CENTER,
        GstAudio.AudioChannelPosition.LFE1,
        GstAudio.AudioChannelPosition.SIDE_LEFT,
        GstAudio.AudioChannelPosition.SIDE_RIGHT,
    ),
)

assert all(len(el) == i + 1 for i, el in enumerate(jack_default_positions))


def pos_in_default_channel_order(ch_pos):
    return default_channel_order.index(ch_pos)


def get_reorder_map(channel_positions):
    if len(set(channel_positions)) != len(channel_positions):
        raise ValueError()

    sorted_channels = tuple(sorted(channel_positions, key=pos_in_default_channel_order))

    return tuple(sorted_channels.index(ch) for ch in channel_positions)


def get_jack_channel_pos(channels, pos):
    if len(jack_default_positions) >= channels:
        return get_reorder_map(jack_default_positions[channels - 1])[pos]
    return pos
