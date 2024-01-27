import subprocess
import sys

def install_dependencies():
    def execute_python_command(arguments: list = None, *args, **kwargs) -> subprocess.CompletedProcess[str]:
        if arguments == None: arguments = []
        print(' '.join([sys.executable] + arguments))
        # Added to remain consistent with executing in same python environment
        return subprocess.run([sys.executable] + arguments, *args, **kwargs)
    for dep in ["requests==2.31.0",
                "PySide6==6.5.1.1"]:
       try:
          proc = execute_python_command(arguments=
                         ["-m", "pip", "install", dep])
          if proc.returncode != 0:
             raise
       except Exception as e:
          print("An error occurred:" + str(e))

    print("Done, all possible dependencies for the data module installed ...")
    