# 配置模块 (底层层)

import io
import os
import re
import sqlite3
import functools

from configparser import (
    Error as _Error,
    ConfigParser as _ConfigParser,
    NoSectionError,
    NoOptionError,
    DuplicateSectionError
)

from . import conf as _conf


__all__ = ['COMMENT_NAME',
           "COMMENT_SYMBOL",
           'create',
           'fix',
           'get_ini_address_list',
           'NoOptionError',
           'NoSectionError',
           'NoCommentError',
           'NoSectionCommentError',
           'DuplicateSectionError',
           'ConfigParser']


COMMENT_NAME = '__table_comment'  #: INI文件中储存 `节注释` 内容的选项的名称
COMMENT_SYMBOL = '; '  #: INI注释的标记符号


def create(sql_address_list: str | list, new_file=False, sort_tup=()):
    """
    从指定的 SQL数据库 中自动生成可修改的 INI文件。

    设计用于 INI文件 的初始化进程。

    默认如果 INI文件 存在，则不再重复创建，除非指定了 new_file
    参数，注意这将导致 INI文件 中所有已修改的内容被重置。

    出于稳定性考虑，不依赖修改后的 :class:`core.base.config.ConfigParser` 类

    :param sql_address_list:
        SQL数据库的地址

    :param new_file:
        如果为 True ，则将彻底重置 INI文件，注意这会丢失原有的所有配置内容

    :param sort_tup:
        用于排序 INI文件 中 节 的顺序的元组

    :type sql_address_list: str | list
    :type new_file: bool
    :type sort_tup: tuple
    """
    if isinstance(sql_address_list, str):
        sql_address_list = [sql_address_list]

    for sql_address in sql_address_list:  # 获取SQL和INI文件的绝对地址
        sql_full_address = sql_address
        ini_full_address = get_ini_address_list(sql_address_list)[0]

        if new_file:  # 强制重新创建
            _create(sql_full_address, ini_full_address, sort_tup)
        else:
            if not os.path.isfile(ini_full_address):  # 跳过已存在的 ini文件，默认处理行为
                _create(sql_full_address, ini_full_address, sort_tup)
    return


def _sort_table(table_name: str, sort_tup: tuple) -> int:
    """
    :return:
        用于排序表名的整数
    """
    try:
        index = sort_tup.index(table_name)
    except ValueError:
        index = len(sort_tup) + 1
    return index


# noinspection SqlResolve
def _create(sql_full_address: str, ini_full_address: str, sort_tup: tuple):
    """创建 INI文件 ，覆写之前存在的内容"""
    with open(ini_full_address, encoding='utf8', mode='w+') as ini_file_open:
        ini_file_write_list = []
        sql_file_cursor = sqlite3.connect(sql_full_address).cursor()
        sql_file_cursor.execute("SELECT tbl_name FROM sqlite_master WHERE type = 'table'")
        sql_table_list = [table_name[0] for table_name in sql_file_cursor.fetchall()]  # 有效表名
        sql_table_list.sort(key=functools.partial(_sort_table, sort_tup=sort_tup))

        for table_name in sql_table_list:
            sql_file_cursor.execute(f"SELECT name FROM {table_name}")
            sql_name_list = [name[0] for name in sql_file_cursor.fetchall()]

            if COMMENT_NAME in sql_name_list:  # 添加节的注释
                sql_file_cursor.execute(f"SELECT comment FROM {table_name} WHERE name = ?",
                                        (COMMENT_NAME,))
                sql_table_comment = sql_file_cursor.fetchone()[0]
                ini_file_write_list.append(COMMENT_SYMBOL + sql_table_comment)
                sql_name_list.remove(COMMENT_NAME)

            ini_file_write_list.append(f"[{table_name}]")  # 添加节

            for name in sql_name_list:
                sql_file_cursor.execute(f"SELECT comment FROM {table_name} WHERE name = ?", (name,))
                name_comment = sql_file_cursor.fetchone()[0]
                if name_comment:  # 添加注释
                    ini_file_write_list.append(COMMENT_SYMBOL + name_comment)

                sql_file_cursor.execute(f"SELECT value FROM {table_name} WHERE name = ?", (name,))
                name_value = sql_file_cursor.fetchone()[0]
                ini_file_write_list.append(f"{name} = {name_value}")  # 添加选项和值

            ini_file_write_list.append('')  # 添加换行

        sql_file_cursor.close()
        ini_file_write_list = [line + '\n' for line in ini_file_write_list]
        ini_file_open.writelines(ini_file_write_list[:-1])
    return


