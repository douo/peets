import os
from distutils import dir_util
from pathlib import Path
from typing import cast

from pytest import fixture


@fixture
def create_file(tmp_path: Path):
    origin_cwd = os.getcwd()

    def _creator(
        name: list | str, parent: Path | str | None = None, chdir: bool = False
    ) -> list[Path] | Path:
        parent = parent or tmp_path
        if not isinstance(parent, Path):
            parent = Path(parent)
        if not parent.is_relative_to(tmp_path):
            parent = tmp_path.joinpath(parent)

        parent.mkdir(parents=True, exist_ok=True)

        def _mkfile(n: str) -> Path:
            f = cast(Path, parent).joinpath(n)
            f.touch()
            return f.relative_to(tmp_path) if chdir else f

        if chdir:
            os.chdir(tmp_path)
        if type(name) is list:
            return [_mkfile(n) for n in name]
        else:
            return _mkfile(cast(str, name))

    yield _creator

    if os.getcwd() != origin_cwd:
        os.chdir(origin_cwd)


@fixture
def data_path(tmp_path, request) -> Path:
    """
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmp_path))

    return tmp_path
