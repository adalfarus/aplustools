import sys


def pype_command():
    """Pype"""
    if len(sys.argv) > 1:
        expression = ' '.join(sys.argv[1:])
        try:
            result = eval(expression)
            print(result)
        except Exception as e:
            print(f"Error: {e}")
    else:
        expression = input("Enter Python expression: ")
        try:
            result = eval(expression)
            print(result)
        except Exception as e:
            print(f"Error: {e}")


def upype_command():
    """Unified pype"""
    if len(sys.argv) > 1:
        # Join the arguments and split by ';'
        code = ' '.join(sys.argv[1:]).split(';')
        try:
            for line in code:
                # Strip leading and trailing whitespace and execute each line
                exec(line.strip())
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Enter Python code (type 'end' on a new line to finish):")
        lines = []
        while True:
            line = input("... ")
            if line == 'end':
                break
            lines.append(line)

        try:
            exec('\n'.join(lines))
        except Exception as e:
            print(f"Error: {e}")
