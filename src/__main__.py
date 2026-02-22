from . import cbc_bin_path
import subprocess
import sys


def main():
    subprocess.run([cbc_bin_path()] + sys.argv[1:], check=False)


if __name__ == "__main__":
    main()
