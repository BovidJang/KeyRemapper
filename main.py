"""
main.py - 程序入口
按键重映射工具 v1.0
"""

import sys
import os

# 确保工作目录正确
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import MainWindow


def main():
    """主函数"""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        import traceback
        error_msg = f"程序启动失败:\n{e}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            import tkinter.messagebox as mb
            mb.showerror("错误", error_msg)
        except Exception:
            pass


if __name__ == "__main__":
    main()
