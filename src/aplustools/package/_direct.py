"""Classes and functions directly accessible through aps.package"""
from importlib.metadata import version as _version, PackageNotFoundError as _PackageNotFoundError
from importlib import import_module as _import_module

from packaging.specifiers import SpecifierSet as _SpecifierSet
from packaging import version as _pkg_version
import warnings as _warnings
import re as _re

# from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
# _enforce_hard_deps(__hard_deps__, __name__)


class LazyLoader:
    """
    LazyModuleLoader is a utility for lazy-loading Python modules and their submodules, with dependency checks.

    This class allows for deferred loading of modules until they are actually used, improving performance in cases where
    a module may not always be necessary. It also checks for required dependencies specified in the module's `__deps__`
    attribute, issuing warnings if any dependencies are missing or do not meet version specifications.

    Features:
    - Lazy-loads modules and submodules.
    - Handles both absolute and relative imports.
    - Checks module dependencies and raises warnings for missing or incompatible dependencies.
    - Provides a `load_all()` method to eagerly load all submodules at once.

    Args:
        module_name (str): The name of the module or package to load. Can handle both packages (e.g., 'aps.io') and modules.

    Methods:
        load_all():
            Loads the specified module and all its submodules eagerly.

    Usage Example:
        loader = LazyModuleLoader('aps.io')
        # Access module properties lazily
        io = loader.some_property
        # Eagerly load all submodules
        loader.load_all()
    """

    def __init__(self, module_name: str) -> None:
        self.module_name: str = module_name
        self.module: _ts.ModuleType | None = None

    @staticmethod
    def _parse_dependency(dep) -> tuple[str | None, str | None]:
        # Regular expression to match a package name followed by an optional version specifier
        match = _re.match(r'([A-Za-z0-9_.-]+)([><=!~]{1,2}.*)?', dep)

        if match:
            pkg_name = match.group(1)  # Package name
            specifier = match.group(2) if match.group(2) else ''  # Version specifier (if exists)
            return pkg_name, specifier
        else:
            return None, None  # In case it doesn't match

    def _check_dependencies(self, module: _ts.ModuleType, enforce_hard: bool = False) -> None:
        """
        Check for the presence of required dependencies stored in __deps__ attribute.

        Args:
            module: The module for which dependencies need to be checked.
        """
        if not hasattr(module, "__deps__") or not hasattr(module, "__hard_deps__"):
            return
        #     raise ValueError(f"__deps__ or __hard_deps__ are not defined in '{self.module_name}'")

        error = ""
        dependencies = module.__deps__
        hard_dependencies = [] if not enforce_hard else module.__hard_deps__
        for dep in dependencies + hard_dependencies:
            try:
                # Split the dependency and version specifier
                pkg_name, specifier = self._parse_dependency(dep)

                # Get the installed version
                installed_version = _version(pkg_name)

                # If there's a version specifier, check against it
                if specifier:
                    spec = _SpecifierSet(specifier)
                    if installed_version not in spec:
                        error = (
                            f"Version conflict for '{pkg_name}' ({{err_type}}): "
                            f"Installed version {installed_version} does not meet {specifier}"
                        )

            except _PackageNotFoundError:
                error = f"{{err_type_upper}} '{dep}' for module '{self.module_name}' is not installed."
            except Exception as e:
                error = f"Error while checking {{err_type}} '{dep}': {e}"
            finally:
                if error != "":
                    if dep in hard_dependencies:
                        raise ModuleNotFoundError(error.format(err_type="hard dependency", err_type_upper="Hard Dependency"))
                    _warnings.warn(error.format(err_type="dependency", err_type_upper="Dependency"))

    def _ensure_loaded_module(self):
        """
        Lazy-load the module or package, and check its dependencies.

        Returns:
            The loaded module.
        """
        if self.module is None:
            try:
                # Handle relative imports correctly
                if self.module_name.startswith('.'):
                    # Calculate the full module name based on the current package
                    caller_package = __name__.rsplit('.', 2)[0]
                    full_module_name = caller_package + self.module_name
                else:
                    full_module_name = self.module_name

                # Import the module
                self.module = _import_module(full_module_name)

                # Check dependencies
                self._check_dependencies(self.module)

            except ImportError as e:
                raise ImportError(
                    f"Optional module '{self.module_name}' not installed. Please install it to use this feature."
                ) from e

    def __repr__(self) -> str:
        if self.module is None:
            return f"<LazyLoader for '{self.module_name}'>"
        return repr(self.module)

    def __getattr__(self, item: str) -> _ts.ModuleType:
        """
        Overrides attribute access to lazily load the module or its submodules.

        Args:
            item (str): The attribute to access, which might trigger the lazy loading of the module or submodule.

        Returns:
            The requested attribute from the lazily loaded module or submodule.
        """
        self._ensure_loaded_module()
        return getattr(self.module, item)

    def __dir__(self) -> list[_ty.Any]:
        """
        Override the `dir()` function to reflect the contents of the lazily loaded module.

        Returns:
            A list of attributes and methods of the module.
        """
        self._ensure_loaded_module()
        return dir(self.module)


