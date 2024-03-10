from aplustools.package import timid, lazy_loader


class TestTimid:
    def test_local(self):
        assert timid.local_test()


class TestLazyLoader:
    def test_local(self):
        assert lazy_loader.local_test()
