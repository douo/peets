import pytest

from dataclasses import dataclass, field
from typing import Dict, List, Optional, get_type_hints

from peets.merger import FieldNotExistError, to_kwargs, replace, TypeNotMatchError, create


@dataclass(kw_only=True, frozen=True)
class People:
    name: str = field(kw_only=False)
    title: Optional[str] = None
    level: int = 0
    age: Optional[int] = None
    # parent:tuple["People", "People"]
    pets: List[str] = field(default_factory=list)
    tools: Dict[str,int] =  field(default_factory=dict)


@dataclass(kw_only=True, frozen=True)
class Department:
    name: str
    manager: Optional[People] = None
    employee: List[People] = field(default_factory=list)
    position: Dict[int, People] = field(default_factory=dict)

def test_to_kwargs():
    addon = {
        "name" : "Demo",
        "year" : 20,
        "demo" : "something else"
    }

    assert to_kwargs(People, addon) == {
        "name": "Demo"
    }

    addon = {
        "name" : "Demo",
        "title" : "Worker",
        "level" : -1,
        "age" : 20,
        "pets" : ["dog"],
        "tools" : {"pen": 1}
    }

    assert to_kwargs(People, addon) == addon

    addon = {
        "account" : "Demo",
        "age" : "30",
        "pet1" : "dog",
        "pet2" : "cat",
        "title" : "Worker,2",
        "tools" : {"pen": 1}
    }

    # table 的结构
    # addon key nanme, target field name, converter
    # 支持多对一，一对多的转换， converter 的数量需要与 target field 一一对应，converter 的参数与 key name 一一对应
    # (addon key nanme,...), (target field name,...), (converter,...)
    map_table = [("account", "name"), # 变量名转换， converter 省略表示直接赋值
                 ("age", "age", lambda age: int(age)), # converter
                 (("pet1","pet2"), "pets", lambda p1,p2: [p1,p2]),
                 ("title", ("title", "level"),
                  (None, lambda title: int(title.split(',')[-1])) # converter 为 None 表示直接转换
                  )
                 ]

    assert to_kwargs(People, addon, map_table) == {
        "name" : "Demo",
        "title" : "Worker,2",
        "level" : 2,
        "age" : 30,
        "pets" : ["dog", "cat"],
        "tools" : {"pen": 1}
    }

    # 如果已经在 map_table 定义过的 key ，不会再自动赋值到同名字段
    addon = {
        "name" : "Name",
        "age" : 30,
        "title" : "Worker",
        "level" : 2
    }
    assert to_kwargs(People, addon, [
        (("title", "level"),
         "title",
         lambda title, level: f"{title},{level}")
    ]) == {
        "name" : "Name",
        "age" : 30,
        "title" : "Worker,2"
    }


def test_to_kwargs_collections():
    # 目标类型是 list 或 dict
    # addon 对应类型是 item 或 key-value tuple
    # 会自动添加到原先的集合中
    addon = {
        "name" : "Name",
        "pets" : "dog",
        "pet2" : "cat",
        "tools" : ("pen", 1),
        "other-tools": ("disc", 10)
    }

    assert to_kwargs(People, addon) == {
        "name" : "Name",
        "pets" : ["dog"],
        "tools" : {"pen": 1}
    }

    assert to_kwargs(People, addon, [
        ("pet2", "pets"),
        ("other-tools", "tools")
    ]) == {
        "name" : "Name",
        "pets" : ["cat", "dog"], # map_table 中的 key 优先处理
        "tools" : {"pen": 1, "disc" : 10}
    }

def test_to_kwargs_empty_addon():
    addon = {
    }

    assert to_kwargs(People, addon) == {}


def test_tokwargs_field_not_exist():
    addon = {
        "name" : "Name",
        "pets" : [1,2]
    }

    with pytest.raises(FieldNotExistError):
        to_kwargs(People, addon, [("pets", "not_exist")])

def test_to_kwargs_type_not_match():
    addon = {
        "name" : "Demo",
        "age" : "abc",
    }

    with pytest.raises(TypeNotMatchError):
        to_kwargs(People, addon)


    addon = {
        "name" : "Demo",
        "pets" : 1
    }

    with pytest.raises(TypeNotMatchError):
        to_kwargs(People, addon)

    addon = {
        "name" : "Demo",
        "tools" : (1,1)
    }

    with pytest.raises(TypeNotMatchError):
        to_kwargs(People, addon)


    # 对集合类也同样适用
    addon = {
        "name" : "Demo",
        "pets" : [1,2,3]
    }

    with pytest.raises(TypeNotMatchError):
        to_kwargs(People, addon)

    addon = {
        "name" : "Demo",
        "tools" : {1:1}
    }

    with pytest.raises(TypeNotMatchError):
        to_kwargs(People, addon)


    # 混合类型的集合会检查所有项

    addon = {
        "name" : "Demo",
        "pets" : ["dog", 2, "cat"]
    }

    with pytest.raises(TypeNotMatchError):
        to_kwargs(People, addon)

    addon = {
        "name" : "Demo",
        "tools" : {"pen": 1, 3: "disc"}
    }

    with pytest.raises(TypeNotMatchError):
        to_kwargs(People, addon)

