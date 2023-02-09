import pickle
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from peets.naming import Op


@dataclass
class Record:
    source: Path
    op: Op
    dest: Path
    date: datetime


class Config:
    def __init__(self):
        pass

    def merge(self, new: Config|Path):
        pass


class Library:
    def __init__(self, path: Path):
        self.path = path
        self._load_record()
        self._load_config()

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

    def _save_record(self):
        with record_path.open("w") as f:
            pickle.dump(self.recode_list, f)


    def record(self, source: Path, op: Op, dest: Path):
        self.record_list.append(
            Record(source.absolute(), op, dest.relative_to(self.path), datetime.now())
        )
        self._save_record()
