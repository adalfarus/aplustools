from aplustools.package import install_dependencies_lst as _install_dependencies_lst


def install_dependencies():
    success = _install_dependencies_lst(["requests==2.31.0", "PySide6==6.6.1", "Pillow==10.3.0", "aiohttp==3.9.3",
                                         "opencv-python==4.9.0.80", "pillow_heif==0.15.0"])
    if not success:
        return
    print("Done, all possible dependencies for the data module installed ...")
