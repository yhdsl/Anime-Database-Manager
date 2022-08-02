# 全局变量 (底层层)

import os
import re
import json
import pickle
import random
import shutil
import hashlib
import pathlib
import sqlite3
import platform
import threading
import configparser

from enum import Enum

from typing import (
    Any as _Any,
    Iterator as _Iterator,
    Union as _Union
)


__all__ = [
    "get_version_dict",
    "extend",
    "PluginsTypeError",
    "NeedHookError",
    "Singleton",
    "Conf",
    "Enum",
    "Project",
    "Version",
    "BuiltinPlugins",
    "Path",
    "Dump",
    "RunInfo",
    "Folder",
    "DBToINIAddress",
    "INIConnect",
    "DBConnect",
    "LogName",
    "dump",
    "load"
]


# ---------- 通用工具部分 ----------
# 全局公开的，可复用的函数


def get_version_dict(version: str) -> dict[str, str | None]:
    """
    用于拆分版本号

    其中版本号格式为 `major.minor.micro-release_name.release_level+ex` ，
    其中后三个内容可以省略，匹配时忽略大小写

    :param version:
        版本号，其格式请参考语义化标准与正则语句

    :type version: str

    :return:
        包含匹配内容的字典，键与版本号格式名称一致，缺省为 None，注意获取的值均为 str 格式
    :rtype: dict[str, str | None]

    :raise ValueError:
        当版本号不符合格式时抛出
    """
    match = re.fullmatch(r'(?P<major>\d+)\.(?P<minor>\d+)\.(?P<micro>\d+)'  # 0.1.0
                         r'('
                         r'((-(?P<release_name>test|alpha|beta|rc|release))'  # -test
                         r'(\.(?P<release_level>\d+))?'  # .0
                         r')?'
                         r'(\+(?P<ex>\w+))?'  # +ex
                         r')?',
                         str(version),
                         flags=re.I)
    if match is None:
        raise ValueError(f"'{version}' 不符合版本号格式")
    return match.groupdict()


def extend(var: list | set | dict, value, *, key=None):
    """
    由于列表，集合等没有一个统一名称的拓展接口，该函数对其进行了统一的封装

    目前支持列表，集合，字典

    :param var:
        待拓展的变量

    :param value:
        待拓展的值
        当拓展字典时，该参数为值，为了避免与键发生顺序错误，建议以关键字传入

    :param key:
        目前仅在拓展字典时使用，为待拓展的键，仅限关键字

    :raise TypeError:
        传入当前不支持拓展的变量时抛出
    """
    if isinstance(var, list):
        var.append(value)
    elif isinstance(var, set):
        var.add(value)
    elif isinstance(var, dict):
        var[key] = value
    else:
        raise TypeError(f"{type(var)} 为不支持的拓展类型")
    return


# ---------- 异常部分 ----------
# 便于全局调用的异常定义


class PluginsTypeError(TypeError):
    """
    当 new 函数不支持当前传入的调用类型时抛出，类似于 TypeError

    这将使 new 函数不会从缓存中被移除
    """
    pass


class NeedHookError(NotImplementedError):
    """
    当类中的方法未被插件钩住时抛出

    仅用于 hook 函数的 r 模式

    通常在内置模块未被正确加载时抛出
    """
    pass


# ---------- 数据类部分 ----------
# 用于储存可变的数据，提供类型检测


class Singleton:
    """
    线程安全的单例类
    """
    _singleton = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if cls._singleton is None:
                cls._singleton = super().__new__(cls)
        return cls._singleton


