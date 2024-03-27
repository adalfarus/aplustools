import subprocess as _subprocess
import sys as _sys


class LazyModuleLoader:
    def __init__(self, module_name):
        self.module_name = module_name
        self.module = None

    def _load_module(self):
        if self.module is None:
            try:
                self.module = __import__(self.module_name, globals(), locals(), ['*'])
            except ImportError:
                raise ImportError("Optional module not installed. Please install it to use this feature.")
        return self.module

    def __repr__(self):
        if self.module is None:
            return f"<LazyModuleLoader for '{self.module_name}'>"
        else:
            return repr(self.module)

    def __getattr__(self, item):
        module = self._load_module()
        return getattr(module, item)

    def __dir__(self):
        self._load_module()
        return dir(self.module)


def _execute_python_command(arguments: list = None, *args, **kwargs) -> _subprocess.CompletedProcess[str]:
    if arguments is None:
        arguments = []
    print(' '.join([_sys.executable] + arguments))
    # Added to remain consistent with executing in the same python environment
    return _subprocess.run([_sys.executable] + arguments, *args, **kwargs)


def install_dependencies_lst(dependencies: list) -> bool:
    for dep in dependencies:
        try:
            proc = _execute_python_command(arguments=["-m", "pip", "install", dep])
            if proc.returncode != 0:
                raise
        except Exception as e:
            print("An error occurred:" + str(e))
            return False
        return True


def install_dependencies():
    success = install_dependencies_lst([])
    if not success:
        return
    print("Done, all possible dependencies for the package module installed ...")
