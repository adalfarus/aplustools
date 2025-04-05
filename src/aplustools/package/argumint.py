"""TBA"""
from argparse import ArgumentParser as _ArgumentParser
import sys as _sys

from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


def analyze_function(function: _ts.FunctionType) -> dict[str, list[_ty.Any] | str | None]:
    """
    Analyzes a given function's signature and docstring, returning a structured summary of its
    arguments, including default values, types, keyword-only flags, documentation hints, and
    choices for `Literal`-type arguments. Also extracts information on `*args`, `**kwargs`,
    and the return type.

    Args:
        function (types.FunctionType): The function to analyze.

    Returns:
        dict: A dictionary containing the following keys:
            - "name" (str): The name of the function.
            - "doc" (str): The function's docstring.
            - "arguments" (List[Dict[str, Union[str, None]]]): Details of each argument:
                - "name" (str): The argument's name.
                - "default" (Any or None): The default value, if provided.
                - "choices" (List[Any] or []): Options for `Literal` type hints, if applicable.
                - "type" (Any or None): The argument's type hint.
                - "doc_help" (str): The extracted docstring help for the argument.
                - "kwarg_only" (bool): True if the argument is keyword-only.
            - "has_*args" (bool): True if the function accepts variable positional arguments.
            - "has_**kwargs" (bool): True if the function accepts variable keyword arguments.
            - "return_type" (Any or None): The function's return type hint.
            - "return_choices" (List[Any] or []): Options for `Literal` type hints for the return type, if applicable.
            - "return_doc_help" (str): The extracted docstring help for the return type.
    """
    name = function.__name__
    arg_count = (function.__code__.co_argcount
                 + function.__code__.co_kwonlyargcount
                 + function.__code__.co_posonlyargcount)
    argument_names = list(function.__code__.co_varnames[:arg_count] or ())
    has_args = (function.__code__.co_flags & 0b0100) == 4
    has_kwargs = (function.__code__.co_flags & 0b1000) == 8
    defaults = list(function.__defaults__ or ())
    if function.__kwdefaults__ is not None:
        defaults.extend(list(function.__kwdefaults__.values()))
    defaults.extend([None] * (len(argument_names) - len(defaults)))
    types = function.__annotations__ or {}
    docstring = function.__doc__ or ""
    type_hints = _ty.get_type_hints(function)

    pos_argcount = function.__code__.co_argcount  # After which i we have kwarg only
    if has_args:
        argument_names.insert(pos_argcount, "args")
        defaults.insert(pos_argcount, None)
        pos_argcount += 1
    if has_kwargs:
        argument_names.append("kwargs")
        defaults.append(None)
    argument_names.append("return")
    defaults.append(None)

    result = {"name": name, "doc": docstring, "arguments": [],
              "has_*args": has_args, "has_**kwargs": has_kwargs,
              "return_type": function.__annotations__.get("return"),
              "return_choices": [], "return_doc_help": ""}
    for i, (argument_name, default) in enumerate(zip(argument_names, defaults)):
        argument_start = docstring.find(argument_name)
        help_str, choices = "", []
        if argument_start != -1:
            help_start = argument_start + len(argument_name)  # Where argument_name ends in docstring
            next_line = argument_start + docstring[argument_start:].find("\n")
            help_str = docstring[help_start:next_line].strip(": \n\t")
        if argument_name == "return":
            type_hint = result["return_type"]
            if getattr(type_hint, "__origin__", None) is _ty.Literal:
                choices = type_hint.__args__
            result["return_choices"] = choices
            result["return_doc_help"] = help_str
            continue
        type_hint = type_hints.get(argument_name)
        if getattr(type_hint, "__origin__", None) is _ty.Literal:
            choices = type_hint.__args__
        result["arguments"].append({"name": argument_name, "default": default,
                                    "choices": choices, "type": types.get(argument_name),
                                    "doc_help": help_str, "kwarg_only": True if i >= pos_argcount else False})
    return result


class ArgumentParsingError(Exception):
    """Exception raised when an error occurs during argument parsing.

    This exception is used to indicate issues when parsing command-line arguments.
    It includes a message and an index to indicate where the error occurred, helping
    users or developers identify the issue in the input command.

    Attributes:
        index (int): The position in the argument list where the error was detected.
    """

    def __init__(self, message: str, index: int) -> None:
        super().__init__(message)
        self.index: int = index


