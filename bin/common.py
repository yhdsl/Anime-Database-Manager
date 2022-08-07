# 通用模块 (启动层)

import os
import sys
import webbrowser

from tkinter import Tk
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Button, Frame, Label, Style
from tkinter.filedialog import askopenfilename, asksaveasfile
from tkinter.messagebox import showerror, showwarning, askyesno


__all__ = [
    'gui_exc_windows',
    'check_environ',
    'check_venv'
]


_TITLE = 'ADM 异常捕获'  # TODO[短期] (@YHDSL) 添加多语言支持
_BUTTON_NAMES = ('前往 Github', '确定', '导出异常日志')
_INFO = '啊哈，程序因为一个未经处理的异常而罢工了！\n' \
        '这往往是由于开发者未能正确的捕获所有抛出的异常而导致的，但有时也可能是故意为之，' \
        '目的是为了提示当前软件运行所需的配置未能被正常载入。\n' \
        '如果你之前对软件进行了修改，尝试回滚或删除被修改过的文件或许是个解决问题的好主意，' \
        '但最好先提前备份好你的个人配置数据。\n' \
        '如果仍不知晓如何修复或确定这是由于软件本身引发的错误，你可以通过下方的按钮前往软件的Github界寻求相关帮助，' \
        '记得在Issues里附上导出的异常日志文件哦。\n\n' \
        '完整的异常链如下：'
_EXC = 'null'

_URL = 'https://github.com/yhdsl/Anime-Database-Manager'

_ICON_ADDRESS = r'core\assets\icon.ico'  # TODO[中期] (@YHDSL) 优化icon
if not os.path.exists(_ICON_ADDRESS):
    _ICON_ADDRESS = None
else:
    _ICON_ADDRESS = os.path.abspath(_ICON_ADDRESS)

_ERROR_TITLE = 'ADM 错误'

_ISSUES_MESSAGE = f"未能成功打开网页，请尝试手动访问\n{_URL}"
_VERSION_MESSAGE = 'ADM 依赖于 Python 高版本的特定功能才能正常运行\n' \
                   '因此至少需要 3.10.0 版本以上的 Python 环境'
_SYSTEM_MESSAGE = 'ADM 的部分底层功能依赖于 Windows 的 DLL\n' \
                  '因此在其他平台上可能会功能受限'
_BIT_MESSAGE = 'ADM 的部分功能仅在 64 位的平台上进行过测试\n' \
               '其在 32 位的平台上可能将无法正常工作'


def _text_limit(text: str, limit: int | None) -> str:
    """
    根据 limit 的值截断 text，截断后会添加省略号

    :param text:
        给定文本

    :param limit:
        文本限制长度，默认 None 为无限制

    :type text: str
    :type limit: int | None

    :return:
        处理后的 text
    :rtype: str
    """
    text = str(text)
    try:
        if len(text) > limit:
            text = text[:limit] + '...'
    except TypeError:
        pass
    return text


def _button_issues_command(root: Tk):
    """
    点击后访问 GitHub 项目主页

    :param root:
        主窗口
    """
    root.attributes('-topmost', False)

    try:
        webbrowser.open_new_tab(_URL)
    except webbrowser.Error:
        showerror(title=_ERROR_TITLE, message=_ISSUES_MESSAGE)

    return


def _button_save_command(root: Tk, exc: str):
    """
    询问保存的文件地址，并写入日志，未选择则返回至主窗口

    :param root:
        主窗口

    :param exc:
        异常文本
    """
    import time
    fp = asksaveasfile(initialfile=f"ADM_unknown_exc_log-{time.strftime('%Y_%m_%d_%H_%M')}.log",
                       filetypes=[("log 文件", "*.log")])
    if fp is not None:
        fp.write(exc)
        fp.close()
        root.quit()
    return


