from pathlib import Path
import os

def create_file(name, tmp_path: Path, parent: Path | str | None  = None):
    parent = parent or tmp_path
    if not isinstance(parent, Path):
        parent = tmp_path.joinpath(parent)
    f = parent.joinpath(name)
    parent.mkdir(parents=True, exist_ok=True)
    f.touch()
    #FIXME
    os.chdir(tmp_path)
    return f.relative_to(tmp_path)