class Data:
    """
    线程安全的描述器
    """

    def __init__(self, key: str, data, instance, *, readonly=False):
        """
        初始化描述器时需要指定名称和数据，并确定是否可读

        :param key:
            描述器名称
        :param data:
            描述器数据
        :param instance:
            调用的实例
        :param readonly:
            可读状态

        :type key: str
        :type readonly: bool
        """
        self._key = str(key)
        self._data = data

        self._readonly = False
        self.__set__(instance, data)  # 初始化时写入数据

        self._readonly = readonly
        return

    def __get__(self, instance, owner=None) -> _Any:
        with instance.get_lock():
            try:
                data = instance.get(self._key)  # 读取被委托至调用者的 get 方法
            except (AttributeError, KeyError) as e:
                raise AttributeError(f"'{instance.__class__.__name__}' "
                                     f"object has no attribute '{self._key}'") from e
        return data

    @staticmethod
    def check(values, types) -> bool:
        """
        检查 values 是否是 types 类型

        :rtype: bool
        """
        return isinstance(values, types)

    def __set__(self, instance, value):
        if self._key in instance.get_disabled_tup():  # 内置名称冲突检查
            raise AttributeError(f"{self._key} 被用于内置方法，其不应当被修改")

        if self._readonly:  # 只读检查
            raise AttributeError(f"{self._key} 被设置为只读，不可被修改")

        types = instance.get_types()  # 类型检测
        if types is not None:
            if not self.check(value, types):
                raise TypeError(f"预期获得 {types} 类型的实例，但是获得了 {type(value)}")

        with instance.get_lock():
            instance.get_data()[self._key] = value
        return

    def __delete__(self, instance):
        pass

    def state(self, *, readonly: bool):
        """
        修改描述器可读状态为 read_state 指定的布尔值

        :param readonly:
            新指定的可读状态

        :type readonly: bool
        """
        self._readonly = bool(readonly)
        return


