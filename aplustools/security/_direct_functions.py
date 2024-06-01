from aplustools.package import install_dependencies_lst as _install_dependencies_lst


def install_dependencies():
    success = _install_dependencies_lst(["cryptography==42.0.5"])
    if not success:
        return
    print("Done, all possible dependencies for the utils module installed ...")
