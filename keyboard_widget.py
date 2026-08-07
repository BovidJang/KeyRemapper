"""
keyboard_widget.py - 可视化键盘组件
完整QWERTY键盘布局（主键区+功能区+导航区+小键盘），一行排列。
布局按真实键盘比例设计。
"""

import tkinter as tk
from mouse_widget import MOUSE_VK_NAMES

# ── 虚拟键码 → 显示名称 ──────────────────────────────────────────
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

# ══════════════════════════════════════════════════════════════════
# 完整键盘布局  (label, vk_code, col, row, width)
#
# 区域定位（真实键盘比例）：
#   主键区    col  0.0 ~ 14.0   (Esc ~ RCtrl)
#   导航区    col 14.5 ~ 17.6   (Ins/PgUp/Del/PgDn + 方向键)
#   小键盘    col 18.1 ~ 21.5
#
# F12 右边 = Backspace 右边 (col 12.6)
# PrtSc/ScrLk/Pause 右边 = 导航区右边 (col 17.6)
# ══════════════════════════════════════════════════════════════════

KEYBOARD_LAYOUT = [
    # ═══ Row 0: Esc | F1-F4 | F5-F8 | F9-F12 | PrtSc ScrLk Pause ═══
    # F12 右边 = col 12.6 对齐 Backspace
    # PrtSc 右边 = col 17.6 对齐导航区
    [
        ("Esc",    0x1B,  0.0,   0, 1.2),
        ("",       0,     1.2,   0, 0.3),
        ("F1",     0x70,  1.5,   0, 1.0), ("F2",  0x71,  2.5,  0, 1.0),
        ("F3",     0x72,  3.5,   0, 1.0), ("F4",  0x73,  4.5,  0, 1.0),
        ("",       0,     5.5,   0, 0.3),
        ("F5",     0x74,  5.8,   0, 1.0), ("F6",  0x75,  6.8,  0, 1.0),
        ("F7",     0x76,  7.8,   0, 1.0), ("F8",  0x77,  8.8,  0, 1.0),
        ("",       0,     9.8,   0, 0.3),
        ("F9",     0x78, 10.1,   0, 1.0), ("F10", 0x79, 11.1,  0, 1.0),
        ("F11",    0x7A, 12.1,   0, 0.95), ("F12", 0x7B, 13.05, 0, 0.95),
        # PrtSc/ScrLk/Pause：右边对齐导航区(col 17.6)
        ("PrtSc",  0x2C, 14.5,   0, 1.03), ("ScrLk", 0x91, 15.53, 0, 1.03), ("Pause", 0x13, 16.56, 0, 1.03),
    ],
    # ═══ Row 1: ` 1-0 - = Bksp  |  Ins Home PgUp ══════════════════
    [
        ("`",     0xC0,  0.0, 1, 1.0),
        ("1",     0x31,  1.0, 1, 1.0), ("2",  0x32,  2.0, 1, 1.0),
        ("3",     0x33,  3.0, 1, 1.0), ("4",  0x34,  4.0, 1, 1.0),
        ("5",     0x35,  5.0, 1, 1.0), ("6",  0x36,  6.0, 1, 1.0),
        ("7",     0x37,  7.0, 1, 1.0), ("8",  0x38,  8.0, 1, 1.0),
        ("9",     0x39,  9.0, 1, 1.0), ("0",  0x30, 10.0, 1, 1.0),
        ("-",     0xBD, 11.0, 1, 1.0), ("=",  0xBB, 12.0, 1, 1.0),
        ("Bksp",  0x08, 13.0, 1, 1.0),
        # 导航区第一行：Ins Home PgUp
        ("Ins",   0x2D, 14.5,  1, 1.03), ("Home", 0x24, 15.53, 1, 1.03), ("PgUp", 0x21, 16.56, 1, 1.03),
    ],
    # ═══ Row 2: Tab Q-P [ ] \  |  Del End PgDn ════════════════════
    [
        ("Tab",   0x09,  0.0, 2, 1.4),
        ("Q",     0x51,  1.4, 2, 1.0), ("W",  0x57,  2.4, 2, 1.0),
        ("E",     0x45,  3.4, 2, 1.0), ("R",  0x52,  4.4, 2, 1.0),
        ("T",     0x54,  5.4, 2, 1.0), ("Y",  0x59,  6.4, 2, 1.0),
        ("U",     0x55,  7.4, 2, 1.0), ("I",  0x49,  8.4, 2, 1.0),
        ("O",     0x4F,  9.4, 2, 1.0), ("P",  0x50, 10.4, 2, 1.0),
        ("[",     0xDB, 11.4, 2, 1.0), ("]",  0xDD, 12.4, 2, 1.0),
        ("\\",    0xDC, 13.4, 2, 0.6),
        # 导航区第二行：Del End PgDn
        ("Del",   0x2E, 14.5,  2, 1.03), ("End", 0x23, 15.53, 2, 1.03), ("PgDn", 0x22, 16.56, 2, 1.03),
    ],
    # ═══ Row 3: Caps A-L ; ' Enter ═════════════════════════════════
    [
        ("Caps",  0x14,  0.0, 3, 1.7),
        ("A",     0x41,  1.7, 3, 1.0), ("S",  0x53,  2.7, 3, 1.0),
        ("D",     0x44,  3.7, 3, 1.0), ("F",  0x46,  4.7, 3, 1.0),
        ("G",     0x47,  5.7, 3, 1.0), ("H",  0x48,  6.7, 3, 1.0),
        ("J",     0x4A,  7.7, 3, 1.0), ("K",  0x4B,  8.7, 3, 1.0),
        ("L",     0x4C,  9.7, 3, 1.0), (";",  0xBA, 10.7, 3, 1.0),
        ("'",     0xDE, 11.7, 3, 1.0),
        ("Enter", 0x0D, 12.7, 3, 1.3),
    ],
    # ═══ Row 4: Shift Z-M , . / Shift  |  ↑ ══════════════════════
    [
        ("LShift", 0xA0,  0.0, 4, 2.2),
        ("Z",  0x5A,  2.2, 4, 1.0), ("X",  0x58,  3.2, 4, 1.0),
        ("C",  0x43,  4.2, 4, 1.0), ("V",  0x56,  5.2, 4, 1.0),
        ("B",  0x42,  6.2, 4, 1.0), ("N",  0x4E,  7.2, 4, 1.0),
        ("M",  0x4D,  8.2, 4, 1.0), (",",  0xBC,  9.2, 4, 1.0),
        (".",  0xBE, 10.2, 4, 1.0), ("/",  0xBF, 11.2, 4, 1.0),
        ("RShift", 0xA1, 12.2, 4, 1.8),
        # 导航区方向键上方：空 | ↑ | 空
        ("",  0, 14.5,  4, 1.03), ("↑", 0x26, 15.53, 4, 1.03), ("",  0, 16.56, 4, 1.03),
    ],
    # ═══ Row 5: Ctrl Win Alt Space Alt Win Menu Ctrl  |  ← ↓ → ════
    [
        ("LCtrl", 0xA2,  0.0, 5, 1.3),
        ("LWin",  0x5B,  1.3, 5, 1.0),
        ("LAlt",  0xA4,  2.3, 5, 1.3),
        ("Space", 0x20,  3.6, 5, 5.8),
        ("RAlt",  0xA5,  9.4, 5, 1.3),
        ("RWin",  0x5C, 10.7, 5, 1.0),
        ("Menu",  0x5D, 11.7, 5, 1.0),
        ("RCtrl", 0xA3, 12.7, 5, 1.3),
        # 方向键
        ("←", 0x25, 14.5, 5, 1.03), ("↓", 0x28, 15.53, 5, 1.03), ("→", 0x27, 16.56, 5, 1.03),
    ],
    # ═══ Row 6-9: 小键盘 ═════════════════════════════════════════
    [
        # Row 1 (小键盘)：Num / * -  —— 对齐主键盘 row 1
        ("Num", 0x90, 18.1, 1, 0.85), ("/", 0x6F, 18.95, 1, 0.85),
        ("*",   0x6A, 19.8,  1, 0.85), ("-", 0x6D, 20.65, 1, 0.85),
        # Row 2：7 8 9 +
        ("7", 0x67, 18.1,  2, 0.85), ("8", 0x68, 18.95, 2, 0.85),
        ("9", 0x69, 19.8,  2, 0.85), ("+", 0x6B, 20.65, 2, -2),
        # Row 3：4 5 6（+ 跨行）
        ("4", 0x64, 18.1,  3, 0.85), ("5", 0x65, 18.95, 3, 0.85),
        ("6", 0x66, 19.8,  3, 0.85),
        # Row 4：1 2 3 Enter（跨行）
        ("1", 0x61, 18.1,  4, 0.85), ("2", 0x62, 18.95, 4, 0.85),
        ("3", 0x63, 19.8,  4, 0.85), ("Enter", 0x10D, 20.65, 4, -2),
        # Row 5：0（宽） .
        ("0", 0x60, 18.1,  5, 1.7), (".", 0x6E, 19.8, 5, 0.85),
    ],
]