class Conf(Singleton):
    """
    配置类，用于绑定一系列有着相同目的的配置值

    一般子类化该类而非使用其实例，具体用法与枚举类相似，
    但是特别的是，目前不支持枚举中类似 Conf.ONE 的用法，
    折中的措施可以参考本模块，该情况在未来可能会被更改

    与枚举类不同的是，按属性访问会直接返回值，无需使用 value 方法，
    对子类进行迭代时，返回的是包含所有值的生成器

    在创建子类时提供的类属性会被自动设置为只读，目的是保证默认配置不受篡改，
    但只读属性可以被修改，这无法被强制保证

    类属性建议与枚举一致，使用全大写，其中以下划线开头的属性不会对其进行任何特殊的处理

    默认会开启类型检测，防止类型不一致，但是如果子类未提供初始类属性，
    或者初始类属性包含多个类型，则类型检测将被关闭
    """
    _init_type = False  # 防止重复创建实例时执行多个初始化代码

    def __init__(self):
        if not self._init_type:
            self._disabled_tup = ('get', 'get_data', 'get_lock',
                                  'get_types', 'set_types', 'get_disabled_tup',
                                  'new', 'state', 'dump', 'load')  # 内置函数名称，不可作为配置名称

            self._data: dict[str, _Any] = {}
            self._data_lock = threading.Lock()
            self._types = None

            # 类属性被设置为只读
            self._class_dict = vars(self.__class__)
            self._class_attrs = filter(lambda value: (value[0] != '_') and (value not in self._disabled_tup),
                                       self._class_dict)
            self._types_set = set()
            for attr in self._class_attrs:
                data = self._class_dict[attr]
                self._types_set.add(type(data))
                data = Data(key=attr, data=data, instance=self, readonly=True)
                setattr(self.__class__, attr, data)
            if len(self._types_set) == 1:  # 如果初始包括多个类型，则不进行类型检测
                self._types = list(self._types_set)[0]
            del self._class_dict
            del self._class_attrs
            del self._types_set

            self._init_type = True

        return

    def get(self, key: str) -> _Any:
        """
        用于改变配置的读取行为

        默认会返回储存在配置字典内 key 对应的值，
        重载该方法允许在返回配置的内容前对其进行处理

        值得注意的是，写入配置的仍然是处理前的数据，这将导致 getattr
        和 setattr 处理的数据不一致

        如果未找到配置，预期抛出 AttributeError 或 KeyError

        :param key:
            配置名称

        :type key: str

        :return:
            配置处理后的值

        :raises AttributeError, KeyError:
            未找到配置
        """
        return self._data[str(key)]

    def get_data(self) -> dict[str, _Any]:
        """
        返回包含属性与数值的字典

        不建议直接修改此字典，请通过描述器进行修改
        """
        return self._data

    def get_lock(self) -> threading.Lock:
        """
        返回配置类对应的锁
        """
        return self._data_lock

    def get_types(self) -> _Any:
        """
        返回配置允许的类型
        """
        return self._types

    def set_types(self, types):
        """
        设置配置允许的类型

        默认为实例检测
        """
        self._types = types
        return

    def get_disabled_tup(self) -> tuple:
        """
        返回不允许配置命名的名称元组
        """
        return self._disabled_tup

    def new(self, name: str, value, *, readonly=False):
        """
        添加新的配置

        :param name:
            配置名称
        :param value:
            配置值
        :param readonly:
            可读状态，默认可读

        :type name: str
        :type readonly: bool
        """
        name = str(name)
        if name in self._data:  # 如果配置存在，则委托至描述器，并更新只读状态
            data = vars(self.__class__)[name]
            data.__set__(self, value)
            self.state(name, readonly=readonly)
        else:
            data = Data(key=name, data=value, instance=self, readonly=bool(readonly))
            setattr(self.__class__, name, data)
        return

    def __setattr__(self, key: str, value):
        if key[0] == "_":  # 除私有属性外，均委托至 new 方法
            super().__setattr__(key, value)
        else:
            self.new(name=str(key), value=value)
        return

    def __delattr__(self, item):
        if item[0] != "_":
            try:
                del self._data[item]
            except KeyError as e:
                raise AttributeError(item) from e
        super().__delattr__(item)

        try:  # 尝试删除类属性
            delattr(self.__class__, item)
        except AttributeError:
            pass

        return

    def state(self, name: str, *, readonly: bool):
        """
        修改指定配置的可读状态

        :param name:
            配置名称

        :param readonly:
            只读状态、

        :type name: str
        :type readonly: bool
        """
        date = vars(self.__class__)[name]
        state = getattr(date, 'state')
        state(readonly=bool(readonly))
        return

    # ---------- 容器支持 ----------

    def __bool__(self) -> bool:
        """
        如果配置数目为空，则返回 False，反之返回 True
        """
        return bool(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, item: int | str) -> _Any:
        if isinstance(item, int):
            try:
                name = list(self._data.keys())[item]
            except IndexError as e:
                raise KeyError from e
            return getattr(self, name)
        elif isinstance(item, str):
            try:
                return getattr(self, item)
            except AttributeError as e:
                raise KeyError from e
        else:
            raise TypeError(f"{type(item)} 为不支持的类型")

    def __setitem__(self, key, value):
        setattr(self, key, value)
        return

    def __delitem__(self, key):
        delattr(self, key)
        return

    def __iter__(self) -> _Iterator:
        return map(self.get, self._data.keys())

    # ---------- 序列化支持 ----------

    def dump(self, file):
        """
        序列化到指定的 file 文件中

        :param file:
            以二进制可写模式打开的文件
        """
        dump_tup = (self._data, self._types)
        pickle.dump(dump_tup, file)
        return

    def load(self, file):
        """
        从 file 文件中恢复配置与类型检测配置，
        并且删除未被缓存的配置

        :param file:
            以二进制模式打开的文件
        """
        load_tup: tuple[dict[str, _Any], _Any] = pickle.load(file)

        self._types = None  # 防止写入错误，关闭类型检测
        for key in load_tup[0]:
            try:
                if getattr(self, key) != load_tup[0][key]:
                    try:
                        self.new(key, load_tup[0][key])
                    except AttributeError:  # 只读
                        self.state(key, readonly=False)
                        self.new(key, load_tup[0][key])
                        self.state(key, readonly=True)
            except AttributeError:  # 非默认数据
                self.new(key, load_tup[0][key])

        for unknown in (set(self._data) - set(load_tup[0])):
            delattr(self, unknown)

        self._types = load_tup[1]

        return


# ---------- 全局常量部分 ----------
#  使用枚举类储存的不可变的常量


class Project(Enum):
    """
    项目基本信息
    """
    NAME = 'Anime Database Manager'
    SHORT_NAME = 'ADM'
    AUTHOR = 'YHDSL'
    VERSION = '0.1.0-test.0'
    URL = 'https://github.com/yhdsl/Anime-Database-Manager'


_version_dict = get_version_dict(Project.VERSION.value)


