import platform
import subprocess
import os

try:
    import winreg
except ImportError:
    winreg = None  # winreg is not available on non-Windows platforms

class System:
    def __init__(self):
        self.os = self.get_os()
        self.os_version = self.get_os_version()
        self.cpu_arch = self.get_cpu_arch()
        self.cpu_brand = self.get_cpu_brand()
        # GPU information retrieval can be complex and platform-dependent
        # self.gpu_info = self.get_gpu_info()
        self.theme = self.get_system_theme()

    def get_os(self):
        """Get the name of the operating system."""
        return platform.system()

    def get_os_version(self):
        """Get the version of the operating system."""
        return platform.version()
    
    def get_major_os_version(self):
        return platform.release()

    def get_cpu_arch(self):
        """Get the architecture of the CPU (e.g., x86_64, ARM)."""
        return platform.machine()

    def get_cpu_brand(self):
        """Get the brand and model of the CPU."""
        if self.os == 'Windows':
            return platform.processor()
        elif self.os == 'Linux' or self.os == 'Darwin':
            command = "cat /proc/cpuinfo | grep 'model name' | uniq"
            return subprocess.check_output(command, shell=True).decode().split(': ')[1].strip()
        return "Unknown"

    # GPU information retrieval is more complex and may require third-party libraries or specific system commands

    def get_system_theme(self):
        if self.os == 'Windows':
            return self.get_windows_theme()
        elif self.os == 'Darwin':
            return self.get_macos_theme()
        elif self.os == 'Linux':
            return self.get_linux_theme()
        return "Unknown"

    def get_windows_theme(self):
        if not winreg:
            return None

        key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        value = 'AppsUseLightTheme'
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key)
            theme_value, _ = winreg.QueryValueEx(reg_key, value)
            winreg.CloseKey(reg_key)
            return 'Dark' if theme_value == 0 else 'Light'
        except Exception:
            return None

    def get_macos_theme(self):
        try:
            theme = subprocess.check_output("defaults read -g AppleInterfaceStyle", shell=True).decode().strip()
            return 'Dark' if theme == 'Dark' else 'Light'
        except subprocess.CalledProcessError:
            return 'Light'  # Default to Light since Dark mode is not set

    def get_linux_theme(self):
        # This method is very basic and might not work on all Linux distributions.
        # Linux theme detection can be very varied depending on the desktop environment.
        try:
            theme = subprocess.check_output("gsettings get org.gnome.desktop.interface gtk-theme", shell=True).decode().strip()
            return 'Dark' if 'dark' in theme.lower() else 'Light'
        except Exception:
            return None

def print_system_info():
    sys_info = System()
    print(f"Operating System: {sys_info.os}")
    print(f"OS Version: {sys_info.os_version}")
    print(f"CPU Architecture: {sys_info.cpu_arch}")
    print(f"CPU Brand: {sys_info.cpu_brand}")
    print(f"System Theme: {sys_info.theme}")
    
def local_test():
    print_system_info()

if __name__ == "__main__":
    local_test()
