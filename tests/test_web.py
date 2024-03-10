from aplustools.web import new_webtools, webtools


class TestNewWebtools:
    def test_local(self):
        assert new_webtools.local_test() # Doens't do anything yet


class TestWebtools:
    def test_local(self):
        assert webtools.local_test()