class Version(Enum):
    """
    项目版本信息
    """
    VERSION = Project.VERSION.value

    MAJOR = _version_dict['major']
    MINOR = _version_dict['minor']
    MICRO = _version_dict['micro']
    RELEASE_NAME = _version_dict['release_name']
    RELEASE_LEVEL = _version_dict['release_level']
    EX = _version_dict['ex']


del _version_dict


class BuiltinPlugins(Enum):
    """
    内置插件名称

    已排除隐藏的插件
    """
    pass


class Path(Enum):
    """
    用于路径类型检测的定义

    与官方定义一致
    """
    StrPath = _Union[str, os.PathLike[str]]
    BytesPath = _Union[bytes, os.PathLike[bytes]]
    StrOrBytesPath = _Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]


# ---------- 全局变量部分 ----------
#  使用 Conf 类储存的可变的配置内容


class _Dump(Conf):
    """
    储存需要序列化的配置类

    默认配置应当只有 Dump 一个
    """
    Dump = None

    def dump(self, file):
        dump_data = {key: value.__class__ for key, value in self._data.items()}  # 储存数据对应的类
        dump_tup = (dump_data, self._types)
        pickle.dump(dump_tup, file)
        return

    def load(self, file):
        load_tup: tuple[dict[str, _Any], _Any] = pickle.load(file)

        data_remove = list(self._data)  # 清理 Dump 类
        for data in data_remove:
            delattr(self, data)

        self.set_types(None)
        for key in load_tup[0]:
            setattr(self, key, load_tup[0][key]())

        self.new('Dump', self, readonly=True)

        self._types = load_tup[1]

        return


Dump = _Dump()
Dump.set_types(Conf)
Dump.state('Dump', readonly=False)
Dump.new('Dump', Dump)
Dump.state('Dump', readonly=True)


class _RunInfo(Conf):
    """
    软件运行时所需的信息

    除非特殊情况，请勿修改该类的内容
    """
    BIN = str(pathlib.Path(__file__).absolute().parent.parent.parent.name)  # bin
    CORE = str(pathlib.Path(__file__).absolute().parent.parent.name)  # core

    ADDRESS = str(pathlib.Path(__file__).absolute().parent.parent.parent)  # bin 文件夹地址

    SYSTEM = platform.system()


RunInfo = _RunInfo()
Dump.new('RunInfo', RunInfo)


class _Folder(Conf):
    """
    运行所需文件夹的位置

    储存内容为用元组表示的地址，
    返回的内容会带上 `RunInfo.ADDRESS` 前缀，
    如果元组内已有绝对地址，则覆盖默认设置

    该配置类下的所有文件夹均会在运行前被创建
    """
    ASSETS = ('core', 'assets')
    LOGS = ('logs',)
    PLUGINS = ('plugins',)
    PROFILES = ('profiles',)
    BACKUP = ('profiles', 'backup')
    CACHE = ('profiles', 'cache')
    CONFIG = ('profiles', 'config')
    DATABASE = ('profiles', 'database')
    TEMP = ('profiles', 'temp')
    TEMPLATES = ('profiles', 'templates')

    def get(self, key: str) -> str:
        return os.path.join(RunInfo.ADDRESS, *self.get_data()[str(key)])


Folder = _Folder()
Dump.new('Folder', Folder)


class _DBToINIAddress(Conf):
    """
    INI文件对应的DB数据库地址

    储存格式要求与 Folder 配置相同

    该配置类下的所有数据库均会生成对应的INI文件
    """
    ADM = ('core', 'assets', 'ADM.db')

    def get(self, key: str) -> str:
        return os.path.join(RunInfo.ADDRESS, *self.get_data()[str(key)])


DBToINIAddress = _DBToINIAddress()
Dump.new('DBToINIAddress', DBToINIAddress)


class _INIConnect(Conf):
    """
    储存全局可用的INI文件读取对象

    类型检测为 ConfigParser 类，其为 configparser模块 的父类
    """
    pass


INIConnect = _INIConnect()
INIConnect.set_types(configparser.ConfigParser)
Dump.new('INIConnect', INIConnect)


