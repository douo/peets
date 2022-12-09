from mypy.stubtest import Signature
import inspect
import os
from distutils import dir_util
from pathlib import Path
from typing import Callable, TypeVar, cast, get_type_hints

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


T = TypeVar("T")


@fixture
def dummy(fake) -> Callable[type[T], T]:
    def valiable_func(obj, name) -> bool:
       try:
         func =  getattr(obj, name)
         return s[0] != '_'  and callable(func)
       except:
         return False

    fake_funcs = [for s in dir(fake) if valiable_func(fake, s)]

    def _fake(name: str, type_: type[T]) -> T | None:
        if(name in fake_funcs):
            func = getattr(fake, name)
            sig = inspect.signature(func)
            if type_ == sig.return_annotation: #FIXME
                return func()
        name = f"py{type_}"
        if(name in fake_funcs):
            func = getattr(fake, name)
            return func()
        return None

    def _create(type_: type[T]) -> T:
        fs = get_type_hints(type_)
        kwargs_ = {k, _fake(v)  for k, v in fs.items()}
        return type_(**kwargs_)
