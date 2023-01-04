"""
ConvertTable 指由 Converter 构成的列表 , 实现 addon:dict 到 target:dataclass 的转换/合并
ConvertTable 实际的类型是 list[Converter]
Converter 的属性定义如下：
- dst: str 是 dataclass 的 field name
- src: str 是 addon 的 key
- convert: Callable[[Any,...], Any] ，将 addon[src] 传入，返回值赋予 dst
- options: 用于配置 converter 的特殊行为

具体定义 converter 的方式分为如下几种情况：
1. dst(field name) 与 src(addon key) 相同：
无须声明 converter，会自动找出与 key 相同名称的 field 进行默认逻辑赋值。
2. dst 与 src 不同，但可以通过默认逻辑赋值
type_1: tuple[str, str]: ("field", "key")
3. src 需要通过 convert 才能赋值 dst
type_2: tuple[str, Callable[[Any,...], Any]]: ("field", lambda key: None)
注意 src 复用 lambda 表达式的参数名声明。所以就不需要重新声明 key。
基于定义，这种方式是支持多个 keys 作为入参的
type_2 是通用模式，其他声明方式都可以通过 type_2 实现
4. 嵌套转换
dst 的类型也是 dataclass/list[dataclass], src 对应的值也是 dict/list[dict]
type_3: tuple[str, SubConvertTable]: ("field", ("key", [("sub_field", "sub_key")]))
SubConvertTable 的实际类型是 tuple[str, ConvertTable]
5. 特殊情况
a. 如果 key 已被显式定义，则不会自动赋值到同名字段

赋值逻辑：
ConvertTable 转换的结果并不是 dataclass，而是一个可用于 dataclass 的 create, replace 方法参数的 shadow dict。所有赋值的描述都是针对于改 shadow dict 而言的。
1. 非集合类型：
  a. 类型相同直接赋值
  b. 都是简单类型（int float complex bool str）尝试用盖类型的构造函数传入 addon[src]，失败将抛出异常
2. 集合类型:
  a. field type 为 list[T]，convert(addon[src]) 类型为 T，返回值将直接插入 dst
  b. field type 为 dict[K,T], convert(addon[src]) 类型为 tuple[K, T] 返回值将直接更新到 dst
  c. ConvertTable 多次更新同一个 dst，都是操作 shadow dict 上的同一个集合实例，初始是一个空集合。无论返回单项还是集合都直接添加（append/update）到 dst  上（dst.update(shadow_dst)）
3. 批量赋值
可以同时为多个 dst 赋值，convert(addon[src]) 类型为 tuple[A,B,C,...] ，同时 dst 也是同样数量的 tuple[str,...]
会按顺序将 A、B、C 按顺序应用默认逻辑赋值给对应的 dst

Options
1. converter 声明的 str 在 addon 中不存在
  - 作为 None 传入（默认）
  - 抛出异常
  - 直接忽略
    - 所有依赖的 src 不存在才忽略，不存在的作为 None 传入
    - 任意 src 不存在就忽略
"""
import inspect
from abc import ABCMeta, abstractmethod
from dataclasses import replace as data_replace
from enum import Flag, auto
from itertools import chain
from types import FunctionType
from typing import (
    Any,
    Callable,
    Protocol,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    get_type_hints,
    runtime_checkable,
)

from typing_inspect import get_args, get_origin, is_union_type

from peets.util.type_utils import check_dict_type, check_iterable_type, is_assignable


class Option(Flag):
    KEY_NOT_EXIST_RAISE = auto()
    KEY_NOT_EXIST_AS_NONE = auto()
    KEY_NOT_EXIST_IGNORE_ANY = auto()
    KEY_NOT_EXIST_IGNORE_ALL = auto()


ConvertTable: TypeAlias = list["Converter"]
SubConvertTable: TypeAlias = tuple[str, ConvertTable]
Dst: TypeAlias = str | tuple[str, ...]
Src: TypeAlias = str | Callable | SubConvertTable
Converter: TypeAlias = tuple[Dst, Src] | tuple[Dst, Src, Option]
PRIMITIVE_TYPE = [str, int, float, complex, bool]


class TypeNotMatch(Exception):
    pass


@runtime_checkable
class Mergeable(Protocol, metaclass=ABCMeta):
    """
    用于元类检查，不是类型检查
    用于类型是否是 dataclass 注解的类
    与 dataclasses.is_dataclass 作用相同
    """

    @staticmethod
    @abstractmethod
    def __call__(self):
        pass

    @property
    @abstractmethod
    def __dataclass_fields__(self):
        pass


T = TypeVar("T")
R = TypeVar("R")


def _is_sub_convert_table(src):
    return isinstance(src, tuple)  # TODO


