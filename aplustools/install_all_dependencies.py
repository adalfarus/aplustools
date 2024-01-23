print("placeholder")

def execute_python_command(arguments: list=None, run: bool=False, *args, **kwargs) -> CompletedProcess[str]:
    if arguments == None: arguments = []
    log(' '.join([sys.executable] + arguments), LogType.DEBUG)
    if run: arguments.append("--run") # Added to remain consistent with executing in same python environment
    return subprocess.run([sys.executable] + arguments, *args, **kwargs)
    
for dep in []:
    execute_python_command("pip", "install", dep)
    