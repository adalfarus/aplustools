import typing

from src.aplustools.data import what_class, what_func, what_module, format_type
# from src.aplustools.package.argumint import analyze_function
from src.aplustools.package import timid
# import inspect
# from typing import Literal
#
#
# import typing as _ty
# import types
#
# class D:
#     def x(self, s: Literal["STR"]) -> None:
#         ...

# what_func(D.x)
# what_func(lambda x, y: None)
# print(analyze_function(D.x))
# what_module(fileio, type_names=True, show_method_origin=False, show_cls_origin=False)
what_module(timid, spaced_methods=False, type_names=True)
# for item in dir(fileio):
#     if item.startswith("_"):
#         continue
#     object_ = getattr(fileio, item)
#     if inspect.isclass(object_):
#         what_class(object_)
#     elif inspect.isfunction(object_):
#         what_func(object_)
#     else:
#         print(f"Unknown type '{object_}'")

exit()
def what_func(func: _ts.FunctionType, type_names: bool = True, show_method_origin: bool = False,
              print_def: bool = True) -> str:
    """
    Analyzes the passed function, formats it into a nice string and optionally prints it.

    :param func:
    :param type_names:
    :param show_method_origin:
    :param print_def:
    :return:
    """
    analysis = _analyze_function(func)

    def _get_type_name(t: _ty.Any) -> str | None:
        if hasattr(t, '__origin__') and t.__origin__ is _ty.Union or type(t) is _ty.Union and type(None) in t.__args__:  # type: ignore
            non_none_types = [arg for arg in t.__args__ if arg is not type(None)]
            return f"{t.__name__}[{', '.join(_get_type_name(arg) for arg in non_none_types)}]"  # type: ignore
        return t.__name__ if hasattr(t, '__name__') else (type(t).__name__ if t is not None else None)

    arguments_str = ''.join([f"{argument['name']}: "  # type: ignore 
                             f"{(_get_type_name(argument['type']) or type(argument['default']).__name__) if type_names else _get_type_name(argument['type']) or type(argument['default'])}"  # type: ignore 
                             f" = {argument['default']}, " for argument in analysis["arguments"]])[:-2]  # type: ignore
    origin = f"{func.__module__}." if show_method_origin else ""
    definition = f"{origin}{analysis['name']}({arguments_str}){(' -> ' + str((_get_type_name(analysis['return_type']) or type(analysis['return_type']).__name__) if type_names else analysis['return_type'])) if analysis['return_type'] is not None else ' -> None'}"
    if print_def:
        print(definition)
    return definition