def test_to_kwargs_nested_map_table():

    addon = {
        "department": "Demo",
        "manager": {
            "name": "Demo",
            "pets": ["dog", "cat"],
            "label": "M"
        },
        "worker": [
            {
                "name": "W1",
                "pets": "dog" ,
            },
            {
                "name": "W2",
                "label": "L",
                "tools": {"pen": 1}
            }
        ],
        "position": {
            1: {
                "name": "p1",
                "label": "P"
            }
        }
    }

    table = [
        ("department", "name"),
        ("worker", "employee",
         lambda ps: [to_kwargs(People, p, [("label", "title")]) for p in ps])
    ]

    assert to_kwargs(Department, addon, table) == {
        "name": "Demo",
        "manager": {
            "name": "Demo",
            "pets": ["dog", "cat"]
        },
        "employee": [
            {
                "name": "W1",
                "title": None,
                "pets": ["dog"]
            },
            {
                "name": "W2",
                "title": "L",
                "tools": {"pen": 1}
            }
        ],
        "position": {
            1: {
                "name": "p1",
            }
        }
    }



def test_create():
    kwargs_ =  {
        "name" : "Demo",
        "title" : "Worker",
        "level" : -1,
        "age" : 20,
        "pets" : ["dog"],
        "tools" : {"pen": 1}
    }

    assert create(People, kwargs_).__dict__ == kwargs_


    kwargs_ = {
        "name": "Demo",
        "manager": {
            "name": "Demo",
            "pets": ["dog", "cat"]
        },
        "employee": [
            {
                "name": "W1",
                "title": None,
                "pets": ["dog"]
            },
            {
                "name": "W2",
                "title": "L",
                "tools": {"pen": 1}
            }
        ],
        "position": {
            1: {
                "name": "P1",
                "title": "P"
            }
        }
    }

    dep = create(Department, kwargs_)

    assert dep.name == kwargs_["name"]
    assert dep.manager.name == kwargs_["manager"]["name"]
    assert dep.position[1].name == kwargs_["position"][1]["name"]

    for i, e in enumerate(dep.employee):
        assert e.name == kwargs_["employee"][i]["name"]

    kwargs_ = {
        "name": "Demo",
        "manager": People(
            name= "Demo",
            pets= ["dog", "cat"]
        ),
        "employee": [
            People(
                name= "W1",
                pets= ["dog"]
            ),
            People(
                name= "W2",
                title= "L",
                tools= {"pen": 1}
            )
        ],
        "position": {
            1: People(
                name= "P1",
                title= "P")
        }
    }

    dep = create(Department, kwargs_)

    assert dep.name == kwargs_["name"]
    assert dep.manager.name == kwargs_["manager"].name
    assert dep.position[1].name == kwargs_["position"][1].name

    for i, e in enumerate(dep.employee):
        assert e.name == kwargs_["employee"][i].name

def test_replace():
    p = People(name="Hello", level=1)

    kwargs_ =  {
        "name" : "Demo",
        "title" : "Worker",
        "age" : 20,
        "pets" : ["dog"],
        "tools" : {"pen": 1}
    }

    n_p = replace(p, kwargs_)

    assert n_p != p
    assert n_p.name == kwargs_["name"]
    assert n_p.title == kwargs_["title"]
    assert n_p.pets == kwargs_["pets"]
    assert n_p.tools == kwargs_["tools"]
    assert n_p.level == p.level


    dep = Department(name="name",
                     manager=People(name="m", title="m", level=5),
                     employee= [People(name="w", title="w", level=1)],
                     position={1 : People(name="p")}
                     )

    kwargs_ = {
        "name": "Demo",
        "manager": {
            "name": "Demo",
            "pets": ["dog", "cat"]
        },
        "employee": [
            {
                "name": "W1",
                "title": None,
                "pets": ["dog"]
            },
            {
                "name": "W2",
                "title": "L",
                "tools": {"pen": 1}
            }
        ],
        "position": {
            1: {
                "name": "P1",
                "title": "P"
            }
        }
    }

    n_dep = replace(dep, kwargs_)

    assert n_dep.name == kwargs_["name"]

    # 字段类型 Mergeable 不会嵌套 replace 会直接创建新实例
    assert n_dep.manager.name == kwargs_["manager"]["name"]
    assert n_dep.manager.pets == kwargs_["manager"]["pets"]
    assert n_dep.manager.level != dep.manager.level

    assert len(n_dep.employee) == len(kwargs_["employee"])
    for i, e in enumerate(n_dep.employee):
        assert e.name == kwargs_["employee"][i]["name"]

    assert n_dep.position[1].name == kwargs_["position"][1]["name"]
