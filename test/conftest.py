import inspect
import os
import random
from dataclasses import is_dataclass
from distutils import dir_util
from pathlib import Path
from typing import Callable, TypeVar, cast, get_type_hints

from pytest import fixture
from typing_inspect import (
    get_args,
    get_origin,
    is_generic_type,
    is_tuple_type,
    is_union_type,
)


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
def dummy(faker) -> Callable[[type[T]], T]:
    def valiable_func(obj, name) -> bool:
        try:
            return False if name[0] == "_" else callable(getattr(obj, name))
        except TypeError:
            return False

    fake_funcs = [s for s in dir(faker) if valiable_func(faker, s)]

    def _create_dataclass(type_: type[T]) -> T:
        if not is_dataclass(type_):
            raise TypeError(f"{type_} is not a dataclass.")
        fs = get_type_hints(type_)
        kwargs_ = {
            k: new_v
            for k, new_v in [(k, _create_field(k, v)) for k, v in fs.items()]
            if new_v
        }
        return type_(**kwargs_)

    def _create_faker_type(type_: type[T]) -> T:
        if type_ is type(None):
            return None
        name = f"py{type_.__name__}"
        if name in fake_funcs:
            func = getattr(faker, name)
            return func()
        raise TypeError(f"No {name} function in faker")

    def _create_collection(type_: type[T], args_t) -> T:
        if type_ in [list, set]:
            func = getattr(faker, f"py{type_.__name__}")
            if len(args_t) != 1:
                raise TypeError("list/set should has only one arg type")
            arg_t = args_t[0]
            if is_union_type(arg_t):
                return func(value_types=get_args(arg_t))
            if is_dataclass(arg_t):
                # 默认长度 10
                return [_create_dataclass(arg_t) for i in range(0, 10)]
            return func(allowed_types=[arg_t])
        if type_ == dict:
            if len(args_t) != 2:
                raise TypeError("list should has 2 args type")
            arg_t = args_t[1]
            if args_t[0] == str:
                if is_union_type(arg_t):
                    return faker.pydict(value_types=get_args(arg_t))
                else:
                    return faker.pydict(value_types=[arg_t])
            else:
                items = []
                for i in range(0, 10):
                    if is_dataclass(args_t[0]):
                        k = _create_dataclass(args_t[0])
                    else:
                        k = _create_faker_type(args_t[0])
                    if is_dataclass(args_t[1]):
                        v = _create_dataclass(args_t[1])
                    else:
                        v = _create_faker_type(args_t[1])
                    items.append((k, v))
                return dict(items)

            return func(value_types=args_t)
        if type_ == tuple:
            # TODO 完善复杂类型
            if Ellipsis in args_t:  # tuple[str,...]
                return faker.pytuple(value_types=args_t[0])
            else:
                return faker.pytuple(
                    nb_elements=len(args_t),
                    variable_nb_elements=False,
                    value_types=args_t,
                )

        raise TypeError(f"faker can't handle {type_}")

    def _create_field(name: str, type_: type[T]) -> T | None:
        if is_union_type(type_):
            # breakpoint()
            args_t = get_args(type_)
            type_set = random.sample([*args_t], len(args_t))
            if name in fake_funcs:
                func = getattr(faker, name)
                sig = inspect.signature(func)
                if sig.return_annotation in type_set:
                    return func()
            for new_t in type_set:
                try:
                    return _create_field(name, new_t)  # 类型缩减
                except TypeError:
                    print(f"{name}  TypeError: f{new_t}")

        if is_dataclass(type_):
            return _create_dataclass(type_)
        if is_generic_type(type_) or is_tuple_type(type_):
            origin = get_origin(type_)
            args_t = get_args(type_)
            return _create_collection(origin, args_t)

        try:
            if name in fake_funcs:
                func = getattr(faker, name)
                sig = inspect.signature(func)
                if sig.return_annotation == type_:
                    return func()
            return _create_faker_type(type_)
        except TypeError:
            print(f"{name}  TypeError: f{new_t}")

        return None

    return _create_dataclass
