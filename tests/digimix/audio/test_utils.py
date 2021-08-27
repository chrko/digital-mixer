from digimix.audio.utils import stereo_to_mono


def test_stereo_to_mono():
    bin_desc = "jackaudiosrc connect=0 client-name=StereoTest\n"
    bin_desc += " ! "
    bin_desc += stereo_to_mono('test', -6)
    bin_desc += " ! "
    bin_desc += "jackaudiosink connect=0 client-name=MonoSum"

    print(' '.join(bin_desc.replace("\n", " ").split()))
