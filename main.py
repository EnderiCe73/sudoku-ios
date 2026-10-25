"""复古数独 —— Kivy 界面层。

界面只负责渲染与交互，规则与状态全部位于 sudoku_core。
"""

import os

from kivy.config import Config

# Kivy 要求在导入 Window 之前完成图形配置，因此这两步必须在其他 kivy 导入之前。
Config.set("graphics", "width", "420")
Config.set("graphics", "height", "680")
Config.set("graphics", "resizable", "1")

from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.graphics import Color, Rectangle  # noqa: E402
from kivy.uix.boxlayout import BoxLayout  # noqa: E402
from kivy.uix.button import Button  # noqa: E402
from kivy.uix.dropdown import DropDown  # noqa: E402
from kivy.uix.gridlayout import GridLayout  # noqa: E402
from kivy.uix.label import Label  # noqa: E402
from kivy.uix.modalview import ModalView  # noqa: E402

from sudoku_core import SudokuGame  # noqa: E402

# ---------------- 配色 ----------------
BG_COLOR = (0.96, 0.94, 0.88, 1)
GRID_BG_COLOR = (0.90, 0.88, 0.82, 1)
CELL_COLOR = (1.00, 1.00, 1.00, 1)
CELL_COLOR_ALT = (0.94, 0.92, 0.88, 1)
HIGHLIGHT_COLOR = (0.85, 0.92, 0.80, 1)
SELECTED_COLOR = (0.70, 0.82, 0.65, 1)
ERROR_COLOR = (0.90, 0.60, 0.60, 1)
TEXT_GIVEN_COLOR = (0.15, 0.10, 0.05, 1)
TEXT_INPUT_COLOR = (0.20, 0.30, 0.50, 1)
TEXT_LIGHT_COLOR = (0.95, 0.93, 0.87, 1)

KEYPAD_COLOR = (0.35, 0.33, 0.30, 1)
CONTROL_COLOR = (0.85, 0.82, 0.75, 1)
CONTROL_TEXT_COLOR = (0.20, 0.15, 0.10, 1)

# ---------------- 字体 ----------------
# iOS/Android 没有 SimHei，统一使用随包字体；桌面端同样可用。
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chinese.ttf")
COMMON_FONT = FONT_PATH if os.path.exists(FONT_PATH) else "Roboto"

# ---------------- 格子状态 ----------------
STATE_NORMAL = "normal"
STATE_HIGHLIGHT = "highlight"
STATE_SELECTED = "selected"

Window.clearcolor = BG_COLOR


class SudokuCell(Button):
    """单个格子：颜色由 is_error 与 state 唯一决定。"""

    def __init__(self, row, col, value=0, block_bg=CELL_COLOR, **kwargs):
        super().__init__(text=str(value) if value else "", **kwargs)
        self.row = row
        self.col = col
        self.is_original = value != 0
        self.is_error = False
        self.state = STATE_NORMAL
        self.block_bg = block_bg
        self.background_normal = ""
        self.font_size = 28
        self.bold = True
        self.font_name = COMMON_FONT
        self.refresh()

    def refresh(self):
        """按当前状态刷新底色与文字色。"""
        if self.state == STATE_SELECTED:
            self.background_color = SELECTED_COLOR
        elif self.is_error:
            self.background_color = ERROR_COLOR
        elif self.state == STATE_HIGHLIGHT:
            self.background_color = HIGHLIGHT_COLOR
        else:
            self.background_color = self.block_bg
        self.color = TEXT_GIVEN_COLOR if self.is_original else TEXT_INPUT_COLOR

    def set_state(self, state):
        self.state = state
        self.refresh()

    def reset_highlight(self):
        self.set_state(STATE_NORMAL)


