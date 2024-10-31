from aplustools.package.argumint import analyze_function, ArgStructBuilder, Argumint, EndPoint
from aplustools.data import beautify_json

import typing as _ty
import sys


def tstfunc(hello_world: str = "DEF!", *args, K: _ty.Literal[0, 1] = 1, **kwargs) -> int:
    """
    This is my func!

    :param hello_world: What you want to print
    :param args: Nothing to note here
    :param K: This is always 1
    :param kwargs: Nothing as noted before
    :return: This is not helpful!
    """
    ...


print(beautify_json(analyze_function(tstfunc)))


def local_test():
    def sorry(*args, **kwargs):
        print("Not implemented yet, sorry!")

    def help_text():
        print("Build -> dir/file or help.")

    def build_file(path: _ty.Literal["./main.py", "./file.py"] = "./main.py", num: int = 0):
        """
        build_file
        :param path: The path to the file that should be built.
        :param num:
        :return None:
        """
        print(f"Building file {path} ..., {num}")

    from aplustools.package import timid

    timer = timid.TimidTimer()

    arg_struct = {
        'apt': {  # Root key
            'build': {  # 'build' related options
                'file': {},  # File-related (ensured endpoint)
                'dir': {  # Directory-related options
                    'main': {},  # Main directory (ensured endpoint)
                    'all': {}  # All directories (ensured endpoint)
                }
            },
            'help': {}  # Help options (ensured endpoint)
        }
    }

    # Example usage
    builder = ArgStructBuilder()
    builder.add_command("apt")
    builder.add_nested_command("apt", "build", "file")

    builder.add_nested_command("apt.build", "dir", {'main': {}, 'all': {}})
    # builder.add_subcommand("apt.build", "dir")
    # builder.add_nested_command("apt.build.dir", "main")
    # builder.add_nested_command("apt.build.dir", "all")

    builder.add_command("apt.help")
    # builder.add_nested_command("apt", "help")

    print(builder.get_structure())  # Best to cache this for better times (by ~15 microseconds)

    parser = Argumint(EndPoint(sorry), arg_struct=arg_struct)
    parser.add_endpoint("apt.help", help_text)

    parser.add_endpoint("apt.build.file", EndPoint(build_file))

    sys.argv[0] = "apt"

    # Testing
    # sys.argv = ["apt", "help"]
    sys.argv = ["apt", "build", "file", "./file.py", "--num=19"]
    parser.parse_cli(sys, "native_light")
    print(timer.end())

local_test()
exit()
from aplustools.security.prot import BlackBox, SecureMemoryChunk


# memory = SecureMemoryChunk(1000)
# memory.write(b"\x10" * 100)
# memory.close()


bb = BlackBox()
x = bytearray(b"\x10\x12\xA2")
bb._attrs.d = x
print(x)


class Test:
    def link(self) -> bytes:
        return bytearray(b"\x01" * 4)


bb.link(Test())
print(bb.link_pub_key)
print(bb._attrs.bb_public_key)
print(bb._attrs._offsets)
