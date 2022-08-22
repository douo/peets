from types import NoneType
from typing import Protocol, Iterable, List, Sequence, Tuple, Dict, Type, Any, Union, Optional, Callable, get_type_hints, runtime_checkable, TypeVar, cast
from itertools import chain
from dataclasses import replace as data_replace
from attr import attrib

from peets.entities.media_entity import MediaEntity

class TypeNotMatchError(Exception):
    pass

class FieldNotExistError(Exception):
    pass

@runtime_checkable
class Mergeable(Protocol):
    __dataclass_fields__: Dict


StictMapTable = List[Tuple[Tuple[str,...], Tuple[str,...], Tuple[Optional[Callable],...]]]
MapTable = List[Tuple[Union[str, Tuple[str,...]], Union[str, Tuple[str,...]]]] | List[Tuple[Union[str, Tuple[str,...]], Union[str, Tuple[str,...]], Union[NoneType, Callable, Tuple[Optional[Callable],...], "MapTable"]]]


def _make_sure_tuple(obj: Any) -> Tuple[Any, ...]:
    return obj if isinstance(obj, tuple) else(obj,)


def _make_sure_table(map_table: MapTable) -> StictMapTable:
    """
    make sure all item is tuple
    """
    return  list(map(lambda i: i if len(i) == 3 else i + (map(lambda _: None, i[1]),), #  补全省略的 converter
                map(lambda i: tuple(map(lambda j:  _make_sure_tuple(j), i)), # 确保所有元素都是 tuple
            map_table)
    )) # type: ignore

M = TypeVar('M', bound=Mergeable)


def _is_mergeable(type_: type) -> bool:
    return hasattr(type_, '__dataclass_fields__') or (_is_origin(type_, Union) and any((
        t for t in type_.__args__ if hasattr(t, '__dataclass_fields__')
    )))

def _get_mergeable(f_type: type) -> Type[Mergeable]:
    if hasattr(f_type, '__dataclass_fields__'):
        return cast(Type[Mergeable], f_type)
    elif _is_origin(f_type, Union):
        return next(cast(Type[Mergeable], t) for t in f_type.__args__ if hasattr(t, '__dataclass_fields__'))

def _is_origin(type_: type, other: type) -> bool:
    return hasattr(type_, '__origin__') and type_.__origin__ == other  # type: ignore


def _is_asignable(v_type: type, f_type: type) -> bool:
    """
    检查类型是否能赋值给目标类型
    TODO 考虑逆变、协变
    """
    return v_type is f_type or (_is_origin(f_type, Union) and v_type in f_type.__args__)

def _check_collction_type(iter_:Iterable, target: Union[type, Sequence[type]]) -> bool:
    """
    检查集合中的类型都是目标类型
    """
    for v in iter_:
        if isinstance(target, Sequence):
            for i, t in enumerate(target):
                if not _is_asignable(type(v[i]), t):
                    return False;
        elif not _is_asignable(type(v), target):
            return False
    return True

def _sanity_kwargs(target: Type[M], kwargs_: dict) -> M:
    base_fields = get_type_hints(target)

    def create_if_need(k, v):
        f_type = base_fields[k]
        if  _is_mergeable(f_type):
            return create(_get_mergeable(f_type), v)
        elif _is_origin(f_type, list) and _is_mergeable(f_type.__args__[0]):
            f_item_type = _get_mergeable(f_type.__args__[0])
            return [create(f_item_type, v_item) for v_item in v]
        elif _is_origin(f_type, dict) and _is_mergeable(f_type.__args__[1]):
            f_value_type = _get_mergeable(f_type.__args__[1])
            return { v_key: create(f_value_type, v_value) for v_key, v_value in v.items() }
        else:
            return v

    return { k: create_if_need(k, v) for k, v in kwargs_.items() }


def create(type_: Type[M], addon: Dict[str, Any], table: Optional[MapTable] = None) -> M:
    kwargs_ = to_kwargs(type_, addon, table)
    kwargs_ = _sanity_kwargs(type_, kwargs_)
    return type_(**kwargs_)


def replace(base:M, addon: Dict[str, Any], table: Optional[MapTable] = None) -> M:
    type_ = type(base)
    kwargs_ = to_kwargs(type_, addon, table)
    kwargs_ = _sanity_kwargs(type_, kwargs_)
    return data_replace(base, **kwargs_)

def to_kwargs(type_: Type[Mergeable], addon: Dict[str, Any], table: Optional[MapTable] = None) -> Dict:
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
            if _is_asignable(v_type, f_type):
                result[attr] = v
            elif _is_mergeable(f_type) and v_type is dict:
                v = cast(Dict[str, Any], v)
                f_item_type = _get_mergeable(f_type)
                result[attr] = to_kwargs(f_item_type, v, _converter_as_map_table(conv))

            # TODO Sequences
            elif _is_origin(f_type, list):
                old = result[attr] if attr in result else []
                f_item_type = f_type.__args__[0]
                if v_type is list:
                    v = cast(List, v)
                    if _check_collction_type(v, f_item_type):
                        old += v
                    elif _is_mergeable(f_item_type) and _check_collction_type(v, dict):
                        v = cast(List[Dict[str, Any]], v)
                        f_item_mergeable_type = _get_mergeable(f_item_type)
                        old += [to_kwargs(f_item_mergeable_type, v_i, _converter_as_map_table(conv)) for v_i in v]
                    else:
                        raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")
                elif _is_asignable(v_type, f_item_type):
                    old.append(v)
                elif _is_mergeable(f_item_type) and v_type is dict:
                    v = cast(Dict[str, Any], v)
                    f_item_mergeable_type = _get_mergeable(f_item_type)
                    old.append(to_kwargs(f_item_mergeable_type, v, _converter_as_map_table(conv)))
                else:
                    raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")

                result[attr] = old

            # Dict
            elif _is_origin(f_type, dict):
                old = result[attr] if attr in result else {}
                f_key_type = f_type.__args__[0]
                f_value_type = f_type.__args__[1]
                if v_type is dict:
                    v = cast(Dict, v)
                    if _check_collction_type(v.items(), f_type.__args__): # v_type 与 f_type 键值类型都匹配
                        old |= v
                    elif _is_mergeable(f_value_type) and _check_collction_type(v.keys(), f_key_type) and _check_collction_type(v.values(), dict): # 只对 value 进行处理
                        v = cast(Dict[f_key_type, Dict[str, Any]], v)
                        f_value_mergeable_type  = _get_mergeable(f_value_type)
                        old |= {k: to_kwargs(f_value_mergeable_type, v_i, _converter_as_map_table(conv)) for k, v_i in v.items()}
                    else:
                        raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")
                elif v_type is tuple:
                    if _is_asignable(type(v[0]), f_key_type) and _is_asignable(type(v[1]), f_value_type): #FIXME 没类型推定？
                        old.__setitem__(*v)
                    elif _is_mergeable(f_value_type) and _is_asignable(type(v[0]), f_key_type) and _is_asignable(type(v[1]), Dict[str, Any]):
                        v = cast(Tuple[f_key_type, Dict[str, Any]], v)
                        f_value_mergeable_type  = _get_mergeable(f_value_type)
                        old[v[0]] = to_kwargs(f_value_mergeable_type, v[1],  _converter_as_map_table(conv))
                    else:
                        raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")
                else:
                    raise TypeNotMatchError(f"Get Type {v_type}, filed {attr} type is {f_type}")
                result[attr] = old
            else:
                raise TypeNotMatchError(f"Get Type {type(v)}, filed {attr} type is {f_type}")


    return result
