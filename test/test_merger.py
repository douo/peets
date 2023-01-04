from dataclasses import asdict, dataclass, field

from pytest import raises

from peets.merger import TypeNotMatch, create, replace, to_kwargs, Option


@dataclass(kw_only=True, frozen=True)
class People:
    name: str = field(kw_only=False)
    title: str | None = None
    number: int = 0
    age: int | None = None
    # parent:tuple["People", "People"]
    pets: list[str] = field(default_factory=list)
    tools: dict[str, int] = field(default_factory=dict)
    pair: tuple[int, str] = (0, "0")


@dataclass(kw_only=True, frozen=True)
class Department:
    name: str
    manager: People | None = None
    employee: list[People] = field(default_factory=list)
    position: dict[int, People] = field(default_factory=dict)


def test_type_0(dummy):
    p1 = dummy(People)
    addon = asdict(p1)
    assert to_kwargs(People, addon) == addon
    assert to_kwargs(
        People, {"name": "Demo", "year": 20, "demo": "something else"}
    ) == {"name": "Demo"}


def test_type_1(dummy):
    p1 = dummy(People)
    p1_dict = asdict(p1)
    addon = {k + "_": v for k, v in p1_dict.items()}
    assert to_kwargs(People, addon, [(k[:-1], k) for k in addon.keys()]) == p1_dict


def test_type_2(dummy):
    addon = {"account": "abcdefg", "pet1": "cat", "pet2": "dog"}
    convert_table = [
        ("name", lambda account: account[:-1]),
        ("pets", lambda pet1, pet2: [pet1, pet2]),
    ]

    assert to_kwargs(People, addon, convert_table) == {
        "name": "abcdef",
        "pets": ["cat", "dog"],
    }


def test_type_3(dummy):
    p = dummy(People)
    addon = {"manager": asdict(p)}
    assert to_kwargs(Department, addon) == {"manager": asdict(p)}

    addon = {"manager": {k + "_": v for k, v in asdict(p).items()}}

    convert_table = [
        (
            "manager",
            ("manager", [(k[:-1], k) for k in addon["manager"].keys()]),
        )
    ]

    assert to_kwargs(Department, addon, convert_table) == {"manager": asdict(p)}


def test_assign_auto_convert(dummy):
    # 自动简单类型转换
    @dataclass(kw_only=True, frozen=True)
    class Primitive:
        int_: int = 0
        float_: float = 0.0
        bool_: bool = False
        complex_: complex = 0
        str_optional: str | None = None
        int_optional: int | None = None

    addon = {"int_": "1",
             "float_": "1.0",
             "bool_": "True",
             "complex_": "(1+1j)",
             "str_optional": "str_optional",
             "int_optional": "1"
             }

    assert to_kwargs(Primitive, addon) == {
        "int_": 1,
        "float_": 1.0,
        "bool_": True,
        "complex_": (1 + 1j),
        "str_optional": "str_optional",
        "int_optional": 1
    }


def test_assign_collection(dummy):
    addon = {
        "name": "dummy",
        "pet": "dog",
        "screw": 10,
    }

    convert_table = [
        # 目标类型是 list/dict
        # addon 对应类型是 item/key-value tuple
        # 会自动创建集合
        ("pets", lambda pet: pet),
        ("tools", lambda screw: ("screw", screw)),
    ]
    assert to_kwargs(People, addon, convert_table) == {
        "name": "dummy",
        "tools" : {"screw":10},
        "pets" : ["dog"]
    }

    addon = {
        "name": "dummy",
        "pet1": "dog",
        "pet2": "cat",
        "screw": 10,
        "knife": 5,
        "cows": ["cow1", "cow2"],
        "box" : {"axe":1}
    }

    convert_table = [
        # 目标类型是 list/dict
        # addon 对应类型是 item/key-value tuple
        # 会自动添加到集合中
        ("pets", lambda pet1: pet1),
        ("pets", "pet2"),
        ("pets", "cows"),
        ("tools", lambda screw: ("screw", screw)),
        ("tools", lambda knife: ("knife", knife)),
        ("tools", "box")
    ]
    kwargs = to_kwargs(People, addon, convert_table)

    assert addon["pet1"] in kwargs["pets"]
    assert addon["pet2"] in kwargs["pets"]
    assert all(cow in kwargs["pets"] for cow in addon["cows"])
    assert kwargs["tools"] == {
        "screw": 10,
        "knife": 5,
        "axe": 1
    }


