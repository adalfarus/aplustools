from aplustools.package import install_dependencies_lst as _install_dependencies_lst


def install_dependencies():
    success = _install_dependencies_lst(["Pillow==10.2.0", "pycryptodome==3.20.0", "brotli==1.1.0", "zstandard==0.22.0",
                                         "py7zr==0.21.0"])
    if not success:
        return
    print("Done, all possible dependencies for the utils module installed ...")
