from aplustools.io import environment, loggers


class TestEnvironment:
    def test_print_system_info(self):
        sys_info = environment.get_system()
        print(f"Operating System: {sys_info.os}")
        print(f"OS Version: {sys_info.major_os_version}")
        print(f"CPU Architecture: {sys_info.cpu_arch}")
        print(f"CPU Brand: {sys_info.cpu_brand}")
        print(f"System Theme: {sys_info.get_system_theme()}")

    def test_system(self):
        try:
            system = environment.get_system()
            # _BaseSystem.send_notification(None, "Zenra", "Hello, how are you?", (), (), ())
            system.send_native_notification("Zenra,", "NOWAYY")
            print("System RAM", system.get_memory_info())
            print(f"Pc has been turned on since {int(system.get_uptime(),)} minutes")

            @environment.strict()
            class MyCls:
                _attr = "A"
            var = MyCls()._attr
        except AttributeError:
            print("Test completed successfully.")
            assert True
            return
        except Exception as e:
            print(f"Exception occurred {e}.")
            assert False
        print("Strict decorator not working.")
        assert False


class TestLoggers:
    def test_local(self):
        assert loggers.local_test()
