import subprocess
import sys

def install_all_dependencies():
    def execute_python_command(arguments: list = None, *args, **kwargs) -> subprocess.CompletedProcess[str]:
        if arguments == None: arguments = []
        print(' '.join([sys.executable] + arguments))
        # Added to remain consistent with executing in same python environment
        return subprocess.run([sys.executable] + arguments, *args, **kwargs)
    for dep in ["requests==2.31.0",
                "Pillow==10.2.0",
                "BeautifulSoup4==4.12.3",
                "datetime==5.4",
                "duckduckgo_search==3.9.3",
                "rich==13.7.0",
                "pycryptodome==3.19.0"]:
       try:
          proc = execute_python_command(arguments=
                         ["-m", "pip", "install", dep])
          if proc.returncode != 0:
             raise
       except Exception as e:
          print("An error occurred:" + str(e))

    print("Done, all possible dependencies installed ...")
    