from src.aplustools import dummy


class TestDummy:
    def test_local(self):
        assert dummy.local_test()
