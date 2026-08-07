"""
mouse_widget.py - 鼠标按键列表组件
以方块列表形式展示鼠标按键，支持点击选择
"""

import tkinter as tk

# 鼠标按键定义
MOUSE_BUTTONS = [
    {"id": "left",       "label": "左键",     "vk": 0x01},
    {"id": "right",      "label": "右键",     "vk": 0x02},
    {"id": "middle",     "label": "中键",     "vk": 0x04},
    {"id": "scroll_up",  "label": "上滚轮",   "vk": 0x100},
    {"id": "scroll_down","label": "下滚轮",   "vk": 0x101},
    {"id": "side1",      "label": "上侧键",   "vk": 0x05},
    {"id": "side2",      "label": "下侧键",   "vk": 0x06},
]

MOUSE_VK_NAMES = {b["vk"]: b["label"] for b in MOUSE_BUTTONS}


class MouseWidget(tk.Frame):
    """鼠标按键列表"""

    def __init__(self, parent, hook_manager, on_change=None, on_select=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.hook_manager = hook_manager
        self.bindings = {}      # {鼠标vk: 键盘vk}
        self.selected_btn = None
        self._on_change = on_change
        self._on_select = on_select
        self._buttons = {}      # {vk: button_widget}

        self.normal_color = "#d4d4d4"
        self.selected_color = "#4a9eff"
        self.mapped_color = "#90ee90"
        self.btn_width = 80
        self.btn_height = 36

        self._build_ui()

    def _build_ui(self):
        for btn in MOUSE_BUTTONS:
            vk = btn["vk"]
            f = tk.Frame(self)
            f.pack(pady=2)

            b = tk.Button(f, text=btn["label"], width=14, height=1,
                          font=("Microsoft YaHei", 10, "bold"),
                          relief=tk.RAISED, bd=1,
                          command=lambda v=vk: self.select_button(v))
            b.pack()
            self._buttons[vk] = b

        self._refresh_colors()

    def _refresh_colors(self):
        for vk, b in self._buttons.items():
            if vk == self.selected_btn:
                b.config(bg=self.selected_color, activebackground=self.selected_color)
            elif vk in self.bindings:
                b.config(bg=self.mapped_color, activebackground=self.mapped_color)
            else:
                b.config(bg=self.normal_color, activebackground=self.normal_color)

        # 显示绑定状态
        if not hasattr(self, '_status_label'):
            self._status_label = tk.Label(self, text="", font=("Microsoft YaHei", 8),
                                           fg="#666", wraplength=200)
            self._status_label.pack(pady=(6, 0))

        lines = []
        for btn in MOUSE_BUTTONS:
            vk = btn["vk"]
            if vk in self.bindings:
                from key_hook import VK_NAMES
                target = self.bindings[vk]
                name = VK_NAMES.get(target, chr(target) if 32 <= target < 127 else f"0x{target:02X}")
                lines.append(f"{btn['label']} → {name}")
        self._status_label.config(text="\n".join(lines) if lines else "")

    def select_button(self, vk):
        if self.selected_btn == vk:
            # 再次点击已选中按键 → 取消选中
            self.deselect_button()
            return
        self.selected_btn = vk
        self._refresh_colors()
        if self._on_select:
            self._on_select(vk, "mouse")
        # 直接进入键盘绑定模式
        self.hook_manager.start_capture("keyboard")
        self._start_poll_capture()

    def deselect_button(self):
        """取消选中"""
        self.selected_btn = None
        self._refresh_colors()
        self.hook_manager.stop_capture()
        if self._on_select:
            self._on_select(None, "none")

    def _start_poll_capture(self):
        """轮询捕获的键盘按键"""
        vk = self.hook_manager.poll_captured_key()
        if vk is not None:
            self.apply_binding(self.selected_btn, vk)
        else:
            self.after(50, self._start_poll_capture)

    def set_bindings(self, bindings):
        self.bindings = {int(k): v for k, v in bindings.items()}
        self._refresh_colors()

    def get_bindings(self):
        return self.bindings.copy()

    def clear_binding(self, vk):
        if vk in self.bindings:
            del self.bindings[vk]
            self._refresh_colors()
            if self._on_change:
                self._on_change()

    def apply_binding(self, mouse_vk, keyboard_vk):
        self.bindings[mouse_vk] = keyboard_vk
        self._refresh_colors()
        if self._on_change:
            self._on_change()