def test_assign_multiple(dummy):
    addon = {
        "name": "dummy",
        "title": "Worker,2",
    }
    convert_table = [
        (  # 单个 key 赋值给多个 fields
            ("title", "number"),
            lambda title: (title.split(",")[0], title.split(",")[-1]),
        )
    ]

    assert to_kwargs(People, addon, convert_table) == {
        "name": "dummy",
        "title": "Worker",
        "number": 2
    }


def test_assign_src_used(dummy):
    # 如果已经在 map_table 定义过的 key ，不会再自动赋值到同名字段
    addon = {"name": "Name", "age": 30, "title": "Worker", "number": 2}
    assert to_kwargs(
        People,
        addon,
        [("title", lambda title, number: f"{title},{number}")],
    ) == {"name": "Name", "age": 30, "title": "Worker,2"}

def test_empty_addon():
    addon = {}
    assert to_kwargs(People, addon) == {}


def test_field_not_exist():
    addon = {"name": "Name", "pets": [1, 2]}
    with raises(KeyError):
        to_kwargs(People, addon, [("not_exist", "pets")])

def test_key_not_exist():
    # key 在 addon 不存在
    # 默认行为，将参数作为 None 传入
    assert to_kwargs(
        People, {"name": "Name"}, [("pets", lambda not_exist: "" if not_exist else "1")]
    ) == {"name": "Name", "pets": ["1"]}

    # 1. 抛出异常
    with raises(KeyError):
        to_kwargs(
            People, {"name": "Name"}, [("pets", lambda not_exist: "" if not_exist else "1", Option.KEY_NOT_EXIST_RAISE)]
        )
    # 2. 任意 key 不存在就不调用
    to_kwargs(
        People, {"name": "Name", "test": "test"},
        [("pets", lambda test, not_exist: "test", Option.KEY_NOT_EXIST_IGNORE_ANY)]
    ) == {"name": "Name"}

    # 2. 所有 key 不存在才不调用
    to_kwargs(
        People, {"name": "Name", "test": "test"},
        [("title", lambda test, not_exist: test+str(not_exist), Option.KEY_NOT_EXIST_IGNORE_ALL)]
    ) == {"name": "Name", "title":"testNone"}
    to_kwargs(
        People, {"name": "Name"},
        [("title", lambda test, not_exist: test+str(not_exist), Option.KEY_NOT_EXIST_IGNORE_ALL)]
    ) == {"name": "Name"}
    to_kwargs(
        People, {"name": "Name"},
        [("title", lambda test, not_exist: str(test)+str(not_exist), Option.KEY_NOT_EXIST_IGNORE_ALL)]
    ) == {"name": "Name", "title": "NoneNone"}


def test_to_kwargs_type_not_match():
    addon = {
        "name": "Demo",
        "age": "abc",
    }

    with raises(TypeNotMatch):
        to_kwargs(People, addon)

    addon = {"name": "Demo", "pets": 1}

    with raises(TypeNotMatch):
        to_kwargs(People, addon)

    addon = {"name": "Demo", "tools": (1, 1)}

    with raises(TypeNotMatch):
        to_kwargs(People, addon)

    # 对集合类也同样适用
    addon = {"name": "Demo", "pets": [1, 2, 3]}

    with raises(TypeNotMatch):
        to_kwargs(People, addon)

    addon = {"name": "Demo", "tools": {1: 1}}

    with raises(TypeNotMatch):
        to_kwargs(People, addon)

    # 混合类型的集合会检查所有项

    addon = {"name": "Demo", "pets": ["dog", 2, "cat"]}

    with raises(TypeNotMatch):
        to_kwargs(People, addon)

    addon = {"name": "Demo", "tools": {"pen": 1, 3: "disc"}}

    with raises(TypeNotMatch):
        to_kwargs(People, addon)


