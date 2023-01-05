import inspect
from types import FunctionType
from typing import Any, Callable, cast, get_type_hints

from lxml import etree as ET

from peets.entities import MediaEntity

NfoItem = (
    str  # element 与 field name 相同
    | (str, str)  # element field name
    # 参数支持 field name、 entity、root element
    # 返回值支持可被转换成 str 的任意类型，或 ET.Element 或 list[ET.Element]
    | Callable
)

NfoTable = list[NfoItem]


def _to_text(value) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def _process(item: NfoItem, root: ET.Element, entity: MediaEntity):
    match item:
        case str() as tag:
            child = ET.Element(tag)
            child.text = _to_text(getattr(entity, tag))
        case str() as tag, str() as attr:
            child = ET.Element(tag)
            child.text = _to_text(getattr(entity, attr))
        case FunctionType() as conv:
            child = _process_callable(conv, root, entity)
        case _:
            raise ValueError(f"Unrecognized Nfoitem {item=} {type(item)=}")

    if isinstance(child, list):
        for c in child:
            root.append(c)
    elif isinstance(child, ET.Element):
        root.append(child)
    else:
        raise ValueError(f"Unrecognized child {child=} {type(child)=}")

def _process_callable(conv: FunctionType, root: ET.Element, entity: MediaEntity):
    args, _, _, _, _, _, annts = inspect.getfullargspec(conv)

    # TODO return type guard
    return_type = annts.get('return')

    type_hints = get_type_hints(entity)
    entity_type = str(type(entity)).lower()

    def _to_param(arg: str, annt: type | None):
        if arg == "root" and annt is ET.Element:
            return root
        if arg in ("entity", entity_type) and annt and issubclass(annt, type(entity)):
            return entity
        if arg in type_hints:
            return getattr(entity, arg)
        if arg == "root":
            return root
        if arg in ("entity", entity_type):
            return entity
        raise ValueError(f"unknown parameter name {arg=}")

    params = (_to_param(arg, annts[arg]) for arg in args)
    result = conv(*params)

    if return_type == ET.Element or isinstance(result, ET.Element):
        return result
    elif return_type == list[ET.Element] or (isinstance(result, list) and check_iterable_type(result, ET.Element)):
        return result
    elif result is None:
        return
    else:
        child = ET.Element(tag)
        child.text = _to_text(result)
        return child


def inflate(root: ET.Element, entity: MediaEntity, table: NfoTable):
    for item in table:
        _process(item, root, entity)
        _process(item, root, entity)
