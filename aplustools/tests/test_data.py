from aplustools.data import database, imagetools, updaters, faker


class TestUpdaters:
    def test_get_last_version(self):
        assert updaters.gitupdater.get_latest_version("adalfarus", "unicode-writer") == ("0.0.2", "0.0.2")
        
    def test_local(self):
        assert updaters.local_test()


class TestDatabase:
    def test_local(self):
        assert database.local_test()


class TestFaker:
    def test_local(self):
        assert faker.local_test()


class TestImagetools:
    def test_local(self):
        assert imagetools.local_test()