def test_to_kwargs_nested_map_table():

    addon = {
        "department": "Demo",
        "bigman": {"name": "Demo", "pets": ["dog", "cat"], "label": "M"},
        "worker": [
            {
                "name": "W1",
                "pets": "dog",
            },
            {"name": "W2", "label": "L", "tools": {"pen": 1}},
        ],
        "position": {1: {"name": "p1", "label": "P"}},
    }

    people_table = [("title", "label")]

    table = [
        ("name", "department"),
        ("manager", ("bigman", people_table)),
        ("employee", ("worker", people_table)),
    ]

    assert to_kwargs(Department, addon, table) == {
        "name": "Demo",
        "manager": {"name": "Demo", "title": "M", "pets": ["dog", "cat"]},
        "employee": [
            {"name": "W1", "title": None, "pets": ["dog"]},
            {"name": "W2", "title": "L", "tools": {"pen": 1}},
        ],
        "position": {
            1: {
                "name": "p1",
            }
        },
    }


def test_create():
    kwargs_ = {
        "name": "Demo",
        "title": "Worker",
        "number": -1,
        "age": 20,
        "pets": ["dog"],
        "tools": {"pen": 1},
        "pair": (1, "1"),
    }

    assert create(People, kwargs_).__dict__ == kwargs_

    kwargs_ = {
        "name": "Demo",
        "manager": {"name": "Demo", "pets": ["dog", "cat"]},
        "employee": [
            {"name": "W1", "title": None, "pets": ["dog"]},
            {"name": "W2", "title": "L", "tools": {"pen": 1}},
        ],
        "position": {1: {"name": "P1", "title": "P"}},
    }

    dep = create(Department, kwargs_)

    assert dep.name == kwargs_["name"]
    assert dep.manager.name == kwargs_["manager"]["name"]
    assert dep.position[1].name == kwargs_["position"][1]["name"]

    for i, e in enumerate(dep.employee):
        assert e.name == kwargs_["employee"][i]["name"]

    kwargs_ = {
        "name": "Demo",
        "manager": People(name="Demo", pets=["dog", "cat"]),
        "employee": [
            People(name="W1", pets=["dog"]),
            People(name="W2", title="L", tools={"pen": 1}),
        ],
        "position": {1: People(name="P1", title="P")},
    }

    dep = create(Department, kwargs_)

    assert dep.name == kwargs_["name"]
    assert dep.manager.name == kwargs_["manager"].name
    assert dep.position[1].name == kwargs_["position"][1].name

    for i, e in enumerate(dep.employee):
        assert e.name == kwargs_["employee"][i].name


def test_replace():
    p = People(name="Hello", number=1)

    kwargs_ = {
        "name": "Demo",
        "title": "Worker",
        "age": 20,
        "pets": ["dog"],
        "tools": {"pen": 1},
    }

    n_p = replace(p, kwargs_)

    assert n_p != p
    assert n_p.name == kwargs_["name"]
    assert n_p.title == kwargs_["title"]
    assert n_p.pets == kwargs_["pets"]
    assert n_p.tools == kwargs_["tools"]
    assert n_p.number == p.number

    dep = Department(
        name="name",
        manager=People(name="m", title="m", number=5),
        employee=[People(name="w", title="w", number=1)],
        position={1: People(name="p")},
    )

    kwargs_ = {
        "name": "Demo",
        "manager": {"name": "Demo", "pets": ["dog", "cat"]},
        "employee": [
            {"name": "W1", "title": None, "pets": ["dog"]},
            {"name": "W2", "title": "L", "tools": {"pen": 1}},
        ],
        "position": {1: {"name": "P1", "title": "P"}},
    }

    n_dep = replace(dep, kwargs_)

    assert n_dep.name == kwargs_["name"]

    # 字段类型 Mergeable 不会嵌套 replace 会直接创建新实例
    assert n_dep.manager.name == kwargs_["manager"]["name"]
    assert n_dep.manager.pets == kwargs_["manager"]["pets"]
    assert n_dep.manager.number != dep.manager.number

    assert len(n_dep.employee) == len(kwargs_["employee"])
    for i, e in enumerate(n_dep.employee):
        assert e.name == kwargs_["employee"][i]["name"]

    assert n_dep.position[1].name == kwargs_["position"][1]["name"]
