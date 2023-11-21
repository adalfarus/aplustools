import winreg

class System:
    def __init__(self):
        self.os = self.get_os()
        self.ver = self.get_os_version()
        self.theme = self.get_os_theme()
        
    def get_os():
        return "win"
        
    def get_os_version():
        pass
        
    def get_os_theme():
        pass
    
    def get_cpu_arch():
        pass # x64 ARM

    def get_cpu_build():
        pass # AMD, Intel
    
    def get_gpu_arch():
        pass

    def get_gpu_build():
        pass
        
def pl():
    pass