class TypewriterButton(Button):
    """数字键盘按键。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = KEYPAD_COLOR
        self.color = TEXT_LIGHT_COLOR
        self.font_size = 24
        self.bold = True
        self.font_name = COMMON_FONT


class VintageButton(Button):
    """功能按钮（擦除 / 难度 / 新游戏 / 继续）。"""

    def __init__(self, **kwargs):
        font_size = kwargs.pop("font_size", 16)
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = CONTROL_COLOR
        self.color = CONTROL_TEXT_COLOR
        self.font_size = font_size
        self.bold = True
        self.font_name = COMMON_FONT


class SudokuApp(App):
    title = "复古数独"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = SudokuGame("easy")
        self.cells = {}
        self.selected_cell = None
        self.game_locked = False
        self._dropdown = None
        self._win_modal = None

    # ---------------- 构建界面 ----------------
    def build(self):
        root = BoxLayout(orientation="vertical", padding=15, spacing=10)
        self._paint_background(root, BG_COLOR)

        root.add_widget(
            Label(
                text="数 独",
                font_size=32,
                bold=True,
                color=TEXT_GIVEN_COLOR,
                size_hint=(1, 0.1),
                font_name=COMMON_FONT,
            )
        )

        grid_container = BoxLayout(
            orientation="vertical", size_hint=(1, 0.55), padding=10
        )
        self._paint_background(grid_container, GRID_BG_COLOR)
        self.grid_layout = GridLayout(cols=9, spacing=2, padding=5)
        self.create_grid()
        grid_container.add_widget(self.grid_layout)
        root.add_widget(grid_container)

        keypad = BoxLayout(
            orientation="horizontal",
            spacing=8,
            padding=(10, 5),
            size_hint=(1, 0.12),
        )
        for num in range(1, 10):
            key = TypewriterButton(text=str(num))
            key.number = num
            key.bind(on_release=self.number_pressed)
            keypad.add_widget(key)
        root.add_widget(keypad)

        controls = BoxLayout(
            orientation="horizontal",
            spacing=10,
            padding=(10, 5),
            size_hint=(1, 0.1),
        )
        controls.add_widget(VintageButton(text="擦 除", on_release=self.erase_cell))
        self.difficulty_btn = VintageButton(
            text="难度: 简单", on_release=self.show_difficulty_menu
        )
        controls.add_widget(self.difficulty_btn)
        controls.add_widget(VintageButton(text="新游戏", on_release=self.new_game))
        root.add_widget(controls)
        return root

    @staticmethod
    def _paint_background(widget, rgba):
        """给容器铺底色，并跟随容器尺寸变化。"""
        with widget.canvas.before:
            Color(*rgba)
            rect = Rectangle(pos=widget.pos, size=widget.size)

        def sync(instance, _value):
            rect.pos = instance.pos
            rect.size = instance.size

        widget.bind(pos=sync, size=sync)

    # ---------------- 棋盘 ----------------
    def create_grid(self):
        self.selected_cell = None
        self.grid_layout.clear_widgets()
        self.cells.clear()
        for row in range(9):
            for col in range(9):
                block_bg = (
                    CELL_COLOR_ALT if (row // 3 + col // 3) % 2 else CELL_COLOR
                )
                cell = SudokuCell(row, col, self.game.puzzle[row][col], block_bg)
                cell.bind(on_release=self.cell_pressed)
                self.cells[(row, col)] = cell
                self.grid_layout.add_widget(cell)

    def reset_highlights(self):
        for cell in self.cells.values():
            cell.reset_highlight()

    def highlight_matching_numbers(self, num):
        text = str(num)
        for cell in self.cells.values():
            if not cell.is_error and cell.text == text:
                cell.set_state(STATE_HIGHLIGHT)

    # ---------------- 交互 ----------------
    def cell_pressed(self, cell):
        if self.game_locked:
            return

        if self.selected_cell is cell:
            self.selected_cell = None
            self.reset_highlights()
            return

        self.reset_highlights()
        row, col = cell.row, cell.col
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for (r, c), other in self.cells.items():
            if other.is_error:
                continue
            in_block = (
                start_row <= r < start_row + 3 and start_col <= c < start_col + 3
            )
            if r == row or c == col or in_block:
                other.set_state(STATE_HIGHLIGHT)

        cell.set_state(STATE_SELECTED)
        self.selected_cell = cell

    def number_pressed(self, button):
        if self.game_locked:
            return
        num = button.number

        self.reset_highlights()
        self.highlight_matching_numbers(num)

        cell = self.selected_cell
        if cell is None or cell.is_original:
            return

        row, col = cell.row, cell.col

        # 再按一次相同数字 = 清除
        if cell.text == str(num):
            self._clear_cell(cell)
            cell.set_state(STATE_SELECTED)
            return

        if self.game.is_valid_move(row, col, num):
            cell.is_error = False
            cell.text = str(num)
            self.game.board[row][col] = num
            self.reset_highlights()
            self.highlight_matching_numbers(num)
            cell.set_state(STATE_SELECTED)
            if self.game.check_win():
                self.game_locked = True
                Clock.schedule_once(lambda _dt: self.show_win_message(), 0.5)
        else:
            # 非法值只作提示，不写入棋盘
            cell.is_error = True
            cell.text = str(num)
            cell.set_state(STATE_NORMAL)

    def _clear_cell(self, cell):
        cell.text = ""
        cell.is_error = False
        self.game.board[cell.row][cell.col] = 0
        cell.set_state(STATE_NORMAL)

    def erase_cell(self, _button):
        if self.game_locked:
            return
        if self.selected_cell is None or self.selected_cell.is_original:
            return
        self._clear_cell(self.selected_cell)
        self.selected_cell = None
        self.reset_highlights()

    # ---------------- 难度与新局 ----------------
    def show_difficulty_menu(self, button):
        if self._dropdown is not None:
            self._dropdown.dismiss()

        dropdown = DropDown()
        for difficulty, name in (
            ("easy", "简单"),
            ("medium", "中等"),
            ("hard", "困难"),
        ):
            item = VintageButton(
                text=name, size_hint_y=None, height=44, font_size=16
            )
            item.bind(
                on_release=lambda _btn, d=difficulty, n=name: self.change_difficulty(
                    d, n, dropdown
                )
            )
            dropdown.add_widget(item)

        self._dropdown = dropdown
        dropdown.open(button)

    def change_difficulty(self, difficulty, display_name, dropdown):
        self.difficulty_btn.text = f"难度: {display_name}"
        dropdown.dismiss()
        self.start_new_game(difficulty)

    def new_game(self, _button):
        self.start_new_game(self.game.difficulty)

    def start_new_game(self, difficulty):
        self.game_locked = False
        self.game = SudokuGame(difficulty)
        self.create_grid()

    # ---------------- 通关提示 ----------------
    def show_win_message(self):
        content = BoxLayout(orientation="vertical", padding=30, spacing=15)
        self._paint_background(content, BG_COLOR)
        content.add_widget(
            Label(
                text="完成！",
                font_size=32,
                bold=True,
                color=TEXT_GIVEN_COLOR,
                font_name=COMMON_FONT,
            )
        )
        content.add_widget(
            Label(
                text="你成功解出了数独！",
                font_size=18,
                color=(0.3, 0.2, 0.1, 1),
                font_name=COMMON_FONT,
            )
        )
        close_btn = VintageButton(
            text="继续",
            size_hint=(0.5, None),
            height=50,
            pos_hint={"center_x": 0.5},
        )
        content.add_widget(close_btn)

        modal = ModalView(size_hint=(0.7, 0.4), background_color=(0, 0, 0, 0.4))
        modal.add_widget(content)
        close_btn.bind(on_release=modal.dismiss)
        modal.bind(on_dismiss=self._forget_win_modal)
        self._win_modal = modal
        modal.open()

    def _forget_win_modal(self, *_args):
        self._win_modal = None


if __name__ == "__main__":
    SudokuApp().run()
