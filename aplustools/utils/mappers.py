# utils/mappers.py
def reverse_map(functions, *args, **kwargs):
    return [func(*args, **kwargs) for func in functions]

# Implement map with generator like arguments?


def local_test():
    try:
        reverse_map([print, print], "Hello World")
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    else:
        print("Test completed successfully.")
        return True


if __name__ == "__main__":
    local_test()
