# 托盘功能模块

import os
import logging

from typing import Callable as _Callable

import win32con
# noinspection PyPackageRequirements
import win32gui
import win32gui_struct

import ADM_Core.CodeBase.Tools as _ADM_Tools


module_name = f'{_ADM_Tools.bin_name}.ADM_PyQt.Tray'


_logger = logging.getLogger(module_name)


class Tray:  # TODO [短期] 添加模块函数支持
    """
    底层的托盘类

    提供了更为详细和全面的托盘自定义内容
    """
    def __init__(self):
        self._icon = None
        self._tip = None

        self._hwnd = None

        self.uCallbackMessage = win32con.WM_USER + 1080

    # ----- 鼠标信号处理 -----

    # noinspection PyUnusedLocal
    def notify(self, hwnd, msg: int, wparam: int, lparam: int):
        """
        窗口信号处理函数，负责处理托盘接收的鼠标信号

        :param hwnd:
            与托盘相关联的通知窗口的句柄
        :param msg:
            自定义的 uCallbackMessage 信号，任何操作均会被发送，
            可通过 uCallbackMessage 实例变量获取或自定义
        :param wparam:
            图标标识符
        :param lparam:
            鼠标或键盘信息
        """
        if lparam == win32con.WM_MOUSEFIRST:  # 悬浮
            self.mouse_over()
        elif lparam == win32con.WM_LBUTTONDOWN:  # 鼠标左键单击
            self.mouse_left_click()
        elif lparam == win32con.WM_MBUTTONDOWN:  # 鼠标中键单击
            self.mouse_middle_click()
        elif lparam == win32con.WM_RBUTTONDOWN:  # 鼠标右键单击
            self.mouse_right_click()
        return

    def mouse_over(self):
        """
        鼠标悬浮操作

        一般不需要指定该操作
        """
        pass

    def mouse_left_click(self):
        """
        鼠标左键按下操作
        """
        pass

    def mouse_middle_click(self):
        """
        鼠标中键按下操作

        一般不需要指定该操作
        """
        pass

    def mouse_right_click(self):  # TODO [短期] 添加菜单支持
        """
        鼠标右键按下操作
        """
        pass

    # ----- 通知窗口 -----

    # noinspection SpellCheckingInspection
    @property
    def _windows_class(self):
        """
        返回一个用于接收信号的类的原子，
        可通过 hwnd 创建为一个窗口
        其消息处理函数为 notify 方法

        **该属性只应该被调用一次**
        """
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.notify  # 指定消息处理函数
        wc.hInstance = win32gui.GetModuleHandle(None)  # 传入当前进程的句柄
        wc.lpszClassName = 'Tray'  # 窗口的类名
        return win32gui.RegisterClass(wc)

    @property
    def hwnd(self):
        """返回一个用于接收信号的窗口"""
        if self._hwnd is None:
            hwnd = win32gui.CreateWindow(self._windows_class,  # 窗口的类
                                         'tray',  # 窗口名称
                                         win32con.WS_OVERLAPPEDWINDOW,  # 窗口样式
                                         win32con.CW_USEDEFAULT,  # 以下为窗口位置
                                         win32con.CW_USEDEFAULT,
                                         win32con.CW_USEDEFAULT,
                                         win32con.CW_USEDEFAULT,
                                         None,  # 父窗口句柄
                                         None,  # 菜单句柄
                                         None,  # 关联模块句柄
                                         None)
            self._hwnd = hwnd
        return self._hwnd

    # ----- 托盘基本属性 -----

    @property
    def icon(self):
        """
        返回加载后的图标文件，如果未指定图标则返回默认图标

        可为该属性指定一个存在的ICO图标文件，用于修改托盘的图标
        """
        if self._icon is None:
            return win32gui.LoadIcon(None, win32con.IDI_APPLICATION)  # 默认图标
        else:
            image = win32gui.LoadImage(None,  # DLL或EXE的句柄
                                       self._icon,  # 图标位置
                                       win32gui.IMAGE_ICON,  # 加载 ICO 文件
                                       0,  # 宽度
                                       0,  # 高度
                                       win32gui.LR_DEFAULTCOLOR | win32gui.LR_DEFAULTSIZE | win32gui.LR_LOADFROMFILE
                                       )
            return image

    @icon.setter
    def icon(self, icon: str):
        if not os.path.isfile(icon):
            raise FileNotFoundError(f"位于 '{icon}' 的文件不存在，无法指定其为托盘的图标")
        else:
            self._icon = os.path.abspath(icon)  # TODO [临时] 自动更新托盘
        return

    @property
    def tip(self):
        """
        返回托盘的提示文本

        可以为该属性指定一个字符串或者一个实时返回提示文本的可调用对象，
        如果可调用，则其不应当接收任何参数
        """
        if callable(self._tip):
            return self._tip()
        else:
            return self._tip

    @tip.setter
    def tip(self, tip: str | _Callable):
        self._tip = tip  # TODO [临时] 自动更新托盘
        return

    @property
    def lp_data(self):
        """
        返回 Shell_NotifyIcon 函数所需的 lpData 结构

        未实现气球通知，请替换为 Windows 通知功能
        """
        uFlags = win32gui.NIF_MESSAGE | win32gui.NIF_ICON

        tip = self.tip
        if tip is not None:
            uFlags |= win32gui.NIF_TIP

        lpData = (self.hwnd,  # 通知窗口句柄
                  0,  # 图标标识符
                  uFlags,  # 可用操作标识符
                  self.uCallbackMessage,  # 自定义的 uCallbackMessage 信号
                  self.icon,  # 托盘图标
                  tip,  # 托盘提示文本
                  )
        return lpData

    # ----- 右键菜单功能 -----

    def menu(self):  # TODO [短期] 添加菜单支持
        # m = win32gui.CreatePopupMenu()  # CreateMenu
        # pos = win32gui.GetCursorPos()
        # item, extras = win32gui_struct.PackMENUITEMINFO(text='option_text')
        # win32gui.InsertMenuItem(m, 0, False, item)
        # item, extras = win32gui_struct.PackMENUITEMINFO(text='option_text',
        #                                                 fType=win32con.MFT_MENUBARBREAK)
        # win32gui.InsertMenuItem(m, 0, False, item)

        n = win32gui.CreatePopupMenu()  # CreateMenu
        pos = win32gui.GetCursorPos()
        item, extras = win32gui_struct.PackMENUITEMINFO(text='option_text',
                                                        dwTypeData=print('run'))
        win32gui.InsertMenuItem(n, 0, False, item)
        item, extras = win32gui_struct.PackMENUITEMINFO(text='option_text',
                                                        fType=win32con.MFT_MENUBARBREAK)
        win32gui.InsertMenuItem(n, 0, False, item)

        win32gui.SetForegroundWindow(self._hwnd)
        win32gui.TrackPopupMenu(n,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self._hwnd,
                                None)
        # win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    # ----- 托盘操作 -----

    def add(self):  # TODO [短期] 添加进程通信支持
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self.lp_data)
        return

    def modify(self):
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, self.lp_data)
        return

    def delete(self):
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self.lp_data)
        return


if __name__ == '__main__':
    tray = Tray()
    tray.tip = 'run'
    tray.mouse_right_click = tray.menu
    tray.add()
    win32gui.PumpMessages()
    # win32gui.PumpMessages()
