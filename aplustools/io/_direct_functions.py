from aplustools.package import install_dependencies_lst as _install_dependencies_lst


def install_dependencies():
    success = _install_dependencies_lst(["speedtest-cli==2.1.3", "windows-toasts==1.1.1; os_name == 'nt'"])
    if not success:
        return
    print("Done, all possible dependencies for the io module installed ...")
