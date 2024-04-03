from aplustools.package import timid


class TestTimid:
    def test_local(self):
        assert timid.local_test()
