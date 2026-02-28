from . import cbc_bin_path
import os
import subprocess
import sys


def main():
    """Entry point for the `cbc` console script.

    On Unix, replaces the Python process with the native CBC binary via
    os.execv — zero overhead, clean signal/exit-code propagation.
    On Windows, runs it as a subprocess and forwards the exit code.
    """
    bin_path = cbc_bin_path()
    args = [bin_path] + sys.argv[1:]
    if os.name != "nt":
        os.execv(bin_path, args)          # replaces this process entirely
    else:
        result = subprocess.run(args, check=False)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
