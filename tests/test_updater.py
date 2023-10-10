from aplustools.updaters import gitupdater

def test_get_last_version():
    assert gitupdater.get_latest_version("adalfarus", "unicode-writer") == "0.0.2", "0.0.2"
