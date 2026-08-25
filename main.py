# main.py (界面层)
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView  # 使用 ModalView 彻底摆脱色块
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.config import Config
from sudoku_core import SudokuGame
import os
import sys

# 界面设置
Config.set('graphics', 'width', '420')
Config.set('graphics', 'height', '680')
Config.set('graphics', 'resizable', '1')
Window.clearcolor = (0.96, 0.94, 0.88, 1)

# iOS 平台不存在 SimHei,改用随包打包的中文字体
if 'ios' in sys.platform:
    COMMON_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chinese.ttf')
else:
    COMMON_FONT = 'SimHei'

# 高亮颜色配置
HIGHLIGHT_CELL_COLOR = (0.85, 0.92, 0.80, 1)     # 联动/十字高亮浅绿
HIGHLIGHT_SELECTED_COLOR = (0.70, 0.82, 0.65, 1) # 当前选中格子深绿

class SudokuCell(Button):
    def __init__(self, row, col, block_bg=(1,1,1,1), **kwargs):
        super().__init__(**kwargs)
        self.row, self.col = row, col
        self.is_original = False
        self.is_error = False
        self.background_normal = ''
        self.font_size = 28
        self.bold = True
        self.font_name = COMMON_FONT
        
        self.block_bg = block_bg
        self.normal_background_color = block_bg
        self.normal_text_color = (0.2, 0.3, 0.5, 1)
        self._update_appearance()
    
    def _update_appearance(self):
        self.normal_background_color = self.block_bg
        self.background_color = self.normal_background_color
        
        if self.is_original:
            self.normal_text_color = (0.15, 0.1, 0.05, 1)
        else:
            self.normal_text_color = (0.2, 0.3, 0.5, 1)
        self.color = self.normal_text_color

    def reset_highlight(self):
        if self.is_error:
            self.background_color = (0.9, 0.6, 0.6, 1)
        else:
            self.background_color = self.normal_background_color


class TypewriterButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.35, 0.33, 0.3, 1)
        self.color = (0.95, 0.93, 0.87, 1)
        self.font_size = 24
        self.bold = True
        self.font_name = COMMON_FONT


class VintageButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.85, 0.82, 0.75, 1)
        self.color = (0.2, 0.15, 0.1, 1)
        self.font_size = kwargs.get('font_size', 16)
        self.bold = True
        self.font_name = COMMON_FONT


class SudokuApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = SudokuGame('easy')
        self.cells = {}
        self.selected_cell = None
        self.game_locked = False
        
        # 🛠️ 隐藏调试模式：绑定键盘监听
        Window.bind(on_keyboard=self.on_keyboard)
    
    def build(self):
        self.title = '复古数独'
        self.main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        with self.main_layout.canvas.before:
            Color(0.96, 0.94, 0.88, 1)
            self.bg_rect = Rectangle(pos=self.main_layout.pos, size=self.main_layout.size)
        self.main_layout.bind(pos=self._update_bg, size=self._update_bg)
        
        title = Label(text='数 独', font_size=32, bold=True, color=(0.2, 0.15, 0.1, 1), size_hint=(1, 0.1), font_name=COMMON_FONT)
        self.main_layout.add_widget(title)
        
        grid_container = BoxLayout(orientation='vertical', size_hint=(1, 0.55), padding=10)
        with grid_container.canvas.before:
            Color(0.9, 0.88, 0.82, 1)
            Rectangle(pos=grid_container.pos, size=grid_container.size)
        
        self.grid_layout = GridLayout(cols=9, spacing=2, padding=5)
        self.create_grid()
        grid_container.add_widget(self.grid_layout)
        
        self.main_layout.add_widget(grid_container)
        
        keyboard_layout = BoxLayout(orientation='horizontal', spacing=8, padding=(10, 5), size_hint=(1, 0.12))
        for num in range(1, 10):
            btn = TypewriterButton(text=str(num))
            btn.number = num
            btn.bind(on_release=self.number_pressed)
            keyboard_layout.add_widget(btn)
        self.main_layout.add_widget(keyboard_layout)
        
        control_layout = BoxLayout(orientation='horizontal', spacing=10, padding=(10, 5), size_hint=(1, 0.1))
        erase_btn = VintageButton(text='擦 除', on_release=self.erase_cell)
        control_layout.add_widget(erase_btn)
        
        self.difficulty_btn = VintageButton(text='难度: 简单', on_release=self.show_difficulty_menu)
        control_layout.add_widget(self.difficulty_btn)
        
        new_game_btn = VintageButton(text='新游戏', on_release=self.new_game)
        control_layout.add_widget(new_game_btn)
        
        self.main_layout.add_widget(control_layout)
        return self.main_layout
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def reset_highlights(self):
        for cell in self.cells.values():
            cell.reset_highlight()

    def highlight_matching_numbers(self, num):
        for cell in self.cells.values():
            if cell.text == str(num) and cell.text != "":
                cell.background_color = HIGHLIGHT_CELL_COLOR

    def create_grid(self):
        self.grid_layout.clear_widgets(); self.cells.clear()
        for i in range(9):
            for j in range(9):
                bg_color = (1.0, 1.0, 1.0, 1)
                # 定义九宫格底色
                if 0 <= i <= 2 and 3 <= j <= 5:
                    bg_color = (0.94, 0.92, 0.88, 1)
                elif 3 <= i <= 5 and (0 <= j <= 2 or 6 <= j <= 8):
                    bg_color = (0.94, 0.92, 0.88, 1)
                elif 6 <= i <= 8 and 3 <= j <= 5:
                    bg_color = (0.94, 0.92, 0.88, 1)
                
                cell = SudokuCell(row=i, col=j, block_bg=bg_color)
                if self.game.original_puzzle[i][j] != 0:
                    cell.text = str(self.game.original_puzzle[i][j])
                    cell.is_original = True
                
                cell._update_appearance()
                cell.bind(on_release=self.cell_pressed)
                self.grid_layout.add_widget(cell)
                self.cells[(i, j)] = cell
    
    def cell_pressed(self, instance):
        if self.game_locked: return
        
        if self.selected_cell == instance:
            self.selected_cell = None
            self.reset_highlights()
            return

        self.reset_highlights()
        
        row, col = instance.row, instance.col
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for (r, c), cell in self.cells.items():
            if (r == row) or (c == col) or (start_row <= r < start_row+3 and start_col <= c < start_col+3):
                cell.background_color = HIGHLIGHT_CELL_COLOR

        instance.background_color = HIGHLIGHT_SELECTED_COLOR
        self.selected_cell = instance
    
    def number_pressed(self, instance):
        if self.game_locked: return
        
        num = instance.number
        
        self.reset_highlights()
        self.highlight_matching_numbers(num)
        
        if not self.selected_cell or self.selected_cell.is_original:
            if self.game.check_win(): 
                self.game_locked = True
                Clock.schedule_once(lambda dt: self.show_win_message(), 0.5)
            return
            
        self.selected_cell.background_color = HIGHLIGHT_SELECTED_COLOR
        
        row, col = self.selected_cell.row, self.selected_cell.col
        
        if self.selected_cell.text == str(num):
            self.selected_cell.text = ''; self.game.board[row][col] = 0
            self.selected_cell.is_error = False
            self.selected_cell._update_appearance()
            return
        
        if self.game.is_valid_move(row, col, num):
            self.selected_cell.is_error = False
            self.selected_cell.text = str(num); self.game.board[row][col] = num
            self.selected_cell._update_appearance()
            
            self.reset_highlights()
            self.highlight_matching_numbers(num)
            self.selected_cell.background_color = HIGHLIGHT_SELECTED_COLOR
            
            if self.game.check_win(): 
                self.game_locked = True
                Clock.schedule_once(lambda dt: self.show_win_message(), 0.5)
        else:
            self.selected_cell.is_error = True
            self.selected_cell.text = str(num)
            self.game.board[row][col] = num
            self.selected_cell.background_color = (0.9, 0.6, 0.6, 1)
    
    def erase_cell(self, instance):
        if self.game_locked: return
        if not self.selected_cell or self.selected_cell.is_original: return
        self.selected_cell.text = ''; self.game.board[self.selected_cell.row][self.selected_cell.col] = 0
        self.selected_cell.is_error = False
        self.selected_cell._update_appearance()
        self.selected_cell = None
        self.reset_highlights()
    
    def show_difficulty_menu(self, instance):
        dropdown = DropDown()
        for diff, name in [('easy','简单'), ('medium','中等'), ('hard','困难')]:
            btn = VintageButton(text=name, size_hint_y=None, height=44, font_size=16)
            btn.bind(on_release=lambda btn, d=diff, n=name: self.change_difficulty(d, n, dropdown))
            dropdown.add_widget(btn)
        dropdown.open(instance)
    
    def change_difficulty(self, difficulty, display_name, dropdown):
        self.difficulty_btn.text = f'难度: {display_name}'; dropdown.dismiss()
        self.game_locked = False
        self.game = SudokuGame(difficulty); self.selected_cell = None; self.create_grid()
    
    def new_game(self, instance):
        self.game_locked = False
        self.game = SudokuGame(self.game.difficulty); self.selected_cell = None; self.create_grid()
    
    # ==========================================
    # ✅ 隐藏功能：一键通关（按 F12 触发）
    # ==========================================
    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        # 监控键盘事件，F12 的键码是 293
        if key == 293:
            self.debug_complete_game()
            return True
        return False

    def debug_complete_game(self):
        if self.game_locked: return # 如果已经通关则跳过
        self.game_locked = True
        
        # 瞬间把正确答案填满所有格子
        for i in range(9):
            for j in range(9):
                cell = self.cells.get((i, j))
                if cell and not cell.is_original:
                    num = self.game.solution[i][j]
                    cell.text = str(num)
                    cell.is_error = False # 清除任何错误标记
                    self.game.board[i][j] = num
                    cell._update_appearance()
        
        self.reset_highlights()
        self.selected_cell = None
        Clock.schedule_once(lambda dt: self.show_win_message(), 0.2)

    # ==========================================
    # ✅ 使用 ModalView 消除残留色块
    # ==========================================
    def show_win_message(self):
        content = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        with content.canvas.before:
            Color(0.96, 0.94, 0.88, 1)
            self.win_bg_rect = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_win_bg, size=self._update_win_bg)
        
        content.add_widget(Label(text='完成！', font_size=32, bold=True, color=(0.2, 0.15, 0.1, 1), font_name=COMMON_FONT))
        content.add_widget(Label(text='你成功解出了数独！', font_size=18, color=(0.3, 0.2, 0.1, 1), font_name=COMMON_FONT))
        
        close_btn = VintageButton(text='继续', size_hint=(0.5, None), height=50, pos_hint={'center_x': 0.5})
        content.add_widget(close_btn)
        
        modal = ModalView(size_hint=(0.7, 0.4), background_color=(0, 0, 0, 0.4)) 
        modal.add_widget(content)
        close_btn.bind(on_release=modal.dismiss)
        modal.open()
        
    def _update_win_bg(self, instance, value):
        self.win_bg_rect.pos = instance.pos
        self.win_bg_rect.size = instance.size

if __name__ == '__main__':
    try: SudokuApp().run()
    except Exception as e: print(f"程序出错: {e}"); input("按回车键退出...")