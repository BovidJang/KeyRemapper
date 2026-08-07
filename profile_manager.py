"""
profile_manager.py - 游戏配置管理器
管理游戏列表、预设方案、按键映射、宏和鼠标绑定
"""

import json
import os
import base64

# 默认配置文件路径（与exe同目录）
DEFAULT_CONFIG_FILE = "profiles.json"

# 内置游戏配置
BUILTIN_GAMES = [
    {
        "name": "冒险岛怀旧服",
        "description": "MapleStory Classic - Nostalgic Server",
        "presets": [
            {
                "name": "预设1",
                "remappings": {},
                "macros": {0x43: [0x11, 0x43]},  # C → Ctrl+C
                "mouse_bindings": {}
            }
        ],
        "is_builtin": True
    }
]


def _make_preset(name="预设1"):
    """创建空白预设"""
    return {"name": name, "remappings": {}, "macros": {}, "mouse_macro": {}, "mouse_bindings": {}}


def _migrate_profile(profile):
    """将旧格式（remappings平铺）迁移到新格式（presets列表）"""
    if 'presets' in profile:
        return profile
    old_remappings = profile.get('remappings', {})
    profile['presets'] = [
        {"name": "预设1", "remappings": old_remappings, "macros": {}, "mouse_bindings": {}}
    ]
    profile.pop('remappings', None)
    return profile


class ProfileManager:
    """游戏配置管理器"""

    def __init__(self, config_file=None):
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.profiles = []
        self.current_profile = None
        self.current_preset_index = 0
        self._load()

    def _load(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.profiles = data.get('profiles', [])
                    saved_current = data.get('current_profile', '')
                    saved_preset = data.get('current_preset_index', 0)
            except Exception as e:
                print(f"加载配置失败: {e}")
                self.profiles = []
                saved_current = ''
                saved_preset = 0
        else:
            self.profiles = []
            saved_current = ''
            saved_preset = 0

        # 迁移旧格式 + 确保内置游戏存在
        for i, p in enumerate(self.profiles):
            self.profiles[i] = _migrate_profile(p)
        for builtin in BUILTIN_GAMES:
            if not any(p['name'] == builtin['name'] for p in self.profiles):
                self.profiles.insert(0, _migrate_profile(builtin.copy()))

        # 恢复上次选中的配置和预设
        self.current_preset_index = saved_preset
        if saved_current:
            for p in self.profiles:
                if p['name'] == saved_current:
                    self.current_profile = p
                    self._fix_preset_index()
                    return
        if self.profiles:
            self.current_profile = self.profiles[0]
            self._fix_preset_index()

    def _fix_preset_index(self):
        """确保预设索引有效"""
        if self.current_profile:
            presets = self.current_profile.get('presets', [])
            if not presets:
                self.current_profile['presets'] = [_make_preset()]
                self.current_preset_index = 0
            elif self.current_preset_index >= len(presets):
                self.current_preset_index = 0

    def _save(self):
        """保存配置"""
        try:
            data = {
                'profiles': self.profiles,
                'current_profile': self.current_profile['name'] if self.current_profile else '',
                'current_preset_index': self.current_preset_index
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    # ── 游戏管理 ──────────────────────────────────────────────────

    def get_profiles(self):
        return self.profiles.copy()

    def get_profile(self, name):
        for profile in self.profiles:
            if profile['name'] == name:
                return profile
        return None

    def add_profile(self, name, description=""):
        if any(p['name'] == name for p in self.profiles):
            return False
        profile = {
            'name': name,
            'description': description,
            'presets': [_make_preset("预设1"), _make_preset("预设2"), _make_preset("预设3")],
            'is_builtin': False
        }
        self.profiles.append(profile)
        self._save()
        return True

    def delete_profile(self, name):
        for i, profile in enumerate(self.profiles):
            if profile['name'] == name:
                if profile.get('is_builtin'):
                    return False
                del self.profiles[i]
                if self.current_profile and self.current_profile['name'] == name:
                    self.current_profile = self.profiles[0] if self.profiles else None
                    self.current_preset_index = 0
                self._save()
                return True
        return False

    def set_current_profile(self, name):
        for profile in self.profiles:
            if profile['name'] == name:
                self.current_profile = profile
                self.current_preset_index = 0
                self._fix_preset_index()
                self._save()
                return True
        return False

    def get_current_profile(self):
        return self.current_profile

    def save_current_profile(self):
        self._save()

    # ── 预设管理 ──────────────────────────────────────────────────

    def get_presets(self):
        if not self.current_profile:
            return []
        return self.current_profile.get('presets', [])

    def get_current_preset(self):
        presets = self.get_presets()
        if 0 <= self.current_preset_index < len(presets):
            return presets[self.current_preset_index]
        return None

    def set_current_preset(self, index):
        presets = self.get_presets()
        if 0 <= index < len(presets):
            self.current_preset_index = index
            self._save()
            return True
        return False

    def add_preset(self, name=None):
        presets = self.get_presets()
        if name is None:
            name = f"预设{len(presets) + 1}"
        presets.append(_make_preset(name))
        self.current_preset_index = len(presets) - 1
        self._save()
        return len(presets) - 1

    def delete_preset(self, index):
        presets = self.get_presets()
        if len(presets) <= 1:
            return False
        if 0 <= index < len(presets):
            del presets[index]
            if self.current_preset_index >= len(presets):
                self.current_preset_index = len(presets) - 1
            self._save()
            return True
        return False

    def rename_preset(self, index, new_name):
        presets = self.get_presets()
        if 0 <= index < len(presets):
            presets[index]['name'] = new_name
            self._save()
            return True
        return False

    # ── 映射/宏/鼠标绑定 读写 ────────────────────────────────────

    def get_remappings(self):
        preset = self.get_current_preset()
        return dict(preset.get('remappings', {})) if preset else {}

    def set_remappings(self, remappings):
        preset = self.get_current_preset()
        if preset:
            preset['remappings'] = {str(k): v for k, v in remappings.items()}
            self._save()

    def get_macros(self):
        preset = self.get_current_preset()
        return dict(preset.get('macros', {})) if preset else {}

    def set_macros(self, macros):
        preset = self.get_current_preset()
        if preset:
            preset['macros'] = macros
            self._save()

    def get_mouse_macro(self):
        preset = self.get_current_preset()
        return dict(preset.get('mouse_macro', {})) if preset else {}

    def set_mouse_macro(self, mouse_macro):
        preset = self.get_current_preset()
        if preset:
            preset['mouse_macro'] = mouse_macro
            self._save()

    def get_mouse_bindings(self):
        preset = self.get_current_preset()
        return dict(preset.get('mouse_bindings', {})) if preset else {}

    def set_mouse_bindings(self, bindings):
        preset = self.get_current_preset()
        if preset:
            preset['mouse_bindings'] = {str(k): v for k, v in bindings.items()}
            self._save()

    # ── 导入导出 ──────────────────────────────────────────────────

    def export_preset(self, index=None):
        """导出预设为字符串"""
        presets = self.get_presets()
        idx = index if index is not None else self.current_preset_index
        if 0 <= idx < len(presets):
            data = json.dumps(presets[idx], ensure_ascii=False)
            return base64.b64encode(data.encode('utf-8')).decode('ascii')
        return ""

    def import_preset(self, code):
        """从字符串导入预设，返回预设对象或None"""
        try:
            data = base64.b64decode(code.encode('ascii')).decode('utf-8')
            preset = json.loads(data)
            if 'name' in preset and 'remappings' in preset:
                preset.setdefault('macros', {})
                preset.setdefault('mouse_bindings', {})
                return preset
        except Exception:
            pass
        return None
