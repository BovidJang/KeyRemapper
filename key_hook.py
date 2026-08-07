"""
key_hook.py - Windows低级键盘钩子模块
使用 WH_KEYBOARD_LL 在OS把按键送给游戏之前拦截，实现真正的按键替换。
"""

import ctypes
from ctypes import wintypes, Structure, POINTER, byref, sizeof
import threading
import time
import queue

# ─── 常量 ────────────────────────────────────────────────────────
WH_KEYBOARD_LL = 13
WM_KEYDOWN    = 0x0100
WM_KEYUP      = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP   = 0x0105
LLKHF_INJECTED = 0x00000010

VK_PROCESSKEY = 0xE5

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP    = 0x0002
KEYEVENTF_EXTENDED = 0x0001

# 鼠标按键
VK_LBUTTON  = 0x01
VK_RBUTTON  = 0x02
VK_MBUTTON  = 0x04
VK_XBUTTON1 = 0x05
VK_XBUTTON2 = 0x06
VK_SCROLL_UP   = 0x100
VK_SCROLL_DOWN = 0x101
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040
MOUSEEVENTF_XDOWN      = 0x0080
MOUSEEVENTF_XUP        = 0x0100
MOUSEEVENTF_WHEEL      = 0x0800
WHEEL_DELTA = 120

EXTENDED_KEYS = {
    0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
    0x2D, 0x2E, 0x5B, 0x5C, 0x5D, 0x90, 0x2C, 0x13,
}

# ─── 结构体 ──────────────────────────────────────────────────────
class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

# 64位Windows: LPARAM=LONG_PTR(8字节有符号), WPARAM=UINT_PTR(8字节无符号), LRESULT=LONG_PTR
LPARAM_TYPE = ctypes.c_longlong
HOOKPROC = ctypes.CFUNCTYPE(ctypes.c_longlong, ctypes.c_int, ctypes.c_ulonglong, LPARAM_TYPE)

class KEYBDINPUT(Structure):
    _fields_ = [
        ("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

class MOUSEINPUT(Structure):
    _fields_ = [
        ("dx", ctypes.c_long), ("dy", ctypes.c_long),
        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_void_p),
    ]

class HARDWAREINPUT(Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

class INPUT(Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]

# ─── API ─────────────────────────────────────────────────────────
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
imm32 = ctypes.WinDLL("imm32", use_last_error=True)

user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.c_void_p, wintypes.DWORD]
user32.CallNextHookEx.restype = ctypes.c_longlong
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ulonglong, LPARAM_TYPE]
user32.GetAsyncKeyState.restype = ctypes.c_short
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

# ─── IME 辅助 ────────────────────────────────────────────────────
def _set_ime_open(hwnd, open_flag):
    try:
        ctx = imm32.ImmGetContext(hwnd)
        if ctx:
            imm32.ImmSetOpenStatus(ctx, open_flag)
            imm32.ImmReleaseContext(hwnd, ctx)
    except Exception:
        pass


# ─── 虚拟键码名称 ────────────────────────────────────────────────
VK_NAMES = {
    0x08: "Back",   0x09: "Tab",    0x0D: "Enter",
    0x10: "Shift",  0x11: "Ctrl",   0x12: "Alt",
    0x13: "Pause",  0x14: "Caps",   0x1B: "Esc",
    0x20: "Space",  0x21: "PgUp",   0x22: "PgDn",
    0x23: "End",    0x24: "Home",   0x25: "Left",
    0x26: "Up",     0x27: "Right",  0x28: "Down",
    0x2C: "PrtSc",  0x2D: "Insert", 0x2E: "Delete",
    0x5B: "LWin",   0x5C: "RWin",   0x5D: "Menu",
    0x90: "NumLk",  0x91: "ScrLk",
    0xA0: "LShift", 0xA1: "RShift",
    0xA2: "LCtrl",  0xA3: "RCtrl",
    0xA4: "LAlt",   0xA5: "RAlt",
    0x60: "Num0",  0x61: "Num1",  0x62: "Num2",
    0x63: "Num3",  0x64: "Num4",  0x65: "Num5",
    0x66: "Num6",  0x67: "Num7",  0x68: "Num8",
    0x69: "Num9",  0x6A: "Num*",  0x6B: "Num+",
    0x6D: "Num-",  0x6E: "Num.",
    0x6F: "Num/",  0x70: "F1",    0x71: "F2",
    0x72: "F3",    0x73: "F4",    0x74: "F5",
    0x75: "F6",    0x76: "F7",    0x77: "F8",
    0x78: "F9",    0x79: "F10",   0x7A: "F11",
    0x7B: "F12",   0x10D: "NumEnter",
}


