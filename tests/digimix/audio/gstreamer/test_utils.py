from digimix.audio.gstreamer.utils import escape_pipeline_description


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