def get_ini_address_list(sql_address_list: str | list) -> list[str]:
    """
    返回对应 SQL文件 对应的 INI文件 的绝对地址。

    :param sql_address_list: SQL文件的地址

    :type sql_address_list: str | list

    :return: 对应INI文件的绝对地址
    :rtype: list[str]
    """
    if isinstance(sql_address_list, str):
        sql_address_list = [sql_address_list]

    ini_address_list = []
    for sql_address in sql_address_list:
        ini_address = os.path.join(_conf.Folder.CONFIG,
                                   f"{os.path.basename(sql_address).rsplit('.', maxsplit=1)[0]}.ini")
        ini_address_list.append(ini_address)
    return ini_address_list


class NoCommentError(_Error):
    """当未找到选项对应的注释时引发的异常。"""

    def __init__(self, option, section):
        _Error.__init__(self, "Option %r in section: %r does not have comment" % (option, section))
        self.option = option
        self.section = section
        self.args = (option, section)


class NoSectionCommentError(_Error):
    """当未找到节对应的注释时引发的异常。"""

    def __init__(self, section):
        _Error.__init__(self, "Section: %r does not have comment" % section)
        self.section = section
        self.args = (section,)


class ConfigParser(_ConfigParser):
    """
    在 ConfigParser类 的基础上添加对注释的支持，其中处理的注释默认仅由 ``;`` 开头，
    此外关闭了 ConfigParser类 的多行支持和允许空值，并且修改保证大小写敏感。

    添加了用于管理注释的方法，并且修改了原有方法以支持注释管理。

    所有的参数与原类相同。

    以下为注释功能的说明。

    在 INI文件中 设定注释内容分为节注释和选项注释，所有的注释内容均在其上一行展示，例如

    ::

        ; section_comment，节注释
        [section]
        ; comment，选项注释
        option = value

    并且暂时要求注释内容仅为单行，不能包含换行符，注释与内容之间不能有空行。

    此外与内置的 ConfigParser类 兼容
    """

    def __init__(self, *args, **kwargs):
        super().__init__(allow_no_value=True,
                         empty_lines_in_values=False,
                         *args,
                         **kwargs)
        self._comment_ConfigParser = _ConfigParser(allow_no_value=True,
                                                   empty_lines_in_values=False)
        return

    def add_section(self, section: str, comment=''):
        """
        **原有方法**

        在原方法的基础上增加了 comment 形参，用于添加section的注释，
        默认为空，即不添加注释，这与原方法保持一致

        :param section:
            与原方法保持一致

        :param comment:
            section的注释内容，不包括注释符号以及末尾的换行符
        """
        section = str(section)
        super().add_section(section=section)
        if comment:
            self._comment_ConfigParser.add_section(section)
            self._comment_ConfigParser[section][COMMENT_NAME] = comment
        return

    def has_section_comment(self, section: str) -> bool:
        """
        **新增方法**

        指明相应名称的section是否存在注释，
        注意这不会区分section是否有效

        :rtype: bool
        """
        return self._comment_ConfigParser.has_option(str(section), COMMENT_NAME)

    def options_with_comment(self, section: str) -> list:
        """
        **新增方法**

        返回指定section中拥有注释内容的选项的列表

        :rtype: list
        """
        section = str(section)
        options_with_comment_list = self._comment_ConfigParser.options(section)
        if COMMENT_NAME in options_with_comment_list:
            options_with_comment_list.remove(COMMENT_NAME)
        return options_with_comment_list

    def has_comment(self, section: str, option: str) -> bool:
        """
        **新增方法**

        section中指明相应名称的选项是否存在注释

        :rtype: bool
        """
        return self._comment_ConfigParser.has_option(str(section), str(option))

    def read(self, filenames, encoding=None) -> list[str]:
        if isinstance(filenames, (str, bytes, os.PathLike)):
            filenames = [filenames]
        # noinspection PyUnresolvedReferences
        encoding = io.text_encoding(encoding)  # Python 3.10 版本引入
        read_ok = []
        for filename in filenames:
            try:
                with open(filename, encoding=encoding) as fp:
                    self._read(self._read_comment(fp), filename)
            except OSError:
                continue
            if isinstance(filename, os.PathLike):
                filename = os.fspath(filename)
            read_ok.append(filename)
        return read_ok

    def read_file(self, f, source=None):
        if source is None:
            try:
                # noinspection PyUnresolvedReferences
                source = f.name
            except AttributeError:
                source = '<???>'
        self._read(self._read_comment(f), source)
        return

    def read_dict(self, dictionary, source='<dict>'):
        """
        .. warning::
            该方法无法使用该子类新提供的注释管理功能
        """
        super().read_dict(dictionary=dictionary, source=source)
        return

    def get_section_comment(self, section: str) -> str:
        """
        **新增方法**

        获取指定名称的section的注释，
        section不存在或section无注释时抛出NoSectionCommentError异常，
        注意抛出异常时不会区分section是否有效

        :rtype: str

        :raise NoSectionCommentError:
            section不存在或section无注释时抛出
        """
        section = str(section)
        try:
            section_comment = self._comment_ConfigParser.get(section, COMMENT_NAME)
        except NoSectionError as e:
            raise NoSectionCommentError(section) from e
        except NoOptionError as e:
            raise NoSectionCommentError(section) from e
        else:
            return section_comment

    def get_comment(self, section: str, option: str):
        """
        **新增方法**

        获取section中指定名称的选项的注释，
        在section不存在时抛出NoSectionError。
        在选项或对应的注释不存在时抛出NoCommentError

        :rtype: str

        :raise NoSectionError:
            在section不存在时抛出
        :raise NoCommentError:
            在选项或对应的注释不存在时抛出
        """
        try:
            comment = self._comment_ConfigParser.get(str(section), str(option))
        except NoOptionError as e:
            raise NoCommentError(str(option), str(section)) from e
        else:
            return comment

    def set(self, section: str, option: str, value=None, comment=''):
        """
        **原有方法**

        在原方法的基础上增加了comment形参，用于指定选项的注释内容
        """
        super().set(str(section), str(option), str(value))
        if comment != '':
            self.set_comment(str(section), str(option), str(comment))
        return

    def set_section_comment(self, section: str, comment: str):
        """
        **新增方法**

        设定指定名称的section的注释为给定值，
        若设定注释值为空，这将删除该注释
        """
        section = str(section)
        comment = str(comment)
        if not comment:
            self._comment_ConfigParser.remove_section(section)
        else:
            if not self._comment_ConfigParser.has_section(section):
                self._comment_ConfigParser.add_section(section)
            self._comment_ConfigParser.set(section, COMMENT_NAME, comment)
        return

    def set_comment(self, section: str, option: str, comment: str):
        """
        **新增方法**

        设定section中指定名称的选项的注释为给定值，
        若设定注释值为空，这将删除该注释，
        若section不存在时，抛出NoSectionError异常，
        若选项不存在时，抛出NoOptionError异常，

        :raise NoSectionError:
            section不存在时抛出
        :raise NoOptionError:
            选项不存在时抛出
        """
        if not comment:
            self._comment_ConfigParser.remove_option(section, option)
        else:
            if not self.has_section(section):
                raise NoSectionError(section)
            if not self.has_option(section, option):
                raise NoOptionError(option, section)
            self._comment_ConfigParser.set(section, option, comment)
        return

    def write(self, fp, space_around_delimiters=True):
        fp_without_comment = io.StringIO()
        super().write(fp=fp_without_comment, space_around_delimiters=space_around_delimiters)

        section_name = ''
        for line in fp_without_comment.getvalue().split('\n')[:-2]:
            line += '\n'
            mo = self.SECTCRE.match(line)
            if mo:
                section_name = mo.group('header')
                try:
                    section_comment = self._comment_ConfigParser[section_name][COMMENT_NAME]
                except KeyError:
                    section_comment = ''
                if section_comment:
                    fp.write(f"{COMMENT_SYMBOL}{section_comment}\n")

            if '=' in line:
                option = line.split('=', maxsplit=1)[0]
                if option[-1] == ' ':
                    option = option[:-1]
                try:
                    comment = self._comment_ConfigParser[section_name][option]
                except KeyError:
                    comment = ''
                if comment:
                    fp.write(f"{COMMENT_SYMBOL}{comment}\n")

            fp.write(line)
        return

    def remove_option(self, section: str, option: str) -> bool:
        self.remove_comment(section, option)
        return super().remove_option(section, option)

    def remove_comment(self, section: str, option: str) -> bool:
        """
        **新增方法**

        移除section中指定名称的选项的注释，
        若移除的选项存在则返回True；在其他情况下将返回False，
        当section不存在时，抛出NoSectionError异常

        :rtype: bool

        :raise NoSectionError:
            section不存在时抛出
        """
        return self._comment_ConfigParser.remove_option(str(section), str(option))

    def remove_section(self, section: str) -> bool:
        self._comment_ConfigParser.remove_section(section)
        return super().remove_section(section)

    def remove_section_comment(self, section: str) -> bool:
        """
        **新增方法**

        移除指定名称的section的注释，
        若移除的选项存在则返回True；在其他情况下将返回False

        :rtype: bool
        """
        try:
            return self._comment_ConfigParser.remove_option(str(section), COMMENT_NAME)
        except NoSectionError:
            return False

    def optionxform(self, optionstr: str) -> str:
        """
        **原有方法**

        修改选项名称为大小写敏感
        """
        return optionstr

    @staticmethod
    def _is_comment(line: str) -> tuple[bool, str]:
        """
        识别输入的内容是否为注释内容，
        注意返回的为一个元组

        :param line:
            文件中的单行内容

        :return:
            元组的第一个部分为判断使用的bool，第二个部分为移除了注释符号和换行符的正文内容
        :rtype: tuple[bool, str]
        """
        if re.match(f'{COMMENT_SYMBOL}.*', line):
            comment_line = line.removeprefix(COMMENT_SYMBOL)
            if comment_line[-1] == '\n':
                comment_line = comment_line[:-1]
            return True, comment_line
        else:
            return False, ''

    def _read_comment(self, fp) -> list[str]:
        """
        从输入的可迭代对象中读取对应的注释内容，并返回移除了注释部分的列表。

        新的注释会覆盖旧的注释，以便读取多个文件。

        :rtype: list[str]
        """
        last_line = ''
        section_name = ''
        new_fp_list = []
        for line in list(fp):
            line = str(line)
            mo = self.SECTCRE.match(line)
            if mo:
                section_name = mo.group('header')
                try:
                    self._comment_ConfigParser.add_section(section_name)
                except DuplicateSectionError:
                    pass
                is_comment_tup = self._is_comment(line=last_line)
                if is_comment_tup[0]:
                    self._comment_ConfigParser[section_name][COMMENT_NAME] = is_comment_tup[1]

            if '=' in line:
                option = line.split('=', maxsplit=1)[0]
                if option[-1] == ' ':
                    option = option[:-1]
                is_comment_tup = self._is_comment(line=last_line)
                if is_comment_tup[0]:
                    self._comment_ConfigParser[section_name][option] = is_comment_tup[1]

            if not self._is_comment(line=line)[0]:
                new_fp_list.append(line)

            last_line = line
        return new_fp_list


