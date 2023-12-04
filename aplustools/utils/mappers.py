# utils/mappers.py

def reverse_map(functions, input_value):
    return [func(input_value) for func in functions]
