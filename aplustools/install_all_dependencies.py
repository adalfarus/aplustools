import subprocess

def execute_python_command(arguments: list=None, run: bool=False, *args, **kwargs) -> subprocess.CompletedProcess[str]:
    if arguments == None: arguments = []
    log(' '.join([sys.executable] + arguments), LogType.DEBUG)
    if run: arguments.append("--run") # Added to remain consistent with executing in same python environment
    return subprocess.run([sys.executable] + arguments, *args, **kwargs)
    
for dep in ["requests==2.31.0", 
            "Pillow==10.1.0", 
            "bs4==4.12.2", 
            "datetime==5.2", 
            "duckduckgo_search==3.9.3", 
            "rich==13.7.0", 
            "pycryptodome==3.19.0"]
    execute_python_command(arguments=
               ["pip", "install", dep])
               
input("Done, press ENTER to exit ...")
    