def fix(sql_address_list: str | list) -> list[ConfigParser]:
    """
    用于修复损坏的 INI文件，并返回包含读取后的 ConfigParser类实例的列表

    原有的所有配置均会被保留，仅添加缺失的选项内容

    :param sql_address_list:
        SQL数据库的地址，可以为字符串或者列表合集

    :type sql_address_list: str | list

    :return:
        包含INI文件的ConfigParser类实例的列表
    :rtype: list[ConfigParser]
    """
    if isinstance(sql_address_list, str):
        sql_address_list = [sql_address_list]

    configparser_list = []
    for sql_address in sql_address_list:  # 获取SQL和INI文件的绝对地址
        sql_full_address = sql_address
        ini_full_address = get_ini_address_list(sql_address_list)[0]

        with open(ini_full_address, encoding='utf8') as old_file_open:
            old_file_list = old_file_open.readlines()  # 旧 INI文件
        create(sql_full_address, new_file=True)
        with open(ini_full_address, encoding='utf8') as new_file_open:
            new_file_list = new_file_open.readlines()  # 新 INI文件

        configparser = ConfigParser()
        configparser.read_file(new_file_list)
        configparser.read_file(old_file_list)  # 旧内容覆盖新内容
        configparser.write(open(ini_full_address, encoding='utf8', mode='w'))
        configparser_list.append(configparser)
    return configparser_list
