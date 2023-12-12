# utils/mappers.py

class EmptyType:
    pass

def reverse_map(functions, input_value=EmptyType()):
    if type(input_value) == EmptyType:
        return [func() for func in functions]
    return [func(input_value) for func in functions]

# Implement map with generator like arguments?

def local_test():
    try:
        reverse_map([print, print], "Hello World")
    except Exception as e:
        print(f"Exception occured {e}.")
        return False
    else:
        print("Test completed successfully.")
        return True

if __name__ == "__main__":
    local_test()
