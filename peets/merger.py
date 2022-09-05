from sys import meta_path
from types import NoneType, UnionType
from typing import Generic, Protocol, Iterable, Sequence, Type, Any, TypeGuard, Union, Callable, get_type_hints, runtime_checkable, TypeVar, cast, TypeAlias
from typing_inspect import get_args, get_origin, is_generic_type, is_tuple_type, is_union_type
from itertools import chain
from dataclasses import replace as data_replace
from attr import attrib
from peets.entities import MediaEntity
from abc import ABCMeta, abstractmethod



class TypeNotMatchError(Exception):
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

T = TypeVar('T')
R = TypeVar('R')
MapTableConverter: TypeAlias = None | Callable | tuple[Callable | None,...] | "MapTable"
MapTableItem: TypeAlias = (tuple[str | tuple[str,...], str | tuple[str,...], MapTableConverter ] |
                           tuple[str | tuple[str,...], str | tuple[str,...]])
MapTable: TypeAlias = list[MapTableItem]

StictMapTableItem = tuple[tuple[str,...], tuple[str,...], tuple[Callable | None,...]]
StictMapTable: TypeAlias  = list[StictMapTableItem]


def _make_sure_tuple(obj: T | tuple[T,...]) -> tuple[T,...]:
    return obj if isinstance(obj, tuple) else(obj,)


def _make_sure_table(map_table: MapTable) -> StictMapTable:
    """
    make sure all item is tuple
    """
    return  list(map(lambda i: i if len(i) == 3 else i + (map(lambda _: None, i[1]),), #  补全省略的 converter
                map(lambda i: tuple(map(lambda j:  _make_sure_tuple(j), i)), # 确保所有元素都是 tuple
            map_table)
    )) # type: ignore


def _is_assignable(v_type: type, f_type: type) -> bool:
    """
    检查类型是否能赋值给目标类型
    """
    # print(f"{v_type}/{f_type}")
    return (f_type is Any or # 任何值都可以赋予 Any
            # 因为类型擦除，运行时无法区分 List[str] 和 List[int]，
            # get_origin(f_type) is v_type or
            (v_type is tuple and is_tuple_type(f_type)) or
            not is_generic_type(f_type) and
            issubclass(v_type, f_type))


def _check_dict_type(dict_:dict, target: tuple[type[T], type[R]]) -> TypeGuard[dict[T,R]]:
    return all(_is_assignable(type(k), target[0]) and _is_assignable(type(v), target[1]) for k,v in dict_.items())


def _check_iterable_type(iter_:Iterable, target:  type[T]) -> TypeGuard[Iterable[T]]:
    """
    检查集合中的类型都是目标类型
    """
    return all(_is_assignable(type(x), target) for x in iter_)


def _get_mergeable(type_: type) -> Mergeable | None:
    if isinstance(type_, Mergeable):
        return type_
    elif is_union_type(type_) and any(t for t in get_args(type_) if isinstance(t, Mergeable)):
        return next(t for t in get_args(type_) if isinstance(t, Mergeable))
    else:
        return None


def _sanity_kwargs(target: Mergeable, kwargs_: dict) -> dict:
    base_fields = get_type_hints(target)

    def create_if_need(k, v):
        f_type = base_fields[k]

        v_type = type(v)
        if  (f_type_mergeable := _get_mergeable(f_type)) and v_type is dict:
            return create(f_type_mergeable, v)
        elif get_origin(f_type) is list and (f_item_type := _get_mergeable(f_type.__args__[0])) and _check_iterable_type(v, dict):
            return [create(f_item_type, v_item) for v_item in v]
        elif get_origin(f_type) is dict and (f_value_type := _get_mergeable(f_type.__args__[1])) and _check_iterable_type(v.values(), dict):
            return { v_key: create(f_value_type, v_value) for v_key, v_value in v.items() }
        else:
            return v

    return { k: create_if_need(k, v) for k, v in kwargs_.items() }



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

    map_table += [((k,), (k,), (None,)) for k in addon.keys() if k not in used and k in base_fields]

    result = { }

    _converter_as_map_table = lambda conv: cast(MapTable, conv) if (conv and type(conv) is MapTable) else None

    for item in map_table:
        key, target, converter = item
        params = tuple(map(addon.get, key))
        for attr, conv in zip(target, converter):
            if attr not in base_fields:
                raise FieldNotExistError(attr)
            f_type = base_fields[attr]  # filed type
            v = conv(*params) if conv and isinstance(conv, Callable) else params[0] #  converter 非 Callable 直接取值
            v_type = type(v)
            if _is_assignable(v_type, f_type):
                result[attr] = v
            elif (f_item_type := _get_mergeable(f_type)) and v_type is dict:
                v = cast(dict[str, Any], v)
                result[attr] = to_kwargs(f_item_type, v, _converter_as_map_table(conv))
            # TODO Sequences
            elif get_origin(f_type) is list:
                old = result[attr] if attr in result else []
                f_item_type = f_type.__args__[0]
                if v_type is list:
                    v = cast(list, v)
                    if _check_iterable_type(v, f_item_type):
                        old += v
                    elif (f_item_mergeable_type := _get_mergeable(f_item_type)) and _check_iterable_type(v, dict):
                        v = cast(list[dict[str, Any]], v)
                        old += [to_kwargs(f_item_mergeable_type, v_i, _converter_as_map_table(conv)) for v_i in v]
                    else:
                        raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")
                elif _is_assignable(v_type, f_item_type):
                    old.append(v)
                elif (f_item_mergeable_type := _get_mergeable(f_item_type)) and v_type is dict:
                    v = cast(dict[str, Any], v)
                    old.append(to_kwargs(f_item_mergeable_type, v, _converter_as_map_table(conv)))
                else:
                    raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")

                result[attr] = old

            # Dict
            elif get_origin(f_type) is  dict:
                old = result[attr] if attr in result else {}
                f_key_type = f_type.__args__[0]
                f_value_type = f_type.__args__[1]
                if isinstance(v, dict):
                    # v_type 与 f_type 键值类型都匹配
                    if _check_dict_type(v, cast(tuple[Any, Any], get_args(f_type))):
                        old |= v
                    elif (f_value_mergeable_type := _get_mergeable(f_value_type)) and _check_iterable_type(v.keys(), f_key_type) and _check_iterable_type(v.values(), dict): # 只对 value 进行处理
                        v = cast(dict[f_key_type, dict[str, Any]], v)
                        old |= {k: to_kwargs(f_value_mergeable_type, v_i, _converter_as_map_table(conv)) for k, v_i in v.items()}
                    else:
                        raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")
                elif isinstance(v, tuple):
                    if _is_assignable(type(v[0]), f_key_type) and _is_assignable(type(v[1]), f_value_type): #FIXME 没类型推定？
                        old.__setitem__(*v)
                    elif (f_value_mergeable_type  := _get_mergeable(f_value_type)) and _is_assignable(type(v[0]), f_key_type) and _is_assignable(type(v[1]), dict[str, Any]):
                        v = cast(tuple[f_key_type, dict[str, Any]], v)
                        old[v[0]] = to_kwargs(f_value_mergeable_type, v[1],  _converter_as_map_table(conv))
                    else:
                        raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")
                else:
                    raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")
                result[attr] = old
            else:
                raise TypeNotMatchError(f"Get Type {type(v)}, filed {attr} type is {f_type}")


    return result