class _DBConnect(Conf):
    """
    储存全局可用的Database文件读取对象

    类型检测为 Connection 类
    """
    pass


DBConnect = _DBConnect()
DBConnect.set_types(sqlite3.Connection)
Dump.new('DBConnect', DBConnect)


class _LogName(Conf):
    """
    储存额外的日志文件名称

    仅储存于项目默认 log文件夹 下的日志名称需要记录，
    位于其他地点的不由 core 进行管理

    类型检测为 str
    """
    pass


LogName = _LogName()
LogName.set_types(str)
Dump.new('LogName', LogName)


# ---------- 序列化部分 ----------
#  缓存配置类的更改


def _json_load(conf_cache_folder: pathlib.Path) -> dict[str, dict[str, str]]:
    """
    读取 json 文件，
    读取失败时缓存失效

    :param conf_cache_folder:
        配置类对应的 cache 文件夹的 Path类实例

    :type conf_cache_folder: pathlib.Path

    :return:
        包含配置类缓存信息的字典，以Dump配置的属性名称为键，
        值为包含了文件名 (filename) 和哈希值 (hash_check) 的字典
    :rtype: dict[str, dict[str, str]]
    """
    try:
        with open(conf_cache_folder / 'info.json', encoding='utf8') as fp:
            dump_info = json.load(fp)
    except FileNotFoundError:
        try:  # 缓存失效，重建整个目录
            shutil.rmtree(conf_cache_folder)
        except FileNotFoundError:
            pass
        conf_cache_folder.mkdir()

        dump_info = {}

    return dump_info


def dump():
    """
    缓存配置类

    需要缓存的配置类定义在 Dump 中，
    缓存的内容位于 cache 文件夹下的 conf 文件夹中，
    由 info.json 文件记录，包括文件名和 hash值
    """
    conf_cache_folder = pathlib.Path(str(Folder.CACHE)) / 'conf'

    dump_info = _json_load(conf_cache_folder)

    for name in Dump.get_data():
        try:  # 旧缓存文件名称
            filename_old = dump_info[name]['filename']
        except KeyError:
            filename_old = None

        filename_new = f"{name}_{random.getrandbits(50)}.pkl"  # 新缓存文件名称，确保唯一
        while filename_old == filename_new:
            filename_new = f"{name}_{random.getrandbits(50)}.pkl"

        with open(conf_cache_folder / filename_new, mode='w+b') as fp:
            try:
                getattr(Dump[name], 'dump')(file=fp)  # 序列化
            except TypeError:
                continue  # 不序列化不支持的内容

        with open(conf_cache_folder / filename_new, mode='r+b') as fp_check:
            h = hashlib.sha256(fp_check.read())
            hash_check = h.hexdigest().upper()

        if filename_old is not None:
            try:
                os.remove(conf_cache_folder / filename_old)
            except FileNotFoundError:
                pass

        info_dict = {'filename': filename_new, 'hash_check': hash_check}
        dump_info[name] = info_dict

    with open(conf_cache_folder / 'info.json', mode='w+', encoding='utf8') as fp_json:
        json.dump(dump_info, fp_json)

    return


def load():
    """
    从缓存中恢复配置值
    """
    conf_cache_folder = pathlib.Path(str(Folder.CACHE)) / 'conf'

    dump_info = _json_load(conf_cache_folder)
    invalid_name_list = []

    for name in dump_info:
        try:
            file = conf_cache_folder / dump_info[name]['filename']
            with open(file, mode='r+b') as fp:
                h = hashlib.sha256(fp.read())
                hash_check = h.hexdigest().upper()
                if hash_check != dump_info[name]['hash_check']:  # hash检测失败
                    invalid_name_list.append(name)
                    continue

                fp.seek(0)
                getattr(Dump[name], 'load')(file=fp)

        except FileNotFoundError:  # 文件不存在
            invalid_name_list.append(name)
            continue

    for invalid_name in invalid_name_list:
        file = conf_cache_folder / dump_info[invalid_name]['filename']
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
        del dump_info[invalid_name]

    with open(conf_cache_folder / 'info.json', mode='w+', encoding='utf8') as fp_json:
        json.dump(dump_info, fp_json)

    return
