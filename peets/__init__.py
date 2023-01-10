from peets._plugin import Plugin
from peets.config import Config

_config = Config()
manager = Plugin(_config)


def get_config() -> Config:
    return _config


__all__ = ("get_config", "manager")
