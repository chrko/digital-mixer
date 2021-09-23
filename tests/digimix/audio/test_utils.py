import math

import pytest

from digimix.audio.utils import (
    amplitude_to_db,
    db_to_amplitude,
    escape_pipeline_description,
    linspace,
    make_discrete_to_continuous,
)


def test_db_to_amplitude():
    assert 0 == db_to_amplitude(-math.inf)
    assert -10 == amplitude_to_db(db_to_amplitude(-10))
    assert -20 == amplitude_to_db(db_to_amplitude(-20))
    assert -30 == amplitude_to_db(db_to_amplitude(-30))


def test_linspace():
    assert linspace(1, 127, 9) == (1., 16.75, 32.5, 48.25, 64., 79.75, 95.5, 111.25, 127.)


@pytest.mark.parametrize("cached", [True, False])
def test_make_discrete_to_continuous_defaults(cached):
    f = make_discrete_to_continuous(cached=cached)
    assert f(0) == -math.inf
    assert f(1) == -98.35
    assert f(127) == 0
    assert f(126) == -0.2756


@pytest.mark.parametrize("cached", [True, False])
def test_make_discrete_to_continuous_input(cached):
    f = make_discrete_to_continuous(
        x=(-128, 127),
        y=(0, 10, 50, 100, 120, 140, 200),
        edge_points=(),
        cached=cached,
    )
    assert f(-128) == 0
    assert f(127) == 200
    assert f(0) == 100.2
    assert f(50) == 123.8
    assert f(-50) == 43.41


def test_escape_pipeline_description():
    print(escape_pipeline_description("""
    bin.(
        name=bin-test
        jackaudiosrc
            connect=0
            name=jas-test
            client_name=test
        ! capsfilter
            name=jas_caps-test
            caps=audio/x-raw,channels=3,channel-mask=(bitmask)0x000
        ! deinterleave
            name=jas_deinter-test

        bin.(
            name=bin-test-music
            interleave
                name=jas_inter-test-music
            ! capsfilter
                name=queue-jas_inter_caps-test-music
                caps=audio/x-raw,channels=2,channel-mask=(bitmask)0x3
            ! tee
                name=src-music

            jas_deinter-test.src_0
            ! capsfilter
                name=jas_deinter-test-src_0
                caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x1
            ! queue
                name=jas_pre-inter-test-music_0
                max-size-time=3000000000
            ! jas_inter-test-music.sink_0

            jas_deinter-test.src_1
            ! capsfilter
                name=jas_deinter-test-src_1
                caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x2
            ! queue
                name=queue-jas_pre-inter-test-music_1
                max-size-time=3000000000
            ! jas_inter-test-music.sink_1
        )

        bin.(
            name=bin-test-mic
            jas_deinter-test.src_2
            ! capsfilter
                name=jas_deinter_caps-test-src_2
                caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x0
            ! tee
                name=src-mic
        )
    )

    audiomixer name=mix

    src-music.
    ! audiopanorama
    ! mix.
    src-mic.
    ! audiopanorama
    ! mix.

    mix. ! jackaudiosink connect=0 name=jacksink client-name=GstSink
    """))
