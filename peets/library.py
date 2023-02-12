from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from peets.naming import Op
from peets.config import Config
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
        self._load_record()
        self._load_config()
        self._init_plugin()

    def _load_record(self):
        record_path = self.path.joinpath(".record.pickle")
        self.record_list = []
        if record_path.exists():
            with record_path.open() as f:
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
        with record_path.open("w") as f:
            pickle.dump(self.record_list, f)

    def record(self, source: Path, op: Op, dest: Path):
        self.record_list.append(
            Record(source.absolute(), op, dest.relative_to(self.path), datetime.now())
        )
        self._save_record()