def _make_sure_tuple(obj: T | tuple[T, ...]) -> tuple[T, ...]:
    return obj if isinstance(obj, tuple) else (obj,)


def _get_mergeable(type_: type) -> Mergeable | None:
    """
    类型是 Mergeable 或者含有 Mergeable
    返回该 Mergeable 类型
    """
    if isinstance(type_, Mergeable):
        return type_
    elif is_union_type(type_) and any(
        t for t in get_args(type_) if isinstance(t, Mergeable)
    ):
        return next(t for t in get_args(type_) if isinstance(t, Mergeable))
    else:
        return None


def _sanity_kwargs(target: Mergeable, kwargs_: dict) -> dict:
    """
    处理嵌套转换，嵌套的 dict 在这一步转换为 dataclass
    """
    base_fields = get_type_hints(target)

    def create_if_need(k, v):
        f_type = base_fields[k]

        v_type = type(v)
        # dst 是 dataclass 且 src 是 dict
        if (f_type_mergeable := _get_mergeable(f_type)) and v_type is dict:
            return create(f_type_mergeable, v)
        elif (
            # dst 是 list[dataclass]
            get_origin(f_type) is list
            and (f_item_type := _get_mergeable(f_type.__args__[0]))
            and check_iterable_type(v, dict)
        ):
            return [create(f_item_type, v_item) for v_item in v]
        elif (
            # dst 是 dict[*, dataclass]
            get_origin(f_type) is dict
            and (f_value_type := _get_mergeable(f_type.__args__[1]))
            and check_iterable_type(v.values(), dict)
        ):
            return {
                v_key: create(f_value_type, v_value) for v_key, v_value in v.items()
            }
        else:
            return v

    return {k: create_if_need(k, v) for k, v in kwargs_.items()}


def create(
    type_: type[T], addon: dict[str, Any], table: ConvertTable | None = None
) -> T:
    """
    type_ 是 @dataclass 装饰的类型
    用 Mergeable 表示显示不是好办法
    """
    kwargs_ = to_kwargs(type_, addon, table)
    kwargs_ = _sanity_kwargs(cast(Mergeable, type_), kwargs_)
    return type_(**kwargs_)


def replace(base: Any, addon: dict[str, Any], table: ConvertTable | None = None) -> Any:
    type_ = cast(Mergeable, type(base))
    kwargs_ = to_kwargs(type_, addon, table)
    kwargs_ = _sanity_kwargs(type_, kwargs_)
    return data_replace(base, **kwargs_)


def to_kwargs(
    type_: Mergeable, addon: dict[str, Any], table: ConvertTable | None = None
) -> dict:
    """
    将 addon 转换成 base 的 kwargs
    """

    type_hints = get_type_hints(type_)
    table = table.copy() if table else []
    used = _get_table_used_key(table)
    # 补全名字相同的项
    table += [(k, k) for k in addon.keys() if k not in used and k in type_hints]
    result = {}

    for converter in table:
        if _option_key_guard(converter, addon):
            continue
        dst, keys, values, sub_table, opt = _preprocess_converter(converter, addon)
        for attr, v in zip(dst, values):
            f_type = type_hints[attr]  # field type
            v_type = type(v)
            if is_assignable(v_type, f_type):
                result[attr] = v
            elif new_v := _auto_convert_primitive(f_type, v_type, v):
                result[attr] = new_v  # 赋值逻辑 1-b
            elif (
                (f_mergeable_type := _get_mergeable(f_type))
                and sub_table is not None  # type 2 不做检查
                and v_type is dict
            ):
                result[attr] = to_kwargs(f_mergeable_type, v, sub_table)
            # List
            elif get_origin(f_type) is list:
                old = result[attr] if attr in result else []
                # 假设列表的类型都是一致的
                f_item_type = get_args(f_type)[0]
                if v_type is list:
                    v = cast(list, v)
                    if check_iterable_type(v, f_item_type):
                        old += v
                    elif (
                        (f_item_mergeable_type := _get_mergeable(f_item_type))
                        and sub_table is not None
                        and check_iterable_type(v, dict)
                    ):
                        old += [to_kwargs(f_item_mergeable_type, i, sub_table) for i in v]
                    else:
                        raise TypeNotMatch(
                            f"Get Type {v_type}, except {attr} type is {f_type}"
                        )
                elif is_assignable(v_type, f_item_type):
                    old.append(v)
                elif (
                    (f_item_mergeable_type := _get_mergeable(f_item_type))
                    and sub_table is not None
                    and v_type is dict
                ):
                    old.append(to_kwargs(f_item_mergeable_type, v, sub_table))
                else:
                    raise TypeNotMatch(
                        f"Get Type {v_type}, except {attr} type is {f_type}"
                    )
                result[attr] = old
            # Dict
            elif get_origin(f_type) is dict:
                old = result[attr] if attr in result else {}
                f_key_type = f_type.__args__[0]
                f_value_type = f_type.__args__[1]
                if isinstance(v, dict):
                    # v_type 与 f_type 键值类型都匹配
                    if check_dict_type(v, cast(tuple[Any, Any], get_args(f_type))):
                        old |= v
                    elif (
                        (f_value_mergeable_type := _get_mergeable(f_value_type))
                        and sub_table is not None
                        and check_iterable_type(v.keys(), f_key_type)
                        and check_iterable_type(v.values(), dict)
                    ):
                        old |= {
                            k: to_kwargs(f_value_mergeable_type, v_i, sub_table)
                            for k, v_i in v.items()
                        }
                    else:
                        raise TypeNotMatch(
                            f"Get Type {v_type}, except {attr} type is {f_type}"
                        )
                elif isinstance(v, tuple):
                    if is_assignable(type(v[0]), f_key_type) and is_assignable(
                        type(v[1]), f_value_type
                    ):  # FIXME 没类型推定？
                        old.__setitem__(*v)
                    elif (
                        (f_value_mergeable_type := _get_mergeable(f_value_type))
                        and sub_table is not None
                        and is_assignable(type(v[0]), f_key_type)
                        and is_assignable(type(v[1]), dict[str, Any])
                    ):
                        old[v[0]] = to_kwargs(f_value_mergeable_type, v[1], sub_table)
                    else:
                        raise TypeNotMatch(
                            f"Get Type {v_type}, except {attr} type is {f_type}"
                        )
                else:
                    raise TypeNotMatch(
                        f"Get Type {v_type}, except {attr} type is {f_type}"
                    )
                result[attr] = old
            else:
                raise TypeNotMatch(
                    f"Get Type {type(v)}, except {attr} type is {f_type}"
                )

    return result