class EndPoint:
    """Represents the endpoint of a trace from an argument structure object.

    The `EndPoint` class serves as a container for functions associated with
    a particular argument path, providing a way to call the function with
    predefined arguments and keyword arguments.

    Attributes:
        analysis (dict): Dictionary containing analysis data of the function's
            arguments, such as names and types, generated by `analyze_function`.
        _arg_index (dict): A mapping of argument names to their indices, allowing
            quick lookup of argument positions by name.
        _function (_ts.FunctionType): The actual function associated with this endpoint,
            which will be called when the endpoint is invoked.
    """

    def __init__(self, function: _ts.FunctionType) -> None:
        self.analysis: dict[str, list[_ty.Any] | str | None] = analyze_function(function)
        self._arg_index: dict[str, int] = {arg["name"]: i for i, arg in enumerate(self.analysis["arguments"])}
        self._function: _ts.FunctionType = function

    def call(self, *args, **kwargs) -> None:
        """Executes the internal function using the specified arguments.

        This method forwards all positional and keyword arguments to the stored
        function, allowing flexible invocation from various contexts.

        Args:
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
        """
        self._function(*args, **kwargs)

    def __repr__(self) -> str:
        args = [f'{key}: {self.analysis["arguments"][index]}' for (key, index) in self._arg_index.items()]
        return f"Endpoint(arguments={args})"


class ArgStructBuilder:
    """A utility class for constructing and managing a hierarchical argument structure.

    `ArgStructBuilder` allows users to build a nested dictionary structure that
    represents CLI commands and their subcommands. The resulting structure can be
    used in CLI parsers or for other command-line interfaces.

    Attributes:
        _commands (dict): The command structure dictionary, storing commands and
            subcommands with their respective mappings.
    """

    def __init__(self) -> None:
        self._commands: dict[str, dict | str] = {}

    def add_command(self, command: str, subcommands: dict | None = None) -> None:
        """Adds a top-level command with optional subcommands.

        Args:
            command (str): The main command to add to the structure.
            subcommands (Optional[dict], optional): Dictionary of subcommands,
                if applicable. If not provided, an empty dictionary is assigned.
        """
        if subcommands is None:
            subcommands = {}
        self._commands[command] = subcommands

    def add_subcommand(self, parent: str, subcommand: str) -> None:
        """Adds a subcommand under an existing top-level command.

        If the parent command does not exist, raises a `ValueError`.

        Args:
            parent (str): The parent command under which to add the subcommand.
            subcommand (str): The subcommand to add within the parent command.

        Raises:
            ValueError: If the parent command does not exist or is incompatible
                with having subcommands.
        """
        if parent not in self._commands:
            raise ValueError(f"Command '{parent}' not found.")
        if isinstance(self._commands[parent], dict):
            self._commands[parent][subcommand] = {}
        else:
            raise ValueError(f"Command '{parent}' cannot have subcommands.")

    def add_nested_command(self, parent: str, command: str, subcommand: str | dict | None) -> None:
        """Adds a nested command within a command structure hierarchy.

        Navigates to the specified parent path in the command structure, allowing
        creation of complex, multi-level command hierarchies.

        Args:
            parent (str): Dot-separated string representing the parent command path.
            command (str): The command to add within the specified parent path.
            subcommand (Optional[str | dict]): Structure for the subcommand. If
                `None`, an empty dictionary is used.

        Raises:
            ValueError: If the specified parent path is not valid.
        """
        if subcommand is None:
            subcommand = {}

        # Navigate to the correct parent level
        parts = parent.split('.')
        current_level = self._commands
        for part in parts:
            if part not in current_level or not isinstance(current_level[part], dict):
                raise ValueError(f"Command '{parent}' not found or is not a valid parent.")
            current_level = current_level[part]

        if isinstance(subcommand, str):
            current_level[command] = {subcommand: {}}
        else:
            current_level[command] = subcommand

    def get_structure(self) -> dict[str, dict | str]:
        """Retrieves the full command structure dictionary.

        Returns:
            dict: The dictionary representing all commands and subcommands,
            which can be used directly by other classes or modules for parsing.
        """
        return self._commands


