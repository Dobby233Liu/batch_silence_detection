import shutil
import subprocess
from io import FileIO
from os.path import realpath
from pydub import AudioSegment


if shutil.which("vgmstream-cli") is None:
    raise Exception("vgmstream-cli is not available")


def seg_from_vgmstream(f: str|FileIO, args=[]) -> AudioSegment:
    in_path = None
    if isinstance(f, FileIO):
        in_path = f.name
    elif isinstance(f, str):
        in_path = realpath(f)
    else:
        raise NotImplementedError()

    with subprocess.Popen(
            [shutil.which("vgmstream-cli"),
                in_path,
                "-p", "-w", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=4096
    ) as proc:
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, proc.args, out, err)

        return AudioSegment(out)