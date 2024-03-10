from aplustools.utils import genpass, mappers, dummy, hasher


class TestGenpass:
    def test_local(self):
        assert genpass.local_test()


class TestMappers:
    def test_local(self):
        assert mappers.local_test()


class TestDummy:
    def test_local(self):
        assert dummy.local_test()


class TestHasher:
    def test_local(self):
        assert hasher.local_test()