_A = _ty.TypeVar('_A')


class Argumint:
    """A command-line argument parser that uses structured arguments and endpoints.

    Argumint is designed to parse CLI arguments using a predefined argument structure.
    It allows users to define and manage argument paths, replace the argument structure,
    and execute endpoints based on parsed arguments.

    Attributes:
        default_endpoint (EndPoint): The default endpoint to call if a path cannot be resolved.
        _arg_struct (dict): The dictionary representing the current argument structure.
        _endpoints (dict): A mapping of argument paths to endpoint functions.
    """

    def __init__(self, default_endpoint: EndPoint, arg_struct: dict[str, dict | str]) -> None:
        self.default_endpoint: EndPoint = default_endpoint
        self._arg_struct: dict[str, dict | str] = arg_struct
        self._endpoints: dict[str, EndPoint] = {}

    @staticmethod
    def _error(i: int, command_string: str) -> None:
        """Displays a caret (`^`) pointing to an error in the command string.

        Args:
            i (int): Index in the command string where the error occurred.
            command_string (str): The command string with the error.
        """
        print(f"{command_string}\n{' ' * i + '^'}")

    @staticmethod
    def _lst_error(i: int, arg_i: int, command_lst: list[str], do_exit: bool = False) -> None:
        """Displays an error caret in a list of command arguments.

        This method calculates the error position in a CLI argument list, displaying
        a caret to indicate where the error was found. Optionally, it can exit
        the program.

        Args:
            i (int): Index of the problematic argument in the list.
            arg_i (int): Position within the argument string to place the caret.
            command_lst (list[str]): List of command-line arguments.
            do_exit (bool, optional): If True, exits the program. Defaults to False.
        """
        length = sum(len(item) for item in command_lst[:i]) + i
        print(' '.join(command_lst) + "\n" +
              " " * (length + arg_i) + "^")
        if do_exit:
            _sys.exit(1)

    def _check_path(self, path: str, overwrite_pre_args: dict | None = None) -> bool:
        """Verifies if a specified path exists within the argument structure.

        This method traverses the structure to confirm whether each segment of the
        path is valid and points to an existing command or subcommand.

        Args:
            path (str): The dot-separated path to check within the argument structure.
            overwrite_pre_args (Optional[dict], optional): An optional argument structure
                to check against instead of the default `_arg_struct`.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        overwrite_pre_args = overwrite_pre_args or self._arg_struct
        current_level: str | dict[str, str | dict] = overwrite_pre_args
        for point in path.split("."):
            if point not in current_level or not isinstance(current_level[point], dict):
                return False
            current_level = current_level[point]
        return True

    def replace_arg_struct(self, new_arg_struct: dict) -> None:
        """Replaces the current argument structure with a new one.

        Updates the structure and removes any existing endpoints that do not match
        the new structure.

        Args:
            new_arg_struct (dict): The new argument structure to replace the current one.
        """
        to_del = []
        for path, endpoint in self._endpoints.items():
            if self._check_path(path, new_arg_struct):
                continue
            else:
                to_del.append(path)
        print(f"Removed {len([self._endpoints.pop(epPath) for epPath in to_del])} endpoints.")

    def add_endpoint(self, path: str, endpoint: EndPoint) -> None:
        """Adds an endpoint at a specified path within the structure.

        The endpoint will be callable from the CLI if the provided path matches.

        Args:
            path (str): Dot-separated path where the endpoint will be added.
            endpoint (EndPoint): The endpoint instance to associate with the path.

        Raises:
            ValueError: If the path does not exist within the argument structure
                or if it already has an endpoint assigned.
        """
        if self._check_path(path):
            if not self._endpoints.get(path):
                self._endpoints[path] = endpoint
            else:
                raise ValueError(f"The path {path} already has an endpoint.")
        else:
            raise ValueError(f"The path '{path}' doesn't exist.")

    def replace_endpoint(self, path: str, endpoint: EndPoint) -> None:
        """Replaces an existing endpoint at a given path.

        This method checks if the specified path exists in the argument structure
        before replacing the existing endpoint with the new one. If the path does
        not exist, an error is raised.

        Args:
            path (str): The path where the endpoint will be replaced.
            endpoint (EndPoint): The new endpoint to assign to the specified path.

        Raises:
            ValueError: If the specified path does not exist in the argument structure.
        """
        if self._check_path(path):
            self._endpoints[path] = endpoint
        else:
            raise ValueError(f"The path '{path}' doesn't exist.")

    def _parse_pre_args(self, pre_args: list[str]) -> list[str]:
        """Parses and validates preliminary arguments from the CLI.

        This method traverses the argument structure and verifies that the provided
        arguments match a valid command path. It returns a structured list of the
        parsed arguments.

        Args:
            pre_args (list[str]): List of preliminary command arguments from the CLI.

        Returns:
            list[str]: A list of parsed arguments that form a valid command path.

        Raises:
            IndexError: If an argument does not match any expected value in the structure.
            KeyError: If a required argument is missing from the structure.
        """
        struct_lst = []

        current_struct = self._arg_struct
        i = call = None
        try:
            for i, call in enumerate(pre_args):
                if call in current_struct or ("ANY" in current_struct and len(current_struct) == 1):
                    struct_lst.append(call)
                    if not i == len(pre_args)-1:
                        current_struct = current_struct[call]
                elif len(current_struct) == 0:  # At endpoint
                    break
                else:
                    raise IndexError
        except TypeError:
            print("Too many pre arguments.")
            self._lst_error(i, 0, pre_args, True)
        except (IndexError, KeyError):
            print(f"The argument '{call}' doesn't exist in current_struct ({current_struct}).")
            self._lst_error(i, 0, pre_args, True)
        return struct_lst

    @staticmethod
    def _to_type(to_type: str, type_: _ty.Type[_A] | None) -> _A | None:
        """Converts a string to a specified type.

        This method attempts to convert a string into a specified type. It supports
        basic types, collections, and literals. For collections, it splits the input
        string by whitespace. If a type cannot be determined, it returns None.

        Args:
            to_type (str): The string to be converted.
            type_ (_ty.Type[_A] | None): The target type for conversion.

        Returns:
            _A | None: The converted value, or None if the type is invalid.
        """
        if not type_:
            return None
        if type_ in [list, tuple, set]:
            tmp = to_type.split()
            return type_(tmp)
        elif _ty.get_origin(type_) is _ty.Literal:
            choices = type_.__args__
            choice_types = set(type(choice) for choice in choices)
            if len(choice_types) == 1:
                type_ = choice_types.pop()  # All choices have the same type
            else:  # Choices have different types
                for type_ in choice_types:
                    try:
                        result = type_(to_type)
                    except Exception:
                        continue
                    else:
                        return result
        return type_(to_type)

    @classmethod
    def _parse_args_native_light(cls, args: list[str], endpoint: EndPoint, smart_typing: bool = True
                                 ) -> dict[str, _ty.Any]:
        """Parses command-line arguments in a lightweight manner.

        This method parses arguments for an endpoint function, supporting positional
        arguments, keyword arguments (preceded by '--'), and flags (preceded by '-').
        It also assigns default values if not all arguments are provided.

        Args:
            args (list[str]): The list of arguments from the CLI.
            endpoint (EndPoint): The endpoint for which arguments are parsed.
            smart_typing (bool, optional): If True, attempts to match argument types
                intelligently based on their default values.

        Returns:
            dict[str, _ty.Any]: A dictionary of parsed argument names and values.

        Raises:
            ArgumentParsingError: If an unknown argument is encountered.
        """
        parsed_args = {}
        remaining_args = list(endpoint.analysis["arguments"])

        for i, arg in enumerate(args):
            # Check for keyword argument
            if arg.startswith("--"):
                key, _, value = arg[2:].partition('=')
                if not any(a["name"] == key for a in endpoint.analysis["arguments"]):
                    raise ArgumentParsingError(f"Unknown argument: {key}", i)
                arg_obj = next(a for a in endpoint.analysis["arguments"] if a["name"] == key)
                parsed_args[key] = cls._to_type(value, arg_obj["type"]) if arg_obj["type"] else value
                remaining_args.remove(arg_obj)

            # Check for flag argument
            elif arg.startswith("-"):
                key = arg[1:]
                if not any(a["name"] == key and a["type"] is bool for a in endpoint.analysis["arguments"]):
                    raise ArgumentParsingError(f"Unknown flag argument: {key}", i)
                parsed_args[key] = True
                remaining_arg = next(a for a in endpoint.analysis["arguments"] if a["name"] == key)
                remaining_args.remove(remaining_arg)

            # Handle positional argument
            else:
                if smart_typing:
                    # Find the first argument with a matching type
                    for pos_arg in remaining_args:
                        if isinstance(pos_arg["default"], type(arg)) or pos_arg["default"] is None:
                            parsed_args[pos_arg["name"]] = cls._to_type(arg, pos_arg["type"])
                            remaining_args.remove(pos_arg)
                            break
                    else:
                        raise ArgumentParsingError("No matching argument type found", i)
                else:
                    # Assign to the next available argument
                    if remaining_args:
                        pos_arg = remaining_args.pop(0)
                        parsed_args[pos_arg["name"]] = cls._to_type(arg, pos_arg["type"])

        # Assign default values for missing optional arguments
        for remaining_arg in remaining_args:
            if remaining_arg["default"] is not None:
                parsed_args[remaining_arg["name"]] = remaining_arg["default"]

        return parsed_args

    @staticmethod
    def _parse_args_arg_parse(args: list[str], endpoint: EndPoint) -> dict[str, _ty.Any]:
        """Parses command-line arguments using the argparse library.

        Sets up argparse to support keyword arguments (prefixed with '--') and flag
        arguments (prefixed with '-'), along with custom help texts.

        Args:
            args (list[str]): The list of command-line arguments to parse.
            endpoint (EndPoint): The endpoint that defines the argument structure.

        Returns:
            dict[str, _ty.Any]: A dictionary of parsed argument names and values.
        """
        parser = _ArgumentParser()

        # Set up argparse for keyword and flag arguments
        for arg in endpoint.analysis["arguments"]:
            if arg["type"] is bool:  # For boolean flags
                parser.add_argument(f"-{arg["name"][0]}", f"--{arg["name"]}", action='store_true', help=arg["help"])
            else:
                parser.add_argument(f"--{arg["name"]}", type=arg["type"], default=arg["default"], help=arg["help"])

        # Parse arguments with argparse
        parsed_args = parser.parse_args(args)
        return vars(parsed_args)

    def _parse_args(self, args: list[str], endpoint: EndPoint,
                    mode: _ty.Literal["arg_parse", "native_light"] = "arg_parse") -> dict[str, _ty.Any]:
        """Dispatches argument parsing to a specified mode.

        This method selects the appropriate parsing function (argparse or native light)
        and processes the arguments accordingly.

        Args:
            args (list[str]): The list of command-line arguments.
            endpoint (EndPoint): The endpoint defining argument requirements.
            mode (Literal["arg_parse", "native_light"], optional): Parsing mode.
                Defaults to `"arg_parse"`, but `"native_light"` can be used for lightweight parsing.

        Returns:
            dict[str, _ty.Any]: Parsed arguments as a dictionary.
        """
        func = self._parse_args_native_light if mode == "native_light" else self._parse_args_arg_parse
        return func(args, endpoint)

    def parse_cli(self, system: _sys = _sys, mode: _ty.Literal["arg_parse", "native_light"] = "arg_parse") -> None:
        """Parses CLI arguments and calls the endpoint based on the parsed path.

        This method processes command-line input, navigates the argument structure,
        and calls the relevant endpoint function. If the path is unmatched, it calls
        the `default_endpoint`.

        Args:
            system (_sys, optional): System module to access arguments from `argv`.
            mode (Literal["arg_parse", "native_light"], optional): Mode to parse
                arguments. Defaults to `"arg_parse"`, but `"native_light"` can be used
                for lightweight parsing.
        """
        arguments = system.argv
        pre_args = self._parse_pre_args(arguments)
        path = '.'.join(pre_args)
        args = arguments[arguments.index(pre_args[-1])+1:]  # Will return an empty list, if [i:] is longer than the list
        endpoint = self._endpoints.get(path) or self.default_endpoint
        arguments = self._parse_args(args, endpoint, mode)
        endpoint.call(**arguments)
