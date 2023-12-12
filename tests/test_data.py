from aplustools.data import database, updaters


class TestUpdaters:
    def test_get_last_version(self):
        assert updaters.gitupdater.get_latest_version(None, "adalfarus", "unicode-writer") == ("0.0.2", "0.0.2")
        
    def test_local(self):
        assert updaters.local_test()
        
class TestDatabase:
    def test_local(self):
        assert database.local_test()