def gui_exc_windows(info=_INFO, exc=_EXC, title=_TITLE, button_names=_BUTTON_NAMES) -> Tk:
    """
    异常捕获窗口，用于在启动层捕获所有未经处理的异常链

    处于稳定性考虑，当前窗口大小和布局均为固定值，不会随显示器的分辨率进行缩放

    不会直接启动消息循环，而是返回主窗口供其他部分调用

    一般仅需向 exc 传入异常文本

    :param info:
        显示在异常文本上方的说明性文字

    :param exc:
        异常文本

    :param title:
        主窗口标题

    :param button_names:
        包含各按钮名称的元组

    :type info: str
    :type exc: str
    :type title: str
    :type button_names: tuple[str, str, str]

    :return:
        主窗口
    :rtype: Tk
    """
    import functools

    root = Tk()
    root.withdraw()  # 防止设置图标时单独显示

    width = 800
    # height = 600
    padding = 20

    # 通知部件
    style_info = Style()
    style_info.configure('root.TLabel', anchor='e', justify='left',
                         padding=padding, wraplength=(width - padding * 2))

    widget_info = Label(root, text=_text_limit(info, limit=300), style='root.TLabel')  # 文本限制在 300 字以内
    widget_info.grid(column=0, columnspan=2, row=0, sticky='w', pady=padding // 2)

    # 异常部件
    exc = _text_limit(exc, limit=None)
    widget_exc = ScrolledText(root, autoseparators=False, undo=False)
    widget_exc.insert('insert', exc)
    widget_exc.see('end')
    widget_exc.configure(state='disabled', height=20)
    widget_exc.grid(column=0, columnspan=2, row=1)

    # 按钮部件
    widget_button_issues = Button(root,
                                  text=_text_limit(button_names[0], limit=50),
                                  command=functools.partial(_button_issues_command, root=root))  # GitHub
    widget_button_issues.grid(column=0, row=2, padx=padding, pady=padding, sticky='w')

    frm_button = Frame(root)
    frm_button.grid(column=1, row=2, padx=padding, pady=padding, sticky='e')

    widget_button_ok = Button(frm_button,
                              text=_text_limit(button_names[1], limit=50),
                              command=root.quit)  # OK
    widget_button_ok.grid(column=1, row=0)

    widget_button_save = Button(frm_button,
                                text=_text_limit(button_names[2], limit=50),
                                command=functools.partial(_button_save_command, root=root, exc=exc))  # Save
    widget_button_save.grid(column=2, row=0, padx=10)

    # 主窗口设置
    root.title(_text_limit(title, limit=50))

    root.attributes('-topmost', True)

    if _ICON_ADDRESS is not None:
        root.iconbitmap(_ICON_ADDRESS)

    widget_info.update()
    widget_exc.update()
    frm_button.update()
    height = widget_info.winfo_height() + widget_exc.winfo_height() + frm_button.winfo_height() + padding * 3
    height = (height + 1) // 2 * 2
    max_width, max_height = root.maxsize()
    centre_width = (max_width - width) // 2
    centre_height = (max_height - height) // 2

    root.geometry(f"{width}x{height}+{centre_width}+{centre_height}")  # 居中
    root.resizable(False, False)
    root.deiconify()
    return root


def check_environ():
    """
    负责检查当前环境状态，以防止未知的错误

    目前包括如下检查项目::

        1. python 版本大于 3.10.0
        #. 系统平台为 Windows
        #. 对 32 位平台发出警告

    """
    if sys.hexversion < 0x030a00f0:  # 3.10.0
        showerror(title=_ERROR_TITLE, message=_VERSION_MESSAGE)
        sys.exit('需要高版本的 Python')

    import platform

    # TODO[中期] (@YHDSL) 添加多平台支持
    if platform.system() not in ('Windows',):  # Windows
        showwarning(title=_ERROR_TITLE, message=_SYSTEM_MESSAGE)

    if sys.maxsize <= 2 ** 32:  # 64 bit
        showwarning(title=_ERROR_TITLE, message=_BIT_MESSAGE)

    return


def _is_venv() -> bool:
    """
    用于检测当前程序是否运行于 venv 虚拟环境中

    :return:
        用于判断是否运行于 venv 虚拟环境中的布尔值
    :rtype: bool
    """
    if 'VIRTUAL_ENV' in os.environ:
        return True
    else:
        return False


def _venv_activate(address: str):
    """
    将指定的虚拟环境加载到当前的环境中

    代码逻辑参考 activate 批处理脚本

    :param address:
        虚拟环境的绝对地址
    """
    address = os.path.abspath(address)

    os.environ['VIRTUAL_ENV'] = address

    if 'PROMPT' not in os.environ:
        os.environ['PROMPT'] = '$P$G'

    if '_OLD_VIRTUAL_PROMPT' in os.environ:
        os.environ['PROMPT'] = os.environ['_OLD_VIRTUAL_PROMPT']

    if '_OLD_VIRTUAL_PYTHONHOME' in os.environ:
        os.environ['PYTHONHOME'] = os.environ['_OLD_VIRTUAL_PYTHONHOME']

    os.environ['_OLD_VIRTUAL_PROMPT'] = os.environ['PROMPT']

    os.environ['PROMPT'] = f"(venv) {os.environ['PROMPT']}"

    if 'PYTHONHOME' in os.environ:
        os.environ['_OLD_VIRTUAL_PYTHONHOME'] = os.environ['PYTHONHOME']
        del os.environ['PYTHONHOME']

    if '_OLD_VIRTUAL_PATH' in os.environ:
        os.environ['PATH'] = os.environ['_OLD_VIRTUAL_PATH']

    if '_OLD_VIRTUAL_PATH' not in os.environ:
        os.environ['_OLD_VIRTUAL_PATH'] = os.environ['PATH']

    os.environ['PATH'] = fr"{address}\Scripts;{os.environ['PATH']}"

    os.environ['VIRTUAL_ENV_PROMPT'] = '(venv) '

    return


def _venv_create(address: str):
    """
    在指定位置创建一个虚拟环境，自动激活并安装指定的依赖

    :param address:
        虚拟环境的绝对地址
    """
    import shutil
    import subprocess

    address = os.path.abspath(address)

    requirements_address = askopenfilename(title='请选择 requirements 文件',
                                           initialdir=os.path.dirname(address),
                                           filetypes=[('requirements 文件', 'requirements.txt')])

    if requirements_address == '':  # 获取 requirements 文件位置
        if os.path.isdir(address):
            shutil.rmtree(address)
        showerror(title='requirements 文件错误',
                  message='不是正确的 requirements 文件\n'
                          '软件将无法继续正常工作')
        sys.exit('requirements 文件错误')

    venv_state = subprocess.run(['python', '-m', 'venv', address])  # 安装虚拟环境
    if venv_state.returncode != 0:
        if os.path.isdir(address):
            shutil.rmtree(address)
        showerror(title='虚拟环境创建失败',
                  message=f'无法创建虚拟环境，退出状态码为 {venv_state.returncode}\n'
                          f'请尝试手动创建虚拟环境')
        sys.exit('虚拟环境创建失败')

    _venv_activate(address)  # 环境激活
    venv_state = subprocess.run(['pip', 'install', '-r', requirements_address])  # 安装依赖
    if venv_state.returncode != 0:
        if os.path.isdir(address):
            shutil.rmtree(address)
        showerror(title='依赖安装失败',
                  message=f'无法正确安装 requirements 文件指定的依赖，'
                          f'退出状态码为 {venv_state.returncode}\n'
                          f'请尝试手动安装相关依赖')
        sys.exit('依赖安装失败')

    return


def check_venv():  # TODO[长期] (@YHDSL) 允许不使用虚拟环境
    if not _is_venv():  # 创建或激活虚拟环境
        main_address = os.path.abspath('.')
        venv_address = fr"{main_address}/venv"
        if not os.path.isdir(venv_address):
            venv_address = fr"{os.path.dirname(main_address)}/venv"
            if not os.path.isdir(venv_address):
                ask_create = askyesno(title='创建虚拟环境',
                                      message='未检测到虚拟环境，是否创建一个新的 venv 虚拟环境？')
                if ask_create:
                    _venv_create(venv_address)
                else:
                    sys.exit('未能创建虚拟环境')
        _venv_activate(venv_address)
    return


if __name__ == '__main__':
    gui_exc_windows(exc='test').mainloop()
