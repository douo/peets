import os
from distutils import dir_util
from pathlib import Path

from pytest import fixture


def create_file(name, tmp_path: Path, parent: Path | str | None = None):
    parent = parent or tmp_path
    if not isinstance(parent, Path):
        parent = tmp_path.joinpath(parent)
    f = parent.joinpath(name)
    parent.mkdir(parents=True, exist_ok=True)
    f.touch()
    # FIXME
    os.chdir(tmp_path)
    return f.relative_to(tmp_path)


@fixture
def datadir(tmpdir, request):
    """
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir
