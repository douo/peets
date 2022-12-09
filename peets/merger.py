'''
通过定义一系列的 converter 称为 ConvertTable, 实现 addon:dict 到 target:dataclass 的转换/合并
ConvertTable 实际的类型是 list[Converter]
converter 的类型定义如下：
converter:
- dst: str 是 dataclass 的 field name
- src: str 是 addon 的 key
- convert: Callable[[Any,...], Any] ，将 addon[src] 传入，返回值赋予 dst
- options: 用于配置 converter 的特殊行为

定义方式 converter 的方式分为如下几种情况：
1. dst(field name) 与 src(addon key) 相同：
无须声明 converter，会自动找出与 key 相同名称的 field 进行默认逻辑赋值。
2. dst 与 src 不同，但可以通过默认逻辑赋值
type_1: tuple[str, str] = ("field", "key")
3. src 需要通过 convert 才能赋值 dst
type_2: tuple[str, Callable[[Any,...], Any]] = ("field", lambda key: None)
注意 src 复用 lambda 表达式的参数名声明。所以就不需要重新声明 key。
基于定义，这种方式是支持多个 keys 作为入参的
type_2 是通用模式，其他声明方式都可以通过 type_2 实现
4. 嵌套转换
dst 的类型也是 dataclass/list[dataclass], src 对应的值也是 dict/list[dict]
type_3: tuple[str, SubConvertTable] = ("field", ("key", [("sub_field", "sub_key")]))
SubConvertTable 的实际类型是 tuple[str, ConvertTable]

赋值逻辑：
1. 简单类型：
  a. 类型相同直接赋值
  b. 尝试用 field type 的构造函数传入 addon[src]，失败将抛出异常
2. 集合类型:
  1. field type 为 list[T]，convert(addon[src]) 类型为 T，返回值将直接插入 dst
  2. field type 为 dict[K,T], convert(addon[src]) 类型为 tuple[K, T] 返回值将直接更新到 dst
3. 批量赋值
可以同时为多个 dst 赋值，convert(addon[src]) 类型为 tuple[A,B,C,...] ，同时 dst 也是同样数量的 tuple[str,...]
会按顺序将 A、B、C 按顺序应用默认逻辑赋值给对应的 dst


'''
from abc import ABCMeta, abstractmethod
from dataclasses import replace as data_replace
from itertools import chain
from typing import (Any, Callable, Protocol, Tuple, TypeAlias, TypeGuard,
                    TypeVar, Union, cast, get_type_hints, runtime_checkable)

from typing_inspect import get_args, get_origin, is_union_type

from peets.util.type_utils import (check_dict_type, check_iterable_type,
                                   is_assignable)

ConvertTable: TypeAlias = list["ConvertTable"]
SubConvertTable: TypeAlias = tuple[str, ConvertTable]
Dst: TypeAlias = str | tuple[str, ...]
Src: TypeAlias = str | Callable | SubConvertTable
Converter: TypeAlias = tuple[Dst, Src]

class UnexceptType(Exception):
    pass


class FieldNotExistError(Exception):
    pass


@runtime_checkable
class Mergeable(Protocol, metaclass=ABCMeta):
    """
    用于元类检查，不是类型检查
    用于类型是否是 dataclass 注解的类
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
MapTableConverter: TypeAlias = Union[
    Callable, None, Tuple[Union[Callable, None], ...], "MapTable"
]
MapTableItem: TypeAlias = (
    tuple[str | tuple[str, ...], str | tuple[str, ...], MapTableConverter]
    | tuple[str | tuple[str, ...], str | tuple[str, ...]]
)

MapTable: TypeAlias = list[MapTableItem]


StictMapTableItem = tuple[tuple[str, ...], tuple[str, ...], tuple[Callable | None, ...]]
StictMapTable: TypeAlias = list[StictMapTableItem]


def _make_sure_tuple(obj: T | tuple[T, ...]) -> tuple[T, ...]:
    return obj if isinstance(obj, tuple) else (obj,)


def _make_sure_table(map_table: MapTable) -> StictMapTable:
    """
    make sure all item is tuple
    """
    return list(
        map(
            lambda i: i
            if len(i) == 3
            else i + (map(lambda _: None, i[1]),),  #  补全省略的 converter
            map(
                lambda i: tuple(
                    map(lambda j: _make_sure_tuple(j), i)
                ),  # 确保所有元素都是 tuple
                map_table,
            ),
        )
    )  # type: ignore


def _get_mergeable(type_: type) -> Mergeable | None:
    if isinstance(type_, Mergeable):
        return type_
    elif is_union_type(type_) and any(
        t for t in get_args(type_) if isinstance(t, Mergeable)
    ):
        return next(t for t in get_args(type_) if isinstance(t, Mergeable))
    else:
        return None


def _sanity_kwargs(target: Mergeable, kwargs_: dict) -> dict:
    base_fields = get_type_hints(target)

    def create_if_need(k, v):
        f_type = base_fields[k]

        v_type = type(v)
        if (f_type_mergeable := _get_mergeable(f_type)) and v_type is dict:
            return create(f_type_mergeable, v)
        elif (
            get_origin(f_type) is list
            and (f_item_type := _get_mergeable(f_type.__args__[0]))
            and check_iterable_type(v, dict)
        ):
            return [create(f_item_type, v_item) for v_item in v]
        elif (
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


def create(type_: type[T], addon: dict[str, Any], table: MapTable | None = None) -> T:
    """
    type_ 是 @dataclass 装饰的类型
    用 Mergeable 表示显示不是好办法
    """
    kwargs_ = to_kwargs(type_, addon, table)
    kwargs_ = _sanity_kwargs(cast(Mergeable, type_), kwargs_)
    return type_(**kwargs_)


def replace(base: Any, addon: dict[str, Any], table: MapTable | None = None) -> Any:
    type_ = cast(Mergeable, type(base))
    kwargs_ = to_kwargs(type_, addon, table)
    kwargs_ = _sanity_kwargs(type_, kwargs_)
    return data_replace(base, **kwargs_)


def to_kwargs(type_: Any, addon: dict[str, Any], table: MapTable | None = None) -> dict:
    """
    将 addon 转换成 base 的 kwargs
    """
    map_table = _make_sure_table(table) if table else []
    # 找出 map_table 中声明的 keys
    used = set(chain(*map(lambda i: i[0], map_table)))
    base_fields = get_type_hints(type_)

    map_table += [
        ((k,), (k,), (None,))
        for k in addon.keys()
        if k not in used and k in base_fields
    ]

    result = {}

    def _map_table_guard(conv) -> TypeGuard[MapTable]:
        if not conv or len(conv) == 0 or type(conv[0]) is tuple:
            return True
        raise UnexceptType(f"conv is {type(conv)} should be MapTable")

    for item in map_table:
        key, target, converter = item
        params = tuple(map(addon.get, key))
        for attr, conv in zip(target, converter):
            if attr not in base_fields:
                raise FieldNotExistError(attr)
            f_type = base_fields[attr]  # filed type
            v = (
                conv(*params) if conv and isinstance(conv, Callable) else params[0]
            )  #  converter 非 Callable 直接取值
            v_type = type(v)
            if is_assignable(v_type, f_type):
                result[attr] = v
            elif (f_item_type := _get_mergeable(f_type)) and v_type is dict:
                if _map_table_guard(conv):
                    v = cast(dict[str, Any], v)
                    result[attr] = to_kwargs(f_item_type, v, conv)
            # TODO Sequences
            elif get_origin(f_type) is list:
                old = result[attr] if attr in result else []
                f_item_type = f_type.__args__[0]
                if v_type is list:
                    v = cast(list, v)
                    if check_iterable_type(v, f_item_type):
                        old += v
                    elif (
                        f_item_mergeable_type := _get_mergeable(f_item_type)
                    ) and check_iterable_type(v, dict):
                        if _map_table_guard(conv):
                            v = cast(list[dict[str, Any]], v)
                            old += [
                                to_kwargs(f_item_mergeable_type, v_i, conv) for v_i in v
                            ]
                    else:
                        raise UnexceptType(
                            f"Get Type {v_type}, except {attr} type is {f_type}"
                        )
                elif is_assignable(v_type, f_item_type):
                    old.append(v)
                elif (
                    f_item_mergeable_type := _get_mergeable(f_item_type)
                ) and v_type is dict:
                    if _map_table_guard(conv):
                        v = cast(dict[str, Any], v)
                        old.append(to_kwargs(f_item_mergeable_type, v, conv))
                else:
                    raise UnexceptType(
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
                        and check_iterable_type(v.keys(), f_key_type)
                        and check_iterable_type(v.values(), dict)
                    ):  # 只对 value 进行处理
                        if _map_table_guard(conv):
                            v = cast(dict[f_key_type, dict[str, Any]], v)
                            old |= {
                                k: to_kwargs(f_value_mergeable_type, v_i, conv)
                                for k, v_i in v.items()
                            }
                    else:
                        raise UnexceptType(
                            f"Get Type {v_type}, except {attr} type is {f_type}"
                        )
                elif isinstance(v, tuple):
                    if is_assignable(type(v[0]), f_key_type) and is_assignable(
                        type(v[1]), f_value_type
                    ):  # FIXME 没类型推定？
                        old.__setitem__(*v)
                    elif (
                        (f_value_mergeable_type := _get_mergeable(f_value_type))
                        and is_assignable(type(v[0]), f_key_type)
                        and is_assignable(type(v[1]), dict[str, Any])
                    ):
                        if _map_table_guard(conv):
                            v = cast(tuple[f_key_type, dict[str, Any]], v)
                            old[v[0]] = to_kwargs(f_value_mergeable_type, v[1], conv)
                    else:
                        raise UnexceptType(
                            f"Get Type {v_type}, except {attr} type is {f_type}"
                        )
                else:
                    raise UnexceptType(
                        f"Get Type {v_type}, except {attr} type is {f_type}"
                    )
                result[attr] = old
            else:
                raise UnexceptType(
                    f"Get Type {type(v)}, except {attr} type is {f_type}"
                )

    return result
