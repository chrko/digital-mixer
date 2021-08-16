from fractions import Fraction

from digimix.midi.generic_controls import ContinuousControlReadOnly


class TestContinuousControlReadOnly:
    def test_pick_up_value(self):
        cc = ContinuousControlReadOnly(behaviour=ContinuousControlReadOnly.Behaviour.PICK_UP)
        cc.value = 10
        assert cc.value == 0
        cc.value = 5
        assert cc.value == 5
        cc.value = 10
        assert cc.value == 10
        cc.value = 20
        assert cc.value == 10

    def test_jump_value(self):
        cc = ContinuousControlReadOnly(behaviour=ContinuousControlReadOnly.Behaviour.JUMP)
        cc.value = 10
        assert cc.value == 10
        cc.value = 5
        assert cc.value == 5
        cc.value = 10
        assert cc.value == 10
        cc.value = 20
        assert cc.value == 20

    def test_callback(self):
        def called_once(*_, **__):
            called_once.calls += 1
            assert called_once.calls == 1

        called_once.calls = 0

        cc = ContinuousControlReadOnly()
        cc.add_callback(called_once)
        cc.value = 5
        assert cc.value == 5
        cc.value = 5
        assert cc.value == 5
        cc.value = 5
        assert cc.value == 5

    def test_mapped_value(self):
        cc = ContinuousControlReadOnly(map_value_range=(-1, 1))
        assert cc.mapped_value == -1
        cc.value = 64
        assert cc.mapped_value == Fraction(1, 127)
        cc.value = 63
        assert cc.mapped_value == Fraction(-1, 127)
        cc.value = 127
        assert cc.mapped_value == 1
