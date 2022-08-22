from pathlib import Path

from peets.finder import traverse, MOVIE_CONTAINERS

def _create_file(name:str, parent:Path):
    f = parent.joinpath(name)
    parent.mkdir(parents=True, exist_ok=True)
    f.touch()
    return f

def test_traverse_single_file(tmp_path:Path):
    """
    识别单个文件
    """
    # 创建 10 个媒体文件
    files = [_create_file(f"test.{suf}", tmp_path)
        for suf in MOVIE_CONTAINERS[1:10]
     ]

    # 单个文件
    for f in files:
        res = list(traverse(f))[0]
        assert res ==  f

    # 多个文件
    res = traverse(*files)
    assert set(res) == set(files)


def test_traverse_folder(tmp_path):
    """
    识别目录内的媒体文件
    """
    # 创建 10 个媒体文件
    files = [_create_file(f"test.{suf}", tmp_path)
        for suf in MOVIE_CONTAINERS[1:10]
     ]

    # 目录内多个文件
    res = traverse(tmp_path)
    assert set(res) == set(files)

    # 非媒体文件不被识别
    other = [_create_file(f"test.{i}", tmp_path)
            for i in range(1,10)
     ]
    res = traverse(tmp_path)
    assert set(res) == set(files)




def test_traverse_mixed(tmp_path):
    """
    识别目录内的媒体文件
    """
    # 创建 10 个媒体文件
    p1 = tmp_path.joinpath("1")
    files_1 = [_create_file(f"test.{suf}", p1)
        for suf in MOVIE_CONTAINERS[1:10]
     ]

    p2 = tmp_path.joinpath("2")
    files_2 = [_create_file(f"test.{suf}", p2)
        for suf in MOVIE_CONTAINERS[1:10]
     ]

    # 多个目录内文件
    res = traverse(p1,p2)
    assert set(res) == set(files_1 +files_2)

    # 混合目录及文件
    files = [_create_file(f"test.{suf}", tmp_path)
        for suf in MOVIE_CONTAINERS[1:10]
     ]

    res = traverse(p1,p2,*files)
    assert set(res) == set(files_1 + files_2 + files)


def test_traverse_hidden_file(tmp_path:Path):
    """
    能识别显示指定的隐藏文件
    """
    hidden = _create_file(f".test.{MOVIE_CONTAINERS[-1]}", tmp_path)

    res = list(traverse(hidden))[0]
    assert res == hidden

def test_traverse_hidden_file_inside_folder(tmp_path:Path):
    """
    目录中的隐藏文件不被识别
    """
    hidden = _create_file(f".test.{MOVIE_CONTAINERS[-1]}", tmp_path)
    res = traverse(tmp_path)
    assert not any(res)


def test_traverse_file_inside_hidden_folder(tmp_path:Path):
    """
    隐藏目录中的文件不被识别
    """
    hidden = _create_file(f"test.{MOVIE_CONTAINERS[-1]}", tmp_path.joinpath(".hidden"))
    res = traverse(tmp_path)
    assert not any(res)


def test_traverse_duplicate_path(tmp_path:Path):
    """
    目录存在重复不产生重复文件
    """
    p1 = tmp_path.joinpath("1")
    files_1 = [_create_file(f"test.{suf}", p1)
        for suf in MOVIE_CONTAINERS[1:10]
     ]

    files = [_create_file(f"test.{suf}", tmp_path)
        for suf in MOVIE_CONTAINERS[1:10]
     ]

    res = list(traverse(tmp_path, p1))
    except_res =  list(traverse(tmp_path))

    assert len(res) == len(except_res)
