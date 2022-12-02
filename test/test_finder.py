from pathlib import Path

from peets.const import VIDEO_CONTAINERS
from peets.finder import traverse


def test_traverse_single_file(create_file):
    """
    识别单个文件
    """
    # 创建 10 个媒体文件
    files = create_file([f"test.{suf}" for suf in VIDEO_CONTAINERS[1:10]])

    # 单个文件
    for f in files:
        res = list(traverse(f))[0]
        assert res == f

    # 多个文件
    res = traverse(*files)
    assert set(res) == set(files)


def test_traverse_folder(create_file, tmp_path):
    """
    识别目录内的媒体文件
    """
    # 创建 10 个媒体文件
    files = create_file([f"test.{suf}" for suf in VIDEO_CONTAINERS[1:10]])

    # 目录内多个文件
    res = traverse(tmp_path)
    assert set(res) == set(files)

    # 非媒体文件不被识别
    other = create_file([f"test.{i}" for i in range(1, 10)])
    res = traverse(tmp_path)
    assert set(res) == set(files)


def test_traverse_mixed(create_file, tmp_path):
    """
    识别目录内的媒体文件
    """
    # 创建 10 个媒体文件
    p1 = tmp_path.joinpath("1")
    files_1 = create_file([f"test.{suf}" for suf in VIDEO_CONTAINERS[1:10]], p1)

    p2 = tmp_path.joinpath("2")
    files_2 = create_file([f"test.{suf}" for suf in VIDEO_CONTAINERS[1:10]], p2)

    # 多个目录内文件
    res = traverse(p1, p2)
    assert set(res) == set(files_1 + files_2)

    # 混合目录及文件
    files = create_file([f"test.{suf}" for suf in VIDEO_CONTAINERS[1:10]])

    res = traverse(p1, p2, *files)
    assert set(res) == set(files_1 + files_2 + files)


def test_traverse_hidden_file(create_file):
    """
    能识别显示指定的隐藏文件
    """
    hidden = create_file(f".test.{VIDEO_CONTAINERS[-1]}")

    res = list(traverse(hidden))[0]
    assert res == hidden


def test_traverse_hidden_file_inside_folder(create_file, tmp_path):
    """
    目录中的隐藏文件不被识别
    """
    create_file(f".test.{VIDEO_CONTAINERS[-1]}")
    res = traverse(tmp_path)
    assert not any(res)


def test_traverse_file_inside_hidden_folder(create_file, tmp_path):
    """
    隐藏目录中的文件不被识别
    """
    create_file(f"test.{VIDEO_CONTAINERS[-1]}", ".hidden")
    res = traverse(tmp_path)
    assert not any(res)


def test_traverse_duplicate_path(create_file, tmp_path):
    """
    目录存在重复不产生重复文件
    """
    p1 = tmp_path.joinpath("1")
    create_file([f"test.{suf}" for suf in VIDEO_CONTAINERS[1:10]], p1)

    create_file([f"test.{suf}" for suf in VIDEO_CONTAINERS[1:10]])

    res = list(traverse(tmp_path, p1))
    except_res = list(traverse(tmp_path))

    assert len(res) == len(except_res)
