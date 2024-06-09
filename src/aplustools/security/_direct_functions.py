from src.aplustools import install_dependencies_lst as _install_dependencies_lst


def install_dependencies():
    success = _install_dependencies_lst(["cryptography==42.0.5", "quantcrypt==0.4.2"])
    if not success:
        return
    print("Done, all possible dependencies for the utils module installed ...")
