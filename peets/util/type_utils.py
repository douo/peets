from typing import Any, Iterable, TypeGuard, TypeVar

from typing_inspect import get_args, get_origin, is_generic_type, is_tuple_type

T = TypeVar("T")
R = TypeVar("R")


def is_assignable(v_type: type, f_type: type) -> bool:
    """
    检查类型是否能赋值给目标类型
    """
    # print(f"{v_type}/{f_type}")
    # TODO 没考虑 Union Type
    return (
        f_type is Any  # 任何值都可以赋予 Any
        or (
            v_type is tuple and is_tuple_type(f_type)
        )  # 因为类型擦除，运行时无法区分 List[str] 和 List[int]，
        or not is_generic_type(f_type)
        and issubclass(v_type, f_type)
    )


def check_dict_type(
    dict_: dict, target: tuple[type[T], type[R]]
) -> TypeGuard[dict[T, R]]:
    return all(
        is_assignable(type(k), target[0]) and is_assignable(type(v), target[1])
        for k, v in dict_.items()
    )


def check_iterable_type(iter_: Iterable, target: type[T]) -> TypeGuard[Iterable[T]]:
    """
    检查集合中的类型都是目标类型
    """
    return all(is_assignable(type(x), target) for x in iter_)
