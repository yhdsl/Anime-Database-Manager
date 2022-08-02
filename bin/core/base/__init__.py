import os

from . import conf
from . import config


__all__ = [
    "conf",
    "config",
    "plugins",
    "translation",
    "mkdir",
    "setup"
]


def mkdir():
    """
    创建 Folder配置 内的所有文件夹
    """
    for folder in conf.Folder:
        os.makedirs(folder, exist_ok=True)
    return


def _setup_conf():
    """
    初始化 conf

    初始化进程::
        1. 载入配置类的序列化缓存
    """
    # 载入配置类的序列化缓存
    conf.load()
    return


def _setup_config():
    """
    初始化 config

    初始化进程::
        1. 根据 DBToINIAddress 内的数据库创建和修复 INI文件
        #. 初始化 INIConnect 配置供全局调用
    """
    sort_tup = ('Global', 'Logging', 'Plugins')
    for name in conf.DBToINIAddress.get_data().keys():
        sql_address = str(getattr(conf.DBToINIAddress, name))
        try:
            config.create(sql_address, sort_tup=sort_tup)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"未能找到 '{sql_address}'，请尝试重新安装") from e
        config_open = config.fix(sql_address)[0]
        conf.INIConnect.new(name, config_open)
    return


def _setup_log():
    """
    初始化 logging

    初始化进程::
        1. 读取配置文件中的 number 和 level
        #. 委托 logging 模块的 setup 函数初始化
    """
    import logging
    from . import logging as log

    log_number = conf.INIConnect['ADM'].getint('Logging', 'number', fallback=0)
    log_level = conf.INIConnect['ADM'].getint('Logging', 'level', fallback=logging.INFO).upper()
    log.setup(number=log_number, level=log_level)
    return


def setup():
    """
    初始化进程
    """
    mkdir()
    _setup_conf()
    _setup_config()
    _setup_log()
    return
