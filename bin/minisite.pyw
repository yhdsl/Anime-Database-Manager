# 网站启动模块 (启动层)

try:
    import common
except ModuleNotFoundError:
    from tkinter.messagebox import showerror
    showerror(title='ADM 错误', message='软件损坏，请尝试重新安装。')


def main():  # TODO[中期] (@YHDSL) 命令行转发&启动网页&任务栏角标
    common.check_environ()

    common.check_venv()

    return


if __name__ == '__main__':
    # noinspection PyBroadException
    try:
        main()
    except Exception:
        import traceback
        root = common.gui_exc_windows(exc=traceback.format_exc())
        root.mainloop()
