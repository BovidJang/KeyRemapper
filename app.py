"""
app.py - 主应用程序窗口
游戏列表、预设管理、可视化键盘+鼠标、编辑面板、状态栏
"""

import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes

from key_hook import KeyHookManager, VK_NAMES as KEY_VK_NAMES
from keyboard_widget import KeyboardWidget
from mouse_widget import MouseWidget
from profile_manager import ProfileManager

# 鼠标按键名称
MOUSE_VK_NAMES = {
    0x01: "左键", 0x02: "右键", 0x04: "中键",
    0x05: "侧键1", 0x06: "侧键2",
    0x100: "上滑", 0x101: "下滑",
}


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("按键重映射工具 v2.0 — 作者：BovidJang")
        self.root.geometry("1200x680")
        self.root.minsize(1000, 600)

        self.hook_manager = KeyHookManager()
        self.profile_manager = ProfileManager()
        self.agreed = False
        self._selected_game_index = 0

        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        self._load_current_profile()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(10, self._center_main_window)

    def _center_main_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def _center_dialog(self, dialog, w, h):
        dialog.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        dialog.geometry(f"{w}x{h}+{rx+(rw-w)//2}+{ry+(rh-h)//2}")

    # ── 菜单 ─────────────────────────────────────────────────────

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建游戏配置", command=self._new_profile)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)

    # ── 主布局 ───────────────────────────────────────────────────

    def _create_main_layout(self):
        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ===== 左侧：游戏 + 预设 =====
        left = tk.Frame(main, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left.pack_propagate(False)

        # 游戏列表
        tk.Label(left, text="🎮 游戏列表", font=("Microsoft YaHei", 10, "bold")).pack(pady=(0, 3))
        gl_frame = tk.Frame(left)
        gl_frame.pack(fill=tk.BOTH, expand=True)
        gl_scroll = tk.Scrollbar(gl_frame)
        gl_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.game_listbox = tk.Listbox(gl_frame, height=6, selectmode=tk.SINGLE,
                                        yscrollcommand=gl_scroll.set, font=("Microsoft YaHei", 9))
        self.game_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gl_scroll.config(command=self.game_listbox.yview)
        self.game_listbox.bind("<<ListboxSelect>>", self._on_game_select)

        gf = tk.Frame(left)
        gf.pack(fill=tk.X, pady=(2, 8))
        tk.Button(gf, text="添加", width=5, command=self._new_profile).pack(side=tk.LEFT)
        tk.Button(gf, text="删除", width=5, command=self._delete_profile).pack(side=tk.LEFT, padx=2)
        tk.Button(gf, text="重命名", width=5, command=self._rename_profile).pack(side=tk.LEFT)

        # 预设列表
        tk.Label(left, text="📋 预设方案", font=("Microsoft YaHei", 10, "bold")).pack(pady=(0, 3))
        pl_frame = tk.Frame(left)
        pl_frame.pack(fill=tk.X)
        pl_scroll = tk.Scrollbar(pl_frame)
        pl_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preset_listbox = tk.Listbox(pl_frame, height=6, selectmode=tk.SINGLE,
                                          yscrollcommand=pl_scroll.set, font=("Microsoft YaHei", 9))
        self.preset_listbox.pack(fill=tk.X)
        pl_scroll.config(command=self.preset_listbox.yview)
        self.preset_listbox.bind("<<ListboxSelect>>", self._on_preset_select)

        pf = tk.Frame(left)
        pf.pack(fill=tk.X, pady=(2, 0))
        tk.Button(pf, text="添加", width=5, command=self._add_preset).pack(side=tk.LEFT)
        tk.Button(pf, text="删除", width=5, command=self._delete_preset).pack(side=tk.LEFT, padx=2)
        tk.Button(pf, text="重命名", width=5, command=self._rename_preset).pack(side=tk.LEFT)

        # ===== 右侧：窗口选择 + 键盘/鼠标 + 编辑面板 =====
        right = tk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 目标窗口
        wf = tk.LabelFrame(right, text=" 🎯 目标窗口 ", font=("Microsoft YaHei", 9, "bold"))
        wf.pack(fill=tk.X, pady=(0, 4))
        wi = tk.Frame(wf)
        wi.pack(fill=tk.X, padx=5, pady=3)
        self.window_label = tk.Label(wi, text="未选择窗口", anchor=tk.W,
                                      font=("Microsoft YaHei", 9), fg="#666")
        self.window_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(wi, text="选择窗口", command=self._select_window).pack(side=tk.RIGHT)

        # 中间：键盘 + 鼠标
        center = tk.Frame(right)
        center.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # 键盘区域
        kb_frame = tk.LabelFrame(center, text=" ⌨️ 键盘 ",
                                  font=("Microsoft YaHei", 9, "bold"))
        kb_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hint_label = tk.Label(kb_frame, text="点击按键进行编辑",
                                    font=("Microsoft YaHei", 8), fg="#0066cc")
        self.hint_label.pack(pady=(2, 0))

        kb_container = tk.Frame(kb_frame)
        kb_container.pack(fill=tk.BOTH, expand=True, padx=3, pady=(0, 3))
        h_scroll = tk.Scrollbar(kb_container, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.keyboard_canvas = tk.Canvas(kb_container, xscrollcommand=h_scroll.set, bg="#f0f0f0")
        self.keyboard_canvas.pack(fill=tk.BOTH, expand=True)
        h_scroll.config(command=self.keyboard_canvas.xview)

        self.keyboard_widget = KeyboardWidget(
            self.keyboard_canvas, self.hook_manager,
            on_change=self._on_mapping_changed,
            on_select=self._on_key_selected
        )

        # 保存 on_select 原始回调，包装后同时清除鼠标选中
        _kb_original_on_select = self.keyboard_widget._on_select
        def _kb_on_select_with_clear(vk, source):
            self.mouse_widget.selected_btn = None
            self.mouse_widget._refresh_colors()
            if _kb_original_on_select:
                _kb_original_on_select(vk, source)
        self.keyboard_widget._on_select = _kb_on_select_with_clear
        self.keyboard_canvas.create_window((0, 0), window=self.keyboard_widget, anchor=tk.NW)
        self.keyboard_canvas.bind("<Configure>", lambda e: self.keyboard_canvas.configure(
            scrollregion=self.keyboard_canvas.bbox("all")))

        # 点击外部空白处 → 取消选中
        def on_root_click(event):
            # 检查点击位置是否在关键区域内部（不取消选中）
            targets = [
                self.keyboard_widget,
                self.mouse_widget,
                self.edit_content,
                self.edit_panel,
                self.start_btn,
                self.stop_btn,
                self.agree_btn,
            ]
            for w in targets:
                try:
                    x = w.winfo_rootx()
                    y = w.winfo_rooty()
                    w2 = x + w.winfo_width()
                    h2 = y + w.winfo_height()
                    if x <= event.x_root <= w2 and y <= event.y_root <= h2:
                        return
                except:
                    continue
            # 点击在空白处 → 取消选中
            self.keyboard_widget.deselect_key()
            self.mouse_widget.deselect_button()
        self.root.bind("<Button-1>", on_root_click, add="+")

        # 鼠标区域
        mouse_frame = tk.LabelFrame(center, text=" 🖱️ 鼠标 ",
                                     font=("Microsoft YaHei", 9, "bold"))
        mouse_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 0))

        self.mouse_widget = MouseWidget(
            mouse_frame, self.hook_manager,
            on_change=self._on_mapping_changed,
            on_select=self._on_key_selected
        )
        self.mouse_widget.pack(padx=3, pady=3)

        # ===== 编辑面板（底部） =====
        self.edit_panel = tk.LabelFrame(right, text=" ✏️ 编辑 ",
                                         font=("Microsoft YaHei", 9, "bold"))
        self.edit_panel.pack(fill=tk.X)

        self.edit_content = tk.Frame(self.edit_panel)
        self.edit_content.pack(fill=tk.X, padx=5, pady=5)

        self.edit_placeholder = tk.Label(self.edit_content,
                                          text="点击键盘或鼠标按键以编辑",
                                          font=("Microsoft YaHei", 9), fg="#999")
        self.edit_placeholder.pack()

        # ===== 控制按钮 =====
        ctrl = tk.Frame(right)
        ctrl.pack(fill=tk.X, pady=(4, 0))

        self.start_btn = tk.Button(ctrl, text="▶ 启动", command=self._on_start_click,
                                    bg="#4CAF50", fg="white", font=("Microsoft YaHei", 10, "bold"), width=10)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.stop_btn = tk.Button(ctrl, text="⏹ 停止", command=self._stop_hook,
                                   state=tk.DISABLED, font=("Microsoft YaHei", 10, "bold"), width=10)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(ctrl, text="🗑 清除当前预设", command=self._clear_all_mappings,
                   font=("Microsoft YaHei", 9), width=14).pack(side=tk.LEFT, padx=(0, 10))

        self.agree_btn = tk.Button(ctrl, text="⚠ 请阅读并同意相关协议",
                                    font=("Microsoft YaHei", 9), width=20,
                                    command=self._show_agreement,
                                    fg="#cc6600")
        self.agree_btn.pack(side=tk.LEFT)

        self.status_indicator = tk.Label(ctrl, text="● 未启动", fg="gray",
                                          font=("Microsoft YaHei", 10, "bold"))
        self.status_indicator.pack(side=tk.RIGHT)

        self._refresh_game_list()
        self._refresh_preset_list()

    def _create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="就绪",
                                    bd=1, relief=tk.SUNKEN,
                                    anchor=tk.W, font=("Microsoft YaHei", 9), padx=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ── 游戏列表 ─────────────────────────────────────────────────

    def _refresh_game_list(self):
        self.game_listbox.delete(0, tk.END)
        for p in self.profile_manager.get_profiles():
            prefix = "📌 " if p.get('is_builtin') else "  "
            self.game_listbox.insert(tk.END, f"{prefix}{p['name']}")
        current = self.profile_manager.get_current_profile()
        if current:
            for i, p in enumerate(self.profile_manager.get_profiles()):
                if p['name'] == current['name']:
                    self.game_listbox.selection_set(i)
                    self.game_listbox.see(i)
                    break

    def _on_game_select(self, event):
        sel = self.game_listbox.curselection()
        if sel:
            self._selected_game_index = sel[0]
            profiles = self.profile_manager.get_profiles()
            if sel[0] < len(profiles):
                self.profile_manager.set_current_profile(profiles[sel[0]]['name'])
                self._refresh_preset_list()
                self._load_current_profile()

    def _new_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("新建游戏配置")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 300, 130)
        tk.Label(dialog, text="请输入游戏名称:", font=("Microsoft YaHei", 10)).pack(pady=(15, 5))
        entry = tk.Entry(dialog, font=("Microsoft YaHei", 10))
        entry.pack(padx=20, fill=tk.X)
        entry.focus()
        bf = tk.Frame(dialog)
        bf.pack(pady=8)
        def ok():
            name = entry.get().strip()
            if not name:
                return
            if self.profile_manager.add_profile(name):
                self._refresh_game_list()
                dialog.destroy()
            else:
                messagebox.showerror("错误", "该名称已存在", parent=dialog)
        tk.Button(bf, text="确定", command=ok, width=6).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="取消", command=dialog.destroy, width=6).pack(side=tk.LEFT, padx=4)
        entry.bind("<Return>", lambda e: ok())

    def _delete_profile(self):
        # 先尝试从列表获取，失败则用保存的索引
        sel = self.game_listbox.curselection()
        idx = sel[0] if sel else self._selected_game_index
        profiles = self.profile_manager.get_profiles()
        if not profiles or idx >= len(profiles):
            return
        p = profiles[idx]
        if p.get('is_builtin'):
            messagebox.showinfo("提示", "内置配置不可删除")
            return
        if messagebox.askyesno("确认", f"确定删除 '{p['name']}'？"):
            self.profile_manager.delete_profile(p['name'])
            self._selected_game_index = 0
            self._refresh_game_list()
            self._refresh_preset_list()
            self._load_current_profile()

    def _rename_profile(self):
        sel = self.game_listbox.curselection()
        idx = sel[0] if sel else self._selected_game_index
        profiles = self.profile_manager.get_profiles()
        if not profiles or idx >= len(profiles):
            return
        p = profiles[idx]
        if p.get('is_builtin'):
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("重命名")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 300, 130)
        tk.Label(dialog, text="新名称:", font=("Microsoft YaHei", 10)).pack(pady=(15, 5))
        entry = tk.Entry(dialog, font=("Microsoft YaHei", 10))
        entry.insert(0, p['name'])
        entry.pack(padx=20, fill=tk.X)
        entry.focus()
        entry.select_range(0, tk.END)
        bf = tk.Frame(dialog)
        bf.pack(pady=8)
        def ok():
            new = entry.get().strip()
            if new and new != p['name']:
                old_remappings = self.profile_manager.get_remappings()
                self.profile_manager.delete_profile(p['name'])
                self.profile_manager.add_profile(new)
                new_p = self.profile_manager.get_profile(new)
                if new_p and old_remappings:
                    new_p['presets'][0]['remappings'] = old_remappings
                self._refresh_game_list()
                dialog.destroy()
        tk.Button(bf, text="确定", command=ok, width=6).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="取消", command=dialog.destroy, width=6).pack(side=tk.LEFT, padx=4)
        entry.bind("<Return>", lambda e: ok())

    # ── 预设列表 ─────────────────────────────────────────────────

    def _refresh_preset_list(self):
        self.preset_listbox.delete(0, tk.END)
        for i, p in enumerate(self.profile_manager.get_presets()):
            prefix = "▸ " if i == self.profile_manager.current_preset_index else "  "
            self.preset_listbox.insert(tk.END, f"{prefix}{p['name']}")
        idx = self.profile_manager.current_preset_index
        if idx < self.preset_listbox.size():
            self.preset_listbox.selection_set(idx)

    def _on_preset_select(self, event):
        sel = self.preset_listbox.curselection()
        if sel:
            self.profile_manager.set_current_preset(sel[0])
            self._refresh_preset_list()
            self._load_current_profile()

    def _add_preset(self):
        idx = self.profile_manager.add_preset()
        self._refresh_preset_list()
        self._load_current_profile()
        self.status_bar.config(text=f"已添加预设 {idx+1}")

    def _delete_preset(self):
        idx = self.profile_manager.current_preset_index
        presets = self.profile_manager.get_presets()
        if len(presets) <= 1:
            messagebox.showinfo("提示", "至少保留一个预设")
            return
        if messagebox.askyesno("确认", f"确定删除预设 '{presets[idx]['name']}'？"):
            self.profile_manager.delete_preset(idx)
            self._refresh_preset_list()
            self._load_current_profile()

    def _rename_preset(self):
        idx = self.profile_manager.current_preset_index
        presets = self.profile_manager.get_presets()
        if idx >= len(presets):
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("重命名预设")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 300, 130)
        tk.Label(dialog, text="新名称:", font=("Microsoft YaHei", 10)).pack(pady=(15, 5))
        entry = tk.Entry(dialog, font=("Microsoft YaHei", 10))
        entry.insert(0, presets[idx]['name'])
        entry.pack(padx=20, fill=tk.X)
        entry.focus()
        bf = tk.Frame(dialog)
        bf.pack(pady=8)
        def ok():
            new = entry.get().strip()
            if new:
                self.profile_manager.rename_preset(idx, new)
                self._refresh_preset_list()
                dialog.destroy()
        tk.Button(bf, text="确定", command=ok, width=6).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="取消", command=dialog.destroy, width=6).pack(side=tk.LEFT, padx=4)
        entry.bind("<Return>", lambda e: ok())

    # ── 加载/保存 ────────────────────────────────────────────────

    def _load_current_profile(self):
        remappings = self.profile_manager.get_remappings()
        macros = self.profile_manager.get_macros()
        mouse_macro = self.profile_manager.get_mouse_macro()
        mouse_bindings = self.profile_manager.get_mouse_bindings()
        preset = self.profile_manager.get_current_preset()
        mouse_button_macro = preset.get('mouse_button_macro', {}) if preset else {}
        self.keyboard_widget.set_remappings(remappings)
        self.keyboard_widget.set_macros(macros)
        self.keyboard_widget.set_mouse_macro(mouse_macro)
        self.mouse_widget.set_bindings(mouse_bindings)
        self.hook_manager.set_remappings(remappings)
        self.hook_manager.set_macros(macros)
        self.hook_manager.set_mouse_bindings(mouse_bindings)
        self.hook_manager.set_mouse_button_macro(mouse_button_macro)
        count = len(remappings) + len(macros) + len(mouse_macro) + len(mouse_bindings) + len(mouse_button_macro)
        name = preset['name'] if preset else "?"
        self.status_bar.config(text=f"当前: {name} | {count} 个绑定")

    def _on_mapping_changed(self):
        remappings = self.keyboard_widget.get_remappings()
        macros = self.keyboard_widget.get_macros()
        mouse_macro = self.keyboard_widget.get_mouse_macro()
        mouse_bindings = self.mouse_widget.get_bindings()
        preset = self.profile_manager.get_current_preset()
        mouse_button_macro = preset.get('mouse_button_macro', {}) if preset else {}
        self.profile_manager.set_remappings(remappings)
        self.profile_manager.set_macros(macros)
        self.profile_manager.set_mouse_macro(mouse_macro)
        self.profile_manager.set_mouse_bindings(mouse_bindings)
        self.hook_manager.set_remappings(remappings)
        self.hook_manager.set_macros(macros)
        self.hook_manager.set_mouse_bindings(mouse_bindings)
        self.hook_manager.set_mouse_button_macro(mouse_button_macro)
        count = len(remappings) + len(macros) + len(mouse_macro) + len(mouse_bindings) + len(mouse_button_macro)
        self.status_bar.config(text=f"已保存: {count} 个绑定")

    def _save_current_mappings(self):
        self._on_mapping_changed()

    # ── 编辑面板 ─────────────────────────────────────────────────

    def _on_key_selected(self, vk, source):
        """按键/鼠标按键被选中时更新编辑面板"""
        for w in self.edit_content.winfo_children():
            w.destroy()

        if source == "none":
            # 取消选中，显示占位提示
            self.edit_placeholder = tk.Label(self.edit_content,
                                              text="点击键盘或鼠标按键以编辑",
                                              font=("Microsoft YaHei", 9), fg="#999")
            self.edit_placeholder.pack()
        elif source == "keyboard":
            self._build_keyboard_edit_panel(vk)
        elif source == "mouse":
            self._build_mouse_edit_panel(vk)

    def _build_keyboard_edit_panel(self, vk):
        """构建键盘按键编辑面板"""
        from mouse_widget import MOUSE_BUTTONS
        name = KEY_VK_NAMES.get(vk, chr(vk) if 32 <= vk < 127 else f"0x{vk:02X}")
        has_remap = vk in self.keyboard_widget.remappings
        has_macro = vk in self.keyboard_widget.macros
        has_mouse = vk in self.keyboard_widget.mouse_macro

        # 顶部：按键名称
        top = tk.Frame(self.edit_content)
        top.pack(fill=tk.X, pady=(0, 4))
        tk.Label(top, text=f"按键: {name}", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.LEFT)

        if has_mouse:
            from mouse_widget import MOUSE_VK_NAMES
            names = [MOUSE_VK_NAMES.get(m, f"0x{m:02X}") for m in self.keyboard_widget.mouse_macro[vk]]
            tk.Label(top, text=f"🖱 → {'+'.join(names)}", font=("Microsoft YaHei", 9),
                      fg="#660099").pack(side=tk.LEFT, padx=10)
        elif has_remap:
            target = self.keyboard_widget.remappings[vk]
            tname = KEY_VK_NAMES.get(target, chr(target) if 32 <= target < 127 else f"0x{target:02X}")
            tk.Label(top, text=f"→ {tname}", font=("Microsoft YaHei", 9),
                      fg="#006600").pack(side=tk.LEFT, padx=10)
        elif has_macro:
            tk.Label(top, text="宏", font=("Microsoft YaHei", 9), fg="#996600").pack(side=tk.LEFT, padx=10)

        tk.Label(top, text="💡 点击其他按键直接绑定",
                  font=("Microsoft YaHei", 8), fg="#999").pack(side=tk.RIGHT)

        # 按钮行：宏 / 绑定鼠标 / 删除
        btns = tk.Frame(self.edit_content)
        btns.pack(fill=tk.X, pady=(0, 3))

        btn_w = 12
        tk.Button(btns, text="设为宏", width=btn_w,
                  command=lambda: self._edit_macro(vk)).pack(side=tk.LEFT, padx=3)
        tk.Button(btns, text="绑定鼠标操作", width=btn_w,
                  command=lambda: self._open_mouse_bind_dialog(vk)).pack(side=tk.LEFT, padx=3)
        if has_remap or has_macro or has_mouse:
            tk.Button(btns, text="删除绑定", width=btn_w, fg="red",
                       command=lambda: self._delete_binding(vk)).pack(side=tk.LEFT, padx=3)

        # 导入导出
        ie = tk.Frame(self.edit_content)
        ie.pack(fill=tk.X, pady=(2, 0))
        tk.Button(ie, text="导出预设", width=12, command=self._export_preset).pack(side=tk.LEFT, padx=3)
        tk.Button(ie, text="导入预设", width=12, command=self._import_preset).pack(side=tk.LEFT, padx=3)

    def _open_mouse_bind_dialog(self, keyboard_vk):
        """弹窗选择要绑定的鼠标操作"""
        from mouse_widget import MOUSE_BUTTONS

        dialog = tk.Toplevel(self.root)
        dialog.title("选择鼠标操作")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 360, 250)

        tk.Label(dialog, text="选择要绑定的鼠标操作:",
                  font=("Microsoft YaHei", 10, "bold")).pack(pady=(10, 6))

        # 网格布局，每行3个按钮
        grid = tk.Frame(dialog)
        grid.pack(pady=(0, 8))
        for i, btn_info in enumerate(MOUSE_BUTTONS):
            label, mvk = btn_info["label"], btn_info["vk"]
            r, c = divmod(i, 3)
            def choose(m=mvk):
                self._bind_mouse_to_key(keyboard_vk, m)
                dialog.destroy()
            tk.Button(grid, text=label, font=("Microsoft YaHei", 9), width=8, height=1,
                      command=choose).grid(row=r, column=c, padx=4, pady=3)

        tk.Button(dialog, text="取消", command=dialog.destroy, width=12).pack(pady=(4, 10))

    def _bind_mouse_to_key(self, keyboard_vk, mouse_vk):
        """将鼠标操作绑定到键盘按键"""
        current = list(self.keyboard_widget.mouse_macro.get(keyboard_vk, []))
        current.append(mouse_vk)
        self.keyboard_widget.mouse_macro[keyboard_vk] = current
        self.keyboard_widget._draw_keyboard()
        self._on_mapping_changed()
        self._on_key_selected(keyboard_vk, "keyboard")

    def _build_mouse_edit_panel(self, vk):
        """构建鼠标按键编辑面板"""
        name = MOUSE_VK_NAMES.get(vk, f"0x{vk:02X}")
        has_binding = vk in self.mouse_widget.bindings

        # 顶部：名称 + 绑定状态
        top = tk.Frame(self.edit_content)
        top.pack(fill=tk.X, pady=(0, 4))
        tk.Label(top, text=f"鼠标: {name}", font=("Microsoft YaHei", 11, "bold")).pack(side=tk.LEFT)

        if has_binding:
            target = self.mouse_widget.bindings[vk]
            tname = KEY_VK_NAMES.get(target, chr(target) if 32 <= target < 127 else f"0x{target:02X}")
            tk.Label(top, text=f"→ 键盘 {tname}", font=("Microsoft YaHei", 10),
                      fg="#006600").pack(side=tk.LEFT, padx=10)

        tk.Label(top, text="💡 点击键盘按键完成绑定",
                  font=("Microsoft YaHei", 8), fg="#999").pack(side=tk.RIGHT)

        # 按钮行1：设为宏 / 绑定鼠标操作 / 删除
        btns = tk.Frame(self.edit_content)
        btns.pack(fill=tk.X, pady=(2, 3))
        btn_w = 12
        tk.Button(btns, text="设为宏", width=btn_w,
                  command=lambda: self._edit_mouse_macro(vk)).pack(side=tk.LEFT, padx=3)
        tk.Button(btns, text="绑定鼠标操作", width=btn_w,
                  command=lambda: self._bind_mouse_action_to_mouse(vk)).pack(side=tk.LEFT, padx=3)
        if has_binding:
            tk.Button(btns, text="删除绑定", width=btn_w, fg="red",
                       command=lambda: self._delete_mouse_binding(vk)).pack(side=tk.LEFT, padx=3)

        # 按钮行2：导入导出
        ie = tk.Frame(self.edit_content)
        ie.pack(fill=tk.X, pady=(0, 0))
        tk.Button(ie, text="导出预设", width=12, command=self._export_preset).pack(side=tk.LEFT, padx=3)
        tk.Button(ie, text="导入预设", width=12, command=self._import_preset).pack(side=tk.LEFT, padx=3)

    def _delete_binding(self, vk):
        """删除键盘映射/宏/鼠标绑定"""
        self.keyboard_widget.remappings.pop(vk, None)
        self.keyboard_widget.macros.pop(vk, None)
        self.keyboard_widget.mouse_macro.pop(vk, None)
        self.keyboard_widget._draw_keyboard()
        self._on_mapping_changed()
        self._on_key_selected(vk, "keyboard")

    def _edit_mouse_macro(self, mouse_vk):
        """编辑鼠标按键的宏序列（触发后发送的键盘+鼠标操作）"""
        from mouse_widget import MOUSE_VK_NAMES

        dialog = tk.Toplevel(self.root)
        dialog.title("宏编辑器")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 460, 420)

        name = MOUSE_VK_NAMES.get(mouse_vk, f"0x{mouse_vk:02X}")
        tk.Label(dialog, text=f"鼠标 {name} 的宏序列",
                  font=("Microsoft YaHei", 10, "bold")).pack(pady=(10, 5))

        # 读取已有绑定（如果有单个键盘绑定，转换为宏步骤）
        current = []
        if mouse_vk in self.mouse_widget.bindings:
            current = [self.mouse_widget.bindings[mouse_vk]]
        steps = list(current)

        list_frame = tk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        lb = tk.Listbox(list_frame, font=("Consolas", 10), height=10)
        lb.pack(fill=tk.BOTH, expand=True)

        def get_step_name(s):
            if s in MOUSE_VK_NAMES:
                return f"🖱 {MOUSE_VK_NAMES[s]}"
            if s == 0x100:
                return "🖱 上滚轮"
            if s == 0x101:
                return "🖱 下滚轮"
            return KEY_VK_NAMES.get(s, chr(s) if 32 <= s < 127 else f"0x{s:02X}")

        def refresh_list():
            lb.delete(0, tk.END)
            for i, s in enumerate(steps):
                lb.insert(tk.END, f"{i+1}. {get_step_name(s)}")

        refresh_list()

        # 添加键盘按键
        add_frame = tk.Frame(dialog)
        add_frame.pack(fill=tk.X, padx=10, pady=(0, 3))
        tk.Label(add_frame, text="添加键盘按键:", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        adding = [False]
        add_label = tk.Label(add_frame, text="", font=("Microsoft YaHei", 9), fg="#0066cc")

        def start_add():
            adding[0] = True
            add_label.config(text="请按键盘...")
            self.hook_manager.start_capture("keyboard")

        def poll_add():
            if not adding[0]:
                return
            vk_code = self.hook_manager.poll_captured_key()
            if vk_code is not None:
                adding[0] = False
                steps.append(vk_code)
                refresh_list()
                add_label.config(text="已添加")
                self.hook_manager.stop_capture()
            else:
                dialog.after(50, poll_add)

        tk.Button(add_frame, text="添加按键", command=lambda: (start_add(), dialog.after(100, poll_add))
                  ).pack(side=tk.LEFT, padx=5)
        add_label.pack(side=tk.LEFT, padx=5)

        # 添加鼠标操作
        mouse_frame = tk.Frame(dialog)
        mouse_frame.pack(fill=tk.X, padx=10, pady=(0, 3))
        tk.Label(mouse_frame, text="添加鼠标操作:", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        for btn_info in [
            ("左键", 0x01), ("右键", 0x02), ("中键", 0x04),
            ("上滚轮", 0x100), ("下滚轮", 0x101),
            ("上侧键", 0x05), ("下侧键", 0x06),
        ]:
            label, mvk = btn_info
            tk.Button(mouse_frame, text=label, font=("Microsoft YaHei", 7), width=6,
                      command=lambda m=mvk: (steps.append(m), refresh_list())
                      ).pack(side=tk.LEFT, padx=1)

        # 操作按钮
        op_frame = tk.Frame(dialog)
        op_frame.pack(fill=tk.X, padx=10, pady=(4, 5))
        def remove_selected():
            sel = lb.curselection()
            if sel:
                del steps[sel[0]]
                refresh_list()
        def move_up():
            sel = lb.curselection()
            if sel and sel[0] > 0:
                i = sel[0]
                steps[i], steps[i-1] = steps[i-1], steps[i]
                refresh_list()
                lb.selection_set(i-1)
        def move_down():
            sel = lb.curselection()
            if sel and sel[0] < len(steps) - 1:
                i = sel[0]
                steps[i], steps[i+1] = steps[i+1], steps[i]
                refresh_list()
                lb.selection_set(i+1)
        tk.Button(op_frame, text="▲上移", command=move_up).pack(side=tk.LEFT, padx=2)
        tk.Button(op_frame, text="▼下移", command=move_down).pack(side=tk.LEFT, padx=2)
        tk.Button(op_frame, text="删除选中", command=remove_selected).pack(side=tk.LEFT, padx=2)
        tk.Button(op_frame, text="清空", command=lambda: (steps.clear(), refresh_list())).pack(side=tk.LEFT, padx=2)

        # 保存
        bf = tk.Frame(dialog)
        bf.pack(pady=(0, 10))
        def save():
            if steps:
                # 宏保存到 mouse_macro（键盘按键 → 鼠标操作序列）
                # 鼠标按键的宏：按此鼠标键时发送这些操作
                # 存储方式：用负数VK表示鼠标按键的宏
                # 实际上我们直接存到 mouse_widget 的 bindings 里不合适
                # 改为：把鼠标宏存到 profile 的 mouse_macro 字段
                # key=鼠标VK(负数避免冲突), value=操作序列
                self._save_mouse_macro(mouse_vk, steps)
            else:
                self._clear_mouse_macro(mouse_vk)
            dialog.destroy()
            self._on_key_selected(mouse_vk, "mouse")
        tk.Button(bf, text="保存", width=8, command=save).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="取消", width=8, command=dialog.destroy).pack(side=tk.LEFT, padx=4)

    def _save_mouse_macro(self, mouse_vk, steps):
        """保存鼠标按键宏"""
        profile = self.profile_manager.get_current_preset()
        if profile:
            if 'mouse_button_macro' not in profile:
                profile['mouse_button_macro'] = {}
            profile['mouse_button_macro'][str(mouse_vk)] = steps
            self.profile_manager.save_current_profile()

    def _clear_mouse_macro(self, mouse_vk):
        """清除鼠标按键宏"""
        profile = self.profile_manager.get_current_preset()
        if profile and 'mouse_button_macro' in profile:
            profile['mouse_button_macro'].pop(str(mouse_vk), None)
            self.profile_manager.save_current_profile()

    def _bind_mouse_action_to_mouse(self, mouse_vk):
        """将一个鼠标操作绑定到另一个鼠标操作（弹窗选择）"""
        from mouse_widget import MOUSE_BUTTONS

        dialog = tk.Toplevel(self.root)
        dialog.title("选择鼠标操作")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 360, 250)

        name = MOUSE_VK_NAMES.get(mouse_vk, f"0x{mouse_vk:02X}")
        tk.Label(dialog, text=f"鼠标 {name} 触发时同时执行:",
                  font=("Microsoft YaHei", 10, "bold")).pack(pady=(10, 6))

        grid = tk.Frame(dialog)
        grid.pack(pady=(0, 8))
        for i, btn_info in enumerate(MOUSE_BUTTONS):
            label, mvk = btn_info["label"], btn_info["vk"]
            if mvk == mouse_vk:
                continue  # 跳过自身
            r, c = divmod(i, 3)
            def choose(m=mvk):
                # 把目标鼠标操作加入到该鼠标按键的宏序列
                profile = self.profile_manager.get_current_preset()
                if profile:
                    if 'mouse_button_macro' not in profile:
                        profile['mouse_button_macro'] = {}
                    key = str(mouse_vk)
                    steps = profile['mouse_button_macro'].get(key, [])
                    if not steps and mouse_vk in self.mouse_widget.bindings:
                        steps = [self.mouse_widget.bindings[mouse_vk]]
                    steps.append(m)
                    profile['mouse_button_macro'][key] = steps
                    self.profile_manager.save_current_profile()
                dialog.destroy()
                self._on_key_selected(mouse_vk, "mouse")
            tk.Button(grid, text=label, font=("Microsoft YaHei", 9), width=8, height=1,
                      command=choose).grid(row=r, column=c, padx=4, pady=3)

        tk.Button(dialog, text="取消", command=dialog.destroy, width=12).pack(pady=(4, 10))

    def _delete_mouse_binding(self, vk):
        """删除鼠标绑定"""
        self.mouse_widget.clear_binding(vk)
        self._on_mapping_changed()
        self._on_key_selected(vk, "mouse")

    def _edit_macro(self, vk):
        """打开宏编辑器"""
        dialog = tk.Toplevel(self.root)
        dialog.title("宏编辑器")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 460, 420)

        from mouse_widget import MOUSE_VK_NAMES

        name = KEY_VK_NAMES.get(vk, f"0x{vk:02X}")
        tk.Label(dialog, text=f"按键 {name} 的宏序列",
                  font=("Microsoft YaHei", 10, "bold")).pack(pady=(10, 5))

        current_macro = self.keyboard_widget.macros.get(vk, [])
        steps = list(current_macro)

        list_frame = tk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        lb = tk.Listbox(list_frame, font=("Consolas", 10), height=10)
        lb.pack(fill=tk.BOTH, expand=True)

        def get_step_name(s):
            if s in MOUSE_VK_NAMES:
                return f"🖱 {MOUSE_VK_NAMES[s]}"
            if s == 0x100:
                return "🖱 上滚轮"
            if s == 0x101:
                return "🖱 下滚轮"
            return KEY_VK_NAMES.get(s, chr(s) if 32 <= s < 127 else f"0x{s:02X}")

        def refresh_list():
            lb.delete(0, tk.END)
            for i, s in enumerate(steps):
                lb.insert(tk.END, f"{i+1}. {get_step_name(s)}")

        refresh_list()

        # 添加键盘按键
        add_frame = tk.Frame(dialog)
        add_frame.pack(fill=tk.X, padx=10, pady=(0, 3))
        tk.Label(add_frame, text="添加键盘按键:", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        adding = [False]
        add_label = tk.Label(add_frame, text="", font=("Microsoft YaHei", 9), fg="#0066cc")

        def start_add():
            adding[0] = True
            add_label.config(text="请按键盘...")
            self.hook_manager.start_capture("keyboard")

        def poll_add():
            if not adding[0]:
                return
            vk_code = self.hook_manager.poll_captured_key()
            if vk_code is not None:
                adding[0] = False
                steps.append(vk_code)
                refresh_list()
                add_label.config(text="已添加")
                self.hook_manager.stop_capture()
            else:
                dialog.after(50, poll_add)

        def on_add_key():
            start_add()
            dialog.after(100, poll_add)

        tk.Button(add_frame, text="添加按键", command=on_add_key).pack(side=tk.LEFT, padx=5)
        add_label.pack(side=tk.LEFT, padx=5)

        # 添加鼠标操作
        mouse_frame = tk.Frame(dialog)
        mouse_frame.pack(fill=tk.X, padx=10, pady=(0, 3))
        tk.Label(mouse_frame, text="添加鼠标操作:", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        for btn_info in [
            ("左键", 0x01), ("右键", 0x02), ("按下滚轮", 0x04),
            ("上滚轮", 0x100), ("下滚轮", 0x101),
            ("上侧键", 0x05), ("下侧键", 0x06),
        ]:
            label, mvk = btn_info
            tk.Button(mouse_frame, text=label, font=("Microsoft YaHei", 7),
                      width=6,
                      command=lambda m=mvk: (steps.append(m), refresh_list())
                      ).pack(side=tk.LEFT, padx=1)

        # 操作按钮
        op_frame = tk.Frame(dialog)
        op_frame.pack(fill=tk.X, padx=10, pady=(4, 5))
        def remove_selected():
            sel = lb.curselection()
            if sel:
                del steps[sel[0]]
                refresh_list()
        def move_up():
            sel = lb.curselection()
            if sel and sel[0] > 0:
                i = sel[0]
                steps[i], steps[i-1] = steps[i-1], steps[i]
                refresh_list()
                lb.selection_set(i-1)
        def move_down():
            sel = lb.curselection()
            if sel and sel[0] < len(steps) - 1:
                i = sel[0]
                steps[i], steps[i+1] = steps[i+1], steps[i]
                refresh_list()
                lb.selection_set(i+1)
        tk.Button(op_frame, text="▲上移", command=move_up).pack(side=tk.LEFT, padx=2)
        tk.Button(op_frame, text="▼下移", command=move_down).pack(side=tk.LEFT, padx=2)
        tk.Button(op_frame, text="删除选中", command=remove_selected).pack(side=tk.LEFT, padx=2)
        tk.Button(op_frame, text="清空", command=lambda: (steps.clear(), refresh_list())).pack(side=tk.LEFT, padx=2)

        # 确定/取消
        bf = tk.Frame(dialog)
        bf.pack(pady=(0, 10))
        def save_macro():
            if steps:
                self.keyboard_widget.macros[vk] = steps
                self.keyboard_widget.remappings.pop(vk, None)
            else:
                self.keyboard_widget.macros.pop(vk, None)
            self.keyboard_widget._draw_keyboard()
            self._on_mapping_changed()
            dialog.destroy()
            self._on_key_selected(vk, "keyboard")
        tk.Button(bf, text="保存", width=8, command=save_macro).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="取消", width=8, command=dialog.destroy).pack(side=tk.LEFT, padx=4)

    # ── 导入导出 ─────────────────────────────────────────────────

    def _export_preset(self):
        code = self.profile_manager.export_preset()
        if not code:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("导出预设")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 500, 160)
        tk.Label(dialog, text="复制以下字符串分享给他人:", font=("Microsoft YaHei", 9)).pack(pady=(10, 5))
        te = tk.Text(dialog, height=3, font=("Consolas", 9), wrap=tk.WORD)
        te.pack(fill=tk.X, padx=10)
        te.insert("1.0", code)
        te.config(state=tk.DISABLED)
        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.status_bar.config(text="已复制到剪贴板")
        bf = tk.Frame(dialog)
        bf.pack(pady=8)
        tk.Button(bf, text="📋 复制", width=10, command=copy).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="关闭", width=10, command=dialog.destroy).pack(side=tk.LEFT, padx=4)

    def _import_preset(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("导入预设")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 500, 160)
        tk.Label(dialog, text="粘贴预设字符串:", font=("Microsoft YaHei", 9)).pack(pady=(10, 5))
        te = tk.Text(dialog, height=3, font=("Consolas", 9), wrap=tk.WORD)
        te.pack(fill=tk.X, padx=10)
        def paste():
            try:
                te.clipboard_get()
            except:
                pass
        def do_import():
            code = te.get("1.0", tk.END).strip()
            preset = self.profile_manager.import_preset(code)
            if preset:
                idx = self.profile_manager.add_preset(preset['name'])
                presets = self.profile_manager.get_presets()
                presets[-1]['remappings'] = preset.get('remappings', {})
                presets[-1]['macros'] = preset.get('macros', {})
                presets[-1]['mouse_bindings'] = preset.get('mouse_bindings', {})
                self.profile_manager.save_current_profile()
                self._refresh_preset_list()
                self._load_current_profile()
                dialog.destroy()
                self.status_bar.config(text=f"已导入预设: {preset['name']}")
            else:
                messagebox.showerror("错误", "导入失败，字符串无效", parent=dialog)
        bf = tk.Frame(dialog)
        bf.pack(pady=8)
        tk.Button(bf, text="导入", width=10, command=do_import).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="取消", width=10, command=dialog.destroy).pack(side=tk.LEFT, padx=4)

    # ── 窗口选择 ─────────────────────────────────────────────────

    def _select_window(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("选择目标窗口")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 480, 400)
        tk.Label(dialog, text="选择目标游戏窗口:", font=("Microsoft YaHei", 10, "bold")).pack(pady=(10, 5))
        lf = tk.Frame(dialog)
        lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        sb = tk.Scrollbar(lf)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb = tk.Listbox(lf, font=("Consolas", 9), yscrollcommand=sb.set)
        lb.pack(fill=tk.BOTH, expand=True)
        sb.config(command=lb.yview)
        windows = self._get_window_list()
        for hwnd, title in windows:
            lb.insert(tk.END, f"{title}  [0x{hwnd:08X}]")
        if windows:
            lb.selection_set(0)
        def on_ok():
            sel = lb.curselection()
            if sel and sel[0] < len(windows):
                hwnd, title = windows[sel[0]]
                self.hook_manager.set_target(hwnd=hwnd, title=title)
                dt = title[:40] + "..." if len(title) > 40 else title
                self.window_label.config(text=f"{dt}  [0x{hwnd:08X}]", fg="#333")
                dialog.destroy()
        bf = tk.Frame(dialog)
        bf.pack(pady=(0, 10))
        tk.Button(bf, text="确定", width=8, command=on_ok).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="取消", width=8, command=dialog.destroy).pack(side=tk.LEFT, padx=4)

    def _get_window_list(self):
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        windows = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, lParam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.strip()
                    if title:
                        windows.append((hwnd, title))
            return True
        user32.EnumWindows(WNDENUMPROC(cb), 0)
        return windows

    # ── 启动/停止 ────────────────────────────────────────────────

    def _start_hook(self):
        # 先检查协议
        if not self.agreed:
            self._show_agreement()
            if not self.agreed:
                return
        # 检查目标窗口
        if not self.hook_manager.target_hwnd:
            messagebox.showwarning("提示", "请先选择目标游戏窗口")
            return
        # 检查是否有映射
        has_mapping = (self.keyboard_widget.remappings or
                       self.keyboard_widget.macros or
                       self.keyboard_widget.mouse_macro or
                       self.mouse_widget.bindings)
        if not has_mapping:
            messagebox.showinfo("提示", "请先设置至少一个按键映射")
            return
        # 启动
        self.hook_manager.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_indicator.config(text="● 运行中", fg="#4CAF50")
        self.status_bar.config(text=f"✅ 运行中 | {self.hook_manager.target_title}")

    def _on_start_click(self):
        """启动按钮点击"""
        import traceback, os
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error.log")
        try:
            with open(log_path, "a") as f:
                f.write(f"\n--- 点击启动 agreed={self.agreed} hwnd={self.hook_manager.target_hwnd} ---\n")
            self._start_hook()
            with open(log_path, "a") as f:
                f.write(f"--- 启动完成 ---\n")
        except Exception as e:
            with open(log_path, "a") as f:
                traceback.print_exc(file=f)
            messagebox.showerror("错误", f"启动出错: {e}")

    def _stop_hook(self):
        self.hook_manager.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_indicator.config(text="● 已停止", fg="red")
        self.status_bar.config(text="⏹ 已停止")

    def _clear_all_mappings(self):
        remappings = self.keyboard_widget.remappings
        macros = self.keyboard_widget.macros
        mouse_bindings = self.mouse_widget.bindings
        total = len(remappings) + len(macros) + len(mouse_bindings)
        if total == 0:
            messagebox.showinfo("提示", "当前没有绑定")
            return
        if messagebox.askyesno("确认清除", f"确定清除当前预设的 {total} 个绑定吗？"):
            self.keyboard_widget.remappings.clear()
            self.keyboard_widget.macros.clear()
            self.mouse_widget.bindings.clear()
            self.keyboard_widget._draw_keyboard()
            self.mouse_widget._draw_mouse()
            self._on_mapping_changed()

    def _show_agreement(self):
        """显示用户协议弹窗"""
        dialog = tk.Toplevel(self.root)
        dialog.title("用户协议")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog, 520, 500)

        tk.Label(dialog, text="用户协议与隐私政策",
                  font=("Microsoft YaHei", 12, "bold")).pack(pady=(10, 5))

        # 协议文本
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        txt = tk.Text(text_frame, font=("Microsoft YaHei", 9),
                       wrap=tk.WORD, yscrollcommand=scrollbar.set)
        txt.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=txt.yview)

        txt.insert("1.0", """用户协议与隐私政策

一、软件说明
本软件是一款按键重映射工具，用于在游戏窗口中重新映射键盘和鼠标按键。
软件通过标准 Windows API (GetAsyncKeyState / SendInput) 实现按键检测和发送，
不修改游戏内存、不注入DLL、不使用hook回调,正常操作无任何游戏封禁风险(仅限于冒险岛)。

二、使用须知
1. 本工具仅供个人学习和娱乐使用
2. 使用本工具造成的任何后果由用户自行承担
3. 请遵守相关游戏的服务条款
4. 本工具不保证在所有游戏中都能正常工作

三、隐私政策
1. 本软件不会收集任何个人信息
2. 本软件不会联网发送任何数据
3. 配置文件保存在本地，不会上传到任何服务器
4. 软件运行期间仅检测键盘和鼠标输入状态

四、免责声明
1. 本软件按"现状"提供，不作任何明示或暗示的保证
2. 开发者不对使用本软件造成的任何直接或间接损失负责
3. 用户在使用前应自行评估风险
4. 本软件不制作任何违反游戏安全条例的相关功能

五、协议更新
开发者保留随时修改本协议的权利。
继续使用本软件即表示您接受修改后的协议。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
作者：BovidJang
发布平台：BiliBili / Github
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
请滚动阅读完整协议后，点击下方按钮同意
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""")
        txt.config(state=tk.DISABLED)

        # 同意按钮 — 先创建，后面绑定命令
        def do_agree():
            self.agreed = True
            self.agree_btn.config(text="✔ 您已同意相关协议", fg="#006600")
            dialog.destroy()

        agree_btn = tk.Button(dialog, text="⚠ 请滚动到底部后再同意",
                               font=("Microsoft YaHei", 14, "bold"),
                               fg="gray", bg="#e0e0e0",
                               width=35, height=2,
                               state=tk.DISABLED)
        agree_btn.pack(pady=(10, 15), ipadx=10, ipady=5)

        # 滚动检测
        def check_scroll(*args):
            first, last = txt.yview()
            if last >= 0.95:
                agree_btn.config(text="✔ 我已详细阅读并同意上述协议",
                                  fg="white", bg="#4CAF50",
                                  activebackground="#45a049",
                                  state=tk.NORMAL,
                                  command=do_agree)

        def on_wheel(event):
            txt.yview_scroll(int(-1 * (event.delta / 120)), "units")
            dialog.after(30, check_scroll)
            return "break"

        txt.bind("<MouseWheel>", on_wheel)
        scrollbar.config(command=lambda *a: (txt.yview(*a), check_scroll()))

    def _show_help(self):
        messagebox.showinfo("使用说明", """按键重映射工具 v2.0 - 使用说明

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 基本步骤：
1. 选择目标游戏窗口
2. 点击键盘/鼠标按键进行绑定
3. 同意用户协议
4. 点击「启动」开始生效

⌨️ 键盘映射：
• 点击键盘按键 → 直接按新键完成绑定
• 设为宏 → 编辑按键序列（支持混入鼠标操作）
• 绑定鼠标操作 → 弹窗选择鼠标按键加入宏

🖱️ 鼠标绑定：
• 点击左侧鼠标按键 → 按键盘按键完成绑定
• 鼠标按键只能绑定到键盘按键

📋 预设管理：
• 每个游戏可创建多个预设方案
• 支持导出/导入预设（分享字符串）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
作者：BovidJang
发布平台：BiliBili / Github
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    def _show_about(self):
        messagebox.showinfo("关于",
            "按键重映射工具 v2.0\n\n"
            "支持键盘映射、鼠标映射、按键宏")

    def _on_close(self):
        self.hook_manager.stop()
        self._save_current_mappings()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