# 网格单位像素
KEY_UNIT   = 36
KEY_HEIGHT = 34


class KeyboardWidget(tk.Canvas):
    """可视化键盘"""

    def __init__(self, parent, hook_manager, on_change=None, on_select=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.hook_manager = hook_manager
        self.key_rects = {}     # {vk: (x1, y1, x2, y2)}
        self.selected_key = None
        self.remappings = {}
        self.macros = {}        # {触发vk: [vk1, vk2, ...]}
        self.mouse_macro = {}   # {触发vk: [鼠标vk1, 鼠标vk2, ...]}
        self._poll_after_id = None
        self._on_change = on_change   # 映射变化时的回调
        self._on_select = on_select   # 选中按键时的回调

        self.normal_color    = "#d4d4d4"
        self.selected_color  = "#4a9eff"
        self.mapped_color    = "#90ee90"
        self.macro_color     = "#ffcc00"
        self.mouse_color     = "#cc99ff"   # 鼠标绑定用浅紫色
        self.text_color      = "#333333"
        self.mapped_text_color = "#006600"
        self.border_color    = "#aaaaaa"

        self._draw_keyboard()

    def _draw_keyboard(self):
        self.delete("all")
        self.key_rects.clear()

        max_x = max_y = 0
        for row in KEYBOARD_LAYOUT:
            for label, vk, col, ri, w in row:
                if vk == 0:
                    continue
                if w < 0:
                    max_x = max(max_x, col + 0.85)
                    max_y = max(max_y, ri + abs(w))
                else:
                    max_x = max(max_x, col + w)
                    max_y = max(max_y, ri + 1)

        cw = int((max_x + 0.5) * KEY_UNIT)
        ch = int((max_y + 0.5) * KEY_HEIGHT)
        self.configure(width=cw, height=ch)

        for row in KEYBOARD_LAYOUT:
            for label, vk, col, ri, w in row:
                if vk == 0:
                    continue
                x1 = col * KEY_UNIT
                y1 = ri * KEY_HEIGHT
                if w < 0:
                    # 负数宽度表示跨行，绝对值=行数，宽度取绝对值
                    row_span = abs(w)
                    w_abs = 0.85
                    x2 = x1 + w_abs * KEY_UNIT - 2
                    y2 = y1 + row_span * KEY_HEIGHT - 2
                else:
                    x2 = x1 + w * KEY_UNIT - 2
                    y2 = y1 + KEY_HEIGHT - 2
                self.key_rects[vk] = (x1, y1, x2, y2)

                color = self._get_key_color(vk)
                if vk == self.selected_key:
                    color = self.selected_color

                self.create_rectangle(x1, y1, x2, y2,
                    fill=color, outline=self.border_color, width=1)

                has_binding = vk in self.remappings or vk in self.macros or vk in self.mouse_macro
                tc = self.mapped_text_color if has_binding else self.text_color
                fs = 8 if abs(w) >= 0.9 else 6
                dy = -5 if has_binding else 0
                self.create_text((x1+x2)/2, (y1+y2)/2+dy,
                    text=label, fill=tc,
                    font=("Microsoft YaHei", fs, "bold"))

                if vk in self.mouse_macro:
                    # 显示鼠标操作名称
                    names = [MOUSE_VK_NAMES.get(m, f"0x{m:02X}") for m in self.mouse_macro[vk]]
                    self.create_text((x1+x2)/2, (y1+y2)/2+10,
                        text="+".join(names), fill="#660099",
                        font=("Microsoft YaHei", 6))
                elif vk in self.remappings:
                    mvk = self.remappings[vk]
                    ml = VK_NAMES.get(mvk, chr(mvk) if 32<=mvk<127 else f"0x{mvk:02X}")
                    self.create_text((x1+x2)/2, (y1+y2)/2+10,
                        text=f"→{ml}", fill="#006600",
                        font=("Microsoft YaHei", 6))
                elif vk in self.macros:
                    self.create_text((x1+x2)/2, (y1+y2)/2+10,
                        text="宏", fill="#996600",
                        font=("Microsoft YaHei", 6))

        self.bind("<Button-1>", self._on_click)

    # ── 精确点击检测 ─────────────────────────────────────────────

    def _on_click(self, event):
        cx, cy = event.x, event.y
        for vk, (x1, y1, x2, y2) in self.key_rects.items():
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                if self.selected_key == vk:
                    # 再次点击已选中按键 → 取消选中
                    self.deselect_key()
                else:
                    self.select_key(vk)
                return
        # 点击空白处 → 取消选中
        self.deselect_key()

    def deselect_key(self):
        """取消选中"""
        if self.selected_key and self.selected_key in self.key_rects:
            orig = self._get_key_color(self.selected_key)
            self._set_color(self.selected_key, orig)
        self.selected_key = None
        self.hook_manager.stop_capture()
        if self._on_select:
            self._on_select(None, "none")

    def select_key(self, vk_code):
        """选中按键并立即进入绑定模式"""
        if self.selected_key and self.selected_key in self.key_rects:
            orig = self._get_key_color(self.selected_key)
            self._set_color(self.selected_key, orig)
        self.selected_key = vk_code
        self._set_color(vk_code, self.selected_color)
        if self._on_select:
            self._on_select(vk_code, "keyboard")
        # 直接进入绑定模式
        self.hook_manager.start_capture("keyboard")
        self._start_polling()

    def _set_color(self, vk, color):
        if vk in self.key_rects:
            x1, y1, x2, y2 = self.key_rects[vk]
            for item in self.find_overlapping(x1, y1, x2, y2):
                if self.type(item) == "rectangle":
                    self.itemconfig(item, fill=color)
                    break

    # ── 轮询捕获 ─────────────────────────────────────────────────

    def _start_polling(self):
        if self._poll_after_id is not None:
            self.after_cancel(self._poll_after_id)
        self._poll_captured()

    def _poll_captured(self):
        vk = self.hook_manager.poll_captured_key()
        if vk is not None:
            self._apply_captured(vk)
        else:
            self._poll_after_id = self.after(50, self._poll_captured)

    def _apply_captured(self, vk_code):
        self._poll_after_id = None
        self.hook_manager.stop_capture()
        changed = False
        if self.selected_key is not None and self.selected_key != vk_code:
            self.remappings[self.selected_key] = vk_code
            self.hook_manager.set_remappings(self.remappings)
            changed = True
        if self.selected_key and self.selected_key in self.key_rects:
            orig = self.mapped_color if self.selected_key in self.remappings else self.normal_color
            self._set_color(self.selected_key, orig)
        self.selected_key = None
        self._draw_keyboard()
        if changed and self._on_change:
            self._on_change()

    def clear_mapping(self, vk_code):
        if vk_code in self.remappings:
            del self.remappings[vk_code]
            self.hook_manager.set_remappings(self.remappings)
            self._draw_keyboard()
            if self._on_change:
                self._on_change()

    def clear_all_mappings(self):
        self.remappings.clear()
        self.hook_manager.set_remappings(self.remappings)
        self._draw_keyboard()
        if self._on_change:
            self._on_change()

    def set_remappings(self, remappings):
        self.remappings = {int(k): v for k, v in remappings.items()}
        self._draw_keyboard()

    def set_macros(self, macros):
        self.macros = {int(k): v for k, v in macros.items()}
        self._draw_keyboard()

    def set_mouse_macro(self, mouse_macro):
        self.mouse_macro = {int(k): [int(m) for m in v] for k, v in mouse_macro.items()}
        self._draw_keyboard()

    def get_remappings(self):
        return self.remappings.copy()

    def get_macros(self):
        return self.macros.copy()

    def get_mouse_macro(self):
        return self.mouse_macro.copy()

    def _get_key_color(self, vk):
        if vk in self.mouse_macro:
            return self.mouse_color
        if vk in self.macros:
            return self.macro_color
        if vk in self.remappings:
            return self.mapped_color
        return self.normal_color
