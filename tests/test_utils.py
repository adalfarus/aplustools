from aplustools.utils import genpass, imagetools, mappers


class TestGenpass:
    def test_local(self):
        assert genpass.local_test()
        
class TestImagetools:
    def test_local(self):
        assert imagetools.local_test()
        
class TestMappers:
    def test_local(self):
        assert mappers.local_test()
