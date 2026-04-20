try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

import os
import sys
import webbrowser
from threading import Timer
from app import create_app, socketio

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    # 如果是在 PyInstaller 打包后的环境中运行
    if getattr(sys, 'frozen', False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(os.path.abspath(__file__))

    app = create_app()
    
    # 启动 1.5 秒后打开浏览器
    Timer(1.5, open_browser).start()
    
    print("EDMS is starting...")
    print("Please do not close this window while using the application.")
    print("URL: http://127.0.0.1:5000")
    
    socketio.run(app, host="127.0.0.1", port=5000, debug=False, allow_unsafe_werkzeug=True)
