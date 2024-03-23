from aplustools import execute_python_command, set_dir_to_ex
from aplustools.web import web_request


class TestDirectFunctions:
    def test_all(self):
        try:
            # set_dir_to_ex()  # Won't work
            execute_python_command(["--version"])
        except Exception as e:
            print(f"Exception occurred {e}")
            assert False
        else:
            assert True


class TestWebRequest:
    def test_local(self):
        assert web_request.local_test()