class KeyHookManager:
    """键盘管理器（WH_KEYBOARD_LL 低级钩子版）"""

    def __init__(self):
        self.target_hwnd = None
        self.target_title = ""
        self.remappings = {}
        self.macros = {}
        self.mouse_bindings = {}
        self.mouse_button_macro = {}
        self.sending_keys = set()
        self.is_running = False
        self.hook_active = False

        # 捕获
        self.capture_mode = False
        self.captured_key = None
        self.capture_type = "keyboard"

        # 钩子
        self._hook_thread = None
        self._hook_thread_id = None
        self._hook_id = None
        self._hook_proc = None
        self._event_queue = queue.Queue()
        self._sending = False

        # 状态
        self._mapped_down = {}
        self._lock = threading.Lock()

    # ── 公共接口 ──────────────────────────────────────────────────

    def set_target(self, hwnd=None, title=""):
        with self._lock:
            self.target_hwnd = hwnd
            self.target_title = title

    def set_remappings(self, remappings):
        with self._lock:
            self.remappings = {int(k): v for k, v in remappings.items()}

    def set_macros(self, macros):
        with self._lock:
            self.macros = {int(k): v for k, v in macros.items()}

    def set_mouse_bindings(self, bindings):
        with self._lock:
            self.mouse_bindings = {int(k): v for k, v in bindings.items()}

    def set_mouse_button_macro(self, macros):
        with self._lock:
            self.mouse_button_macro = {int(k): v for k, v in macros.items()}

    def start(self):
        self._start_hook_thread()
        self.hook_active = True
        return True

    def stop(self):
        self.hook_active = False
        self._stop_hook_thread()

    def _start_hook_thread(self):
        if self.is_running:
            return
        self.is_running = True
        self._hook_thread = threading.Thread(target=self._hook_loop, daemon=True)
        self._hook_thread.start()
        # 等待钩子安装完成
        for _ in range(50):
            if self._hook_id:
                break
            import time; time.sleep(0.02)

    def _stop_hook_thread(self):
        if not self.is_running:
            return
        self.is_running = False
        if self._hook_id and self._hook_thread_id:
            try:
                user32.PostThreadMessageW(self._hook_thread_id, 0x0012, 0, 0)
            except Exception:
                pass
        if self._hook_thread:
            self._hook_thread.join(timeout=1)
            self._hook_thread = None

    def start_capture(self, capture_type="keyboard"):
        with self._lock:
            self.capture_mode = True
            self.captured_key = None
            self.capture_type = capture_type
        if not self.is_running:
            self._start_hook_thread()
        hwnd = user32.GetForegroundWindow()
        _set_ime_open(hwnd, False)

    def stop_capture(self):
        with self._lock:
            self.capture_mode = False
            self.captured_key = None
        hwnd = user32.GetForegroundWindow()
        _set_ime_open(hwnd, True)
        if not self.hook_active:
            self.stop()

    def poll_captured_key(self):
        with self._lock:
            if self.captured_key is not None:
                key = self.captured_key
                self.captured_key = None
                return key
        return None

    # ── 钩子线程 ─────────────────────────────────────────────────

    def _hook_loop(self):
        """钩子线程：安装钩子 + 消息循环"""
        self._hook_thread_id = kernel32.GetCurrentThreadId()
        self._hook_proc = HOOKPROC(self._hook_callback)

        self._hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._hook_proc, None, 0
        )
        if not self._hook_id:
            self.is_running = False
            return

        msg = wintypes.MSG()
        while self.is_running:
            # PeekMessage 不阻塞，让线程能检查 is_running
            while user32.PeekMessageW(byref(msg), None, 0, 0, 1):
                if msg.message == 0x0012:
                    self.is_running = False
                    break
                user32.TranslateMessage(byref(msg))
                user32.DispatchMessageW(byref(msg))
            if self.is_running:
                time.sleep(0.005)

        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None
        self.is_running = False

    def _hook_callback(self, nCode, wParam, lParam):
        if nCode >= 0 and not self._sending:
            try:
                kb = ctypes.cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
            except Exception:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            vk = kb.vkCode
            flags = kb.flags

            # 跳过注入的事件
            if flags & LLKHF_INJECTED:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            # 跳过鼠标按键
            if 0x01 <= vk <= 0x06:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            with self._lock:
                capture = self.capture_mode
                remap = dict(self.remappings)
                macro = dict(self.macros)
                running = self.hook_active
                target_hwnd = self.target_hwnd

            # 捕获模式：记录按键，放行
            if capture and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                actual_vk = vk
                if vk == VK_PROCESSKEY:
                    for t in range(1, 256):
                        if t != VK_PROCESSKEY and user32.GetAsyncKeyState(t) & 0x8000:
                            actual_vk = t
                            break
                with self._lock:
                    self.captured_key = actual_vk
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            if not running:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            # 检查目标窗口
            fg = user32.GetForegroundWindow()
            if target_hwnd and fg != target_hwnd:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            # 解析 IME 键
            actual_vk = vk
            if vk == VK_PROCESSKEY:
                for t in range(1, 256):
                    if t != VK_PROCESSKEY and user32.GetAsyncKeyState(t) & 0x8000:
                        actual_vk = t
                        break

            # ── 按下 ──
            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                is_repeat = bool(flags & (1 << 30))
                if is_repeat:
                    return user32.CallNextHookEx(None, nCode, wParam, lParam)

                # 宏
                if actual_vk in macro:
                    keys = macro[actual_vk]
                    threading.Thread(target=self._execute_macro, args=(keys,), daemon=True).start()
                    return -1  # 拦截

                # 重映射
                if actual_vk in remap:
                    mapped = remap[actual_vk]
                    self._send_key(vk, True)     # 弹起原键
                    self._send_key(mapped, False) # 按下映射键
                    with self._lock:
                        self._mapped_down[vk] = mapped
                    return -1  # 拦截

                return user32.CallNextHookEx(None, nCode, wParam, lParam)

            # ── 释放 ──
            if wParam in (WM_KEYUP, WM_SYSKEYUP):
                mapped = self._mapped_down.pop(vk, None)
                if mapped:
                    self._send_key(mapped, True)  # 释放映射键
                    return -1  # 拦截

                return user32.CallNextHookEx(None, nCode, wParam, lParam)

        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _process_event(self, event):
        action, vk, scan = event

        with self._lock:
            capture = self.capture_mode
            capture_type = self.capture_type
            remap = dict(self.remappings)
            macro = dict(self.macros)
            running = self.hook_active
            target_hwnd = self.target_hwnd

        # ── 捕获模式 ──
        if capture and action == 'down':
            actual_vk = vk
            if vk == VK_PROCESSKEY:
                for test_vk in range(1, 256):
                    if test_vk == VK_PROCESSKEY:
                        continue
                    if user32.GetAsyncKeyState(test_vk) & 0x8000:
                        actual_vk = test_vk
                        break
            with self._lock:
                self.captured_key = actual_vk
            return

        if not running:
            return

        # ── 检查目标窗口 ──
        fg = user32.GetForegroundWindow()
        if target_hwnd and fg != target_hwnd:
            return

        # ── 解析 IME 键 ──
        actual_vk = vk
        if vk == VK_PROCESSKEY:
            for test_vk in range(1, 256):
                if test_vk == VK_PROCESSKEY:
                    continue
                if user32.GetAsyncKeyState(test_vk) & 0x8000:
                    actual_vk = test_vk
                    break

        # ── 按下 ──
        if action == 'down':
            # 宏
            if actual_vk in macro:
                keys = macro[actual_vk]
                threading.Thread(target=self._execute_macro, args=(keys,), daemon=True).start()
                return -1

            # 重映射
            if actual_vk in remap:
                mapped = remap[actual_vk]
                # 弹起原键
                self._send_key(vk, True)
                # 按下映射键
                self._send_key(mapped, False)
                with self._lock:
                    self._mapped_down[vk] = mapped
                return -1  # 拦截原键

        # ── 释放 ──
        if action == 'up':
            mapped = self._mapped_down.pop(vk, None)
            if mapped:
                self._send_key(mapped, True)
                return -1  # 拦截原键

        return user32.CallNextHookEx(None, 0, 0, 0)

    def _execute_macro(self, keys):
        self._sending = True
        try:
            for vk in keys:
                if vk == 0x10D:
                    vk = 0x0D
                if vk == VK_SCROLL_UP:
                    self._send_mouse_wheel(1)
                elif vk == VK_SCROLL_DOWN:
                    self._send_mouse_wheel(-1)
                elif self._is_mouse_vk(vk):
                    self._send_mouse(vk, False)
                else:
                    self._send_key(vk, False)
                import time; time.sleep(0.03)
            import time; time.sleep(0.02)
            for vk in reversed(keys):
                if vk == 0x10D:
                    vk = 0x0D
                if vk in (VK_SCROLL_UP, VK_SCROLL_DOWN):
                    continue
                if self._is_mouse_vk(vk):
                    self._send_mouse(vk, True)
                else:
                    self._send_key(vk, True)
                import time; time.sleep(0.03)
        finally:
            self._sending = False

    @staticmethod
    def _is_mouse_vk(vk):
        return vk in (VK_LBUTTON, VK_RBUTTON, VK_MBUTTON, VK_XBUTTON1, VK_XBUTTON2)

    # ── 发送输入 ─────────────────────────────────────────────────

    def _send_key(self, vk_code, key_up):
        self._sending = True
        try:
            flags = KEYEVENTF_KEYUP if key_up else 0
            if vk_code in EXTENDED_KEYS:
                flags |= KEYEVENTF_EXTENDED
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = vk_code
            inp.union.ki.wScan = user32.MapVirtualKeyW(vk_code, 0)
            inp.union.ki.dwFlags = flags
            user32.SendInput(1, byref(inp), sizeof(INPUT))
        finally:
            self._sending = False

    def _send_mouse(self, vk_code, button_up):
        self._sending = True
        try:
            if vk_code == VK_LBUTTON:
                flags = MOUSEEVENTF_LEFTUP if button_up else MOUSEEVENTF_LEFTDOWN
            elif vk_code == VK_RBUTTON:
                flags = MOUSEEVENTF_RIGHTUP if button_up else MOUSEEVENTF_RIGHTDOWN
            elif vk_code == VK_MBUTTON:
                flags = MOUSEEVENTF_MIDDLEUP if button_up else MOUSEEVENTF_MIDDLEDOWN
            elif vk_code == VK_XBUTTON1:
                flags = MOUSEEVENTF_XUP if button_up else MOUSEEVENTF_XDOWN
            elif vk_code == VK_XBUTTON2:
                flags = MOUSEEVENTF_XUP if button_up else MOUSEEVENTF_XDOWN
            else:
                return
            inp = INPUT()
            inp.type = 0  # INPUT_MOUSE
            inp.union.mi.dwFlags = flags
            user32.SendInput(1, byref(inp), sizeof(INPUT))
        finally:
            self._sending = False

    def _send_mouse_wheel(self, direction):
        self._sending = True
        try:
            inp = INPUT()
            inp.type = 0
            inp.union.mi.dwFlags = MOUSEEVENTF_WHEEL
            inp.union.mi.mouseData = WHEEL_DELTA * direction
            user32.SendInput(1, byref(inp), sizeof(INPUT))
        finally:
            self._sending = False
