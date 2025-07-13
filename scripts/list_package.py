import os
import ast
from pathlib import Path


def should_skip(path: Path) -> bool:
    """Skip paths that are test files or test folders."""
    return "test" in path.name.lower() or os.path.basename(path.name).startswith("_")


def get_classes_in_file(file_path: Path) -> list[str]:
    """Return list of class names defined in the Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filename=str(file_path))
    except Exception:
        return []

    return [
        n.name
        for n in node.body
        if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and not n.name.startswith("_")
    ]


def list_modules_and_classes(package_dir: str, base_package: str = ""):
    package_path = Path(package_dir).resolve()
    for root, dirs, files in os.walk(package_path):
        root_path = Path(root)
        rel_path = root_path.relative_to(package_path)

        # Build the package path (e.g. aplustools.utils)
        module_prefix = (
            ".".join([base_package] + list(rel_path.parts))
            if rel_path.parts
            else base_package
        )

        # Remove test dirs in-place to avoid walking into them
        dirs[:] = [d for d in dirs if not should_skip(Path(d))]

        for file in files:
            file_path = Path(file)
            if (
                file_path.suffix != ".py"
                or should_skip(file_path)
                or file_path.name.startswith("_")
            ):
                continue

            modname = file_path.stem
            full_module = f"{module_prefix}.{modname}" if module_prefix else modname

            file_full_path = root_path / file_path
            class_names = get_classes_in_file(file_full_path)

            if class_names:
                print(f"{full_module}")
                for cls in class_names:
                    print(f"  - {full_module}.{cls}")

        # If this is a package with __init__.py and classes, list them
        if "__init__.py" in files and not should_skip(root_path):
            init_path = root_path / "__init__.py"
            class_names = get_classes_in_file(init_path)
            if class_names:
                full_package = module_prefix
                print(f"{full_package}")
                for cls in class_names:
                    print(f"  - {full_package}.{cls}")


# Example usage
if __name__ == "__main__":
    # Adjust these as needed
    package_path = "../src/aplustools"
    base_package = "aplustools"

    list_modules_and_classes(package_path, base_package)
