import inspect
from abc import ABC, abstractmethod

from types import FunctionType
from typing import Callable, Generic, TypeAlias, TypeVar, get_type_hints

from lxml import etree as ET

from peets.entities import MediaEntity
from peets.util.type_utils import check_iterable_type

T = TypeVar("T", bound=MediaEntity)

class Connector(ABC, Generic[T]):
    def __init__(
        self,
        name: str
    ) -> None:
        self.name = name

    @abstractmethod
    def generate(self, media: T) -> str:
        pass

    @property
    @abstractmethod
    def available_type(self) -> list[str]:
        pass

    def is_available(self, media: T) -> bool:
        return type(media).__name__.lower() in [
            t.lower() for t in self.available_type
        ]

global connectors
connectors: list[Connector] = []


def register(*p: Connector):
    global connectors
    connectors += p

def connector(media: T) -> list[Connector[T]]:
    global connectors
    return [
        c
        for c in connectors
        if c.is_available(media)
    ]



# TODO 追加一个 trigger ，只有 trigger 返回 True, 该 Item 才会生效
# TODO trigger 默认可以是 field not None
NfoItem: TypeAlias = (
    str  # element 与 field name 相同
    | tuple[str, str]  # element field name
    # 参数支持 field name、 entity、root element
    # 返回值支持可被转换成 str 的任意类型
    | tuple[str, Callable]
    # 或 ET.Element 或 list[ET.Element] 或 None
    | Callable
)

NfoTable: TypeAlias = list[NfoItem]


def create_element(tag: str, text: str | None, **extra) -> ET._Element:
    ele = ET.Element(tag, **extra)
    if text:
        ele.text = text
    return ele


def inflate(root: ET._Element, entity: MediaEntity, table: NfoTable):
    for item in table:
        _process(item, root, entity)


def _to_text(value) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def _process(item: NfoItem, root: ET._Element, entity: MediaEntity):
    return_type = None

    match item:
        case str() as tag:
            child = ET.Element(tag)
            child.text = _to_text(getattr(entity, tag))
        case str() as tag, str() as attr:
            child = ET.Element(tag)
            child.text = _to_text(getattr(entity, attr))
        case str() as tag, FunctionType() as conv:
            child = ET.Element(tag)
            value, return_type = _process_callable(conv, root, entity)
            child.text = _to_text(value)
        case FunctionType() as conv:
            child, return_type = _process_callable(conv, root, entity)
        case _:
            raise ValueError(f"Unrecognized Nfoitem {item=} {type(item)=}")

    if return_type == ET._Element or isinstance(child, ET._Element):
        root.append(child)
    elif return_type == list[ET._Element] or (
        isinstance(child, list) and check_iterable_type(child, ET._Element)
    ):
        for c in child:
            root.append(c)
    elif child is None:
        return
    else:
        raise ValueError(f"Unrecognized child {child=} {type(child)=}")


def _process_callable(conv: FunctionType, root: ET._Element, entity: MediaEntity):
    args, _, _, _, _, _, annts = inspect.getfullargspec(conv)

    # TODO return type guard
    return_type = annts.get("return")

    type_hints = get_type_hints(type(entity))
    entity_type = type(entity).__name__.lower()
    print(f"{entity_type=}")
    def _to_param(arg: str, annt: type | None):
        if arg == "root" and annt is ET._Element:
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

    params = (_to_param(arg, annts.get(arg)) for arg in args)
    return conv(*params), return_type