def _option_key_guard(converter: Converter, addon: dict) -> bool:
    """
    处理 key 在 addon 不存在的逻辑
    """
    option = converter[2] if len(converter) > 2 else Option.KEY_NOT_EXIST_AS_NONE
    src = _convert_src_to_keys(converter[1])
    if Option.KEY_NOT_EXIST_RAISE in option:
        for key in src:
            if key not in addon:
                raise KeyError(f"{key=} not in {addon=}")
    elif Option.KEY_NOT_EXIST_IGNORE_ALL in option:
        return all(k not in addon for k in src)
    elif Option.KEY_NOT_EXIST_IGNORE_ANY in option:
        return any(k not in addon for k in src)
    elif Option.KEY_NOT_EXIST_AS_NONE in option:
        return False
    else:
        raise ValueError(f"Unknown {option=}")


def _preprocess_converter(converter: Converter, addon: dict):
    """
    转换 Converter 到统一的标准类型:
    [(dst,...),(value,...), sub table, Option]
    """
    match converter:
        case dst, str() as key, *opt:
            dst = _make_sure_tuple(dst)
            keys = _make_sure_tuple(key)
            values = (addon.get(key),)
            table: list | None = []
        case dst, FunctionType() as conv, *opt:
            keys = tuple(inspect.getfullargspec(conv)[0])
            params = tuple(map(addon.get, keys))
            values = conv(*params)
            # dst 只有一个值时，返回值直接赋予 dst
            if not isinstance(dst, tuple):
                values = (values,)
            dst = _make_sure_tuple(dst)
            table = None
        case dst, (str() as key, list() as table), *opt:
            dst = _make_sure_tuple(dst)
            keys = _make_sure_tuple(key)
            values = (addon.get(key),)
        case _:
            raise TypeError(f"{type(src)=} is not a type of {Src=} .")

    opt = opt[0] if opt else None
    return (dst, keys, values, table, opt)


def _get_table_used_key(table: ConvertTable) -> set[str]:
    return set(chain(*(_convert_src_to_keys(c[1]) for c in table)))


def _convert_src_to_keys(src: Src) -> tuple[str, ...]:
    match src:
        case str() as src:
            return (src,)
        case FunctionType() as conv:
            return tuple(inspect.getfullargspec(conv)[0])
        case str() as src, list():
            return (src,)
        case _:
            raise TypeError(f"{src} is not a f{Src} type.")


def _auto_convert_primitive(f_type: type, v_type: type, v: Any) -> Any | None:
    if v_type in PRIMITIVE_TYPE:
        if f_type in PRIMITIVE_TYPE:
            return f_type(v)
        elif is_union_type(f_type):
            for t in get_args(f_type):
                if t in PRIMITIVE_TYPE:
                    try:
                        return t(v)
                    except ValueError:
                        # logger.warning("auto convert failed.", exc_info=True)
                        pass

    return None
