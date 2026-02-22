import os


def cbc_dist_dir() -> str:
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), "cbc_dist")


def cbc_bin_path() -> str:
    return os.path.join(cbc_dist_dir(), "bin", "cbc.exe" if os.name == "nt" else "cbc")


def cbc_include_dir() -> str:
    return os.path.join(cbc_dist_dir(), "include", "coin")


def cbc_lib_dir() -> str:
    return os.path.join(cbc_dist_dir(), "lib")