def setup_lazy_loaders(
        module_globals: dict[str, _ty.Any],
        lazy_modules: dict[str, str],
        direct_module: _ts.ModuleType | None = None):
    """
    Set up lazy loaders for specified submodules and dynamically import members from a direct module.

    This function configures lazy loaders for submodules and dynamically imports public members from
    the specified direct module without overwriting existing global variables that would later be cleaned up.

    Args:
        module_globals (dict): The global dictionary of the calling module (typically `globals()`).
        lazy_modules (dict): A dictionary of module names to be lazy-loaded, where the key is the attribute
                             name and the value is the module path.
        direct_module (module, optional): The direct module from which to dynamically import public members.
                                          If not provided, no dynamic imports will occur.

    Example Usage:
        lazy_modules = {
            "timid": "aplustools.package.timid",
            "argumint": "aplustools.package.argumint"
        }
        setup_lazy_loaders(globals(), lazy_modules, some_direct_module)
    """
    # Set up lazy loaders
    for name, path in lazy_modules.items():
        module_globals[name] = LazyLoader(path)

    # Initialize or extend __all__ with lazy-loaded module names
    if "__all__" not in module_globals:
        module_globals["__all__"] = []

    module_globals["__all__"].extend(lazy_modules.keys())

    # Import everything from the direct module if provided
    if direct_module:
        direct_module_contents = dir(direct_module)
        for name in direct_module_contents:
            if not name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
                if name in module_globals:
                    _warnings.warn(f"Overwrote {name} while lazy loading", stacklevel=2)
                module_globals[name] = getattr(direct_module, name)
                module_globals["__all__"].append(name)
            elif name == "__deps__":
                fake_self = type("Bla", (LazyLoader,), {"module_name": __name__})
                fake_module = type("clss", (object, ), {
                    "__deps__": getattr(direct_module, name),
                    "__hard_deps__": []  # getattr(direct_module, "__hard_deps__")
                })
                LazyLoader._check_dependencies(fake_self, fake_module)


def optional_import(module_name: str, fromlist: list | None = None) -> _ts.ModuleType | None:  # TODO: Fix return type
    """
    Attempt to import a module by its name. Return the module if available, otherwise return None.

    Args:
        module_name (str): The name of the module to import.
        fromlist (list): List of internal classes to import.

    Returns:
        module: The imported module if successful, or None if the import fails.
    """
    if fromlist is None:
        fromlist = []
    try:
        return __import__(module_name, fromlist=fromlist)
    except ImportError:
        return None


def check_if_available(module_spec: str) -> bool:
    """
    Checks if a module spec is available using importlib and packaging.specifiers.
    Returns True if module spec is available, otherwise False.

    :param module_spec: e.g. 'PySide6>=6.7.0'
    :return: True if available, otherwise False.
    """
    fake_self = type("Bla", (LazyLoader,), {"module_name": __name__})
    fake_module = type("clss", (object,), {
        "__deps__": [],
        "__hard_deps__": [module_spec]
    })
    try:
        LazyLoader._check_dependencies(fake_self, fake_module, True)
    except ModuleNotFoundError:
        return False
    return True


def enforce_hard_deps(hard_deps: list[str], module_name: str) -> None:
    """
    Enforces all hard dependencies passed as hard_deps. Raises a ModuleNotFound error for any missing.

    :param hard_deps: List of hard dep specs e.g. 'PySide>=6.7.0'.
    :param module_name: __name__ of the current module.
    :return: None
    """
    fake_self = type("Bla", (LazyLoader,), {"module_name": module_name})
    fake_module = type("clss", (object,), {
        "__deps__": [],
        "__hard_deps__": hard_deps
    })
    LazyLoader._check_dependencies(fake_self, fake_module, True)
