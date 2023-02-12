from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from reflink import supported_at
from datetime import datetime
from peets.config import Config, Op
from peets._plugin import Plugin


@dataclass
class Record:
    source: Path
    op: Op
    dest: Path
    date: datetime


class Library:
    def __init__(self, path: Path):
        self.path = path
        path.mkdir(parents=True, exist_ok=True)
        self._load_record()

        self._load_config()
        if self.config.op == Op.Reflink:
            if not supported_at(self.path):
                self.config.op = Op.Copy
                print("lib_path {path} is not supported reflink. fallback to copy.")

        self._init_plugin()

    def _load_record(self):
        record_path = self.path.joinpath(".record.pickle")
        self.record_list = []
        if record_path.exists():
            with record_path.open("rb") as f:
                self.record_list = pickle.load(f)

    def _load_config(self):
        self.config = Config()
        user_config = Path.home().joinpath(".config/peets/config.yml")
        lib_config = self.path.joinpath(".peets.yml")
        self.config.merge(user_config)
        self.config.merge(lib_config)

    def _init_plugin(self):
        self.manager = Plugin(self)

    def _save_record(self):
        record_path = self.path.joinpath(".record.pickle")
        with record_path.open("wb") as f:
            pickle.dump(self.record_list, f)

    def record(self, source: Path, op: Op, dest: Path):
        self.record_list.append(
            Record(source.absolute(), op, dest.relative_to(self.path), datetime.now())
        )
        self._save_record()
