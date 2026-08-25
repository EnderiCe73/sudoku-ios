# sudoku_core.py
import random

class SudokuCore:
    """数独核心逻辑（完全独立于界面）"""
    
    @staticmethod
    def generate_solution():
        board = [[0 for _ in range(9)] for _ in range(9)]
        SudokuCore._solve(board)
        return board
    
    @staticmethod
    def _solve(board):
        empty = SudokuCore._find_empty(board)
        if not empty: return True
        row, col = empty
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        for num in numbers:
            if SudokuCore._is_valid(board, row, col, num):
                board[row][col] = num
                if SudokuCore._solve(board): return True
                board[row][col] = 0
        return False
    
    @staticmethod
    def _find_empty(board):
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0: return (i, j)
        return None
    
    @staticmethod
    def _is_valid(board, row, col, num):
        for j in range(9):
            if board[row][j] == num: return False
        for i in range(9):
            if board[i][col] == num: return False
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if board[i][j] == num: return False
        return True
    
    @staticmethod
    def generate_puzzle(difficulty='easy'):
        solution = SudokuCore.generate_solution()
        puzzle = [row[:] for row in solution]
        cells_to_remove = {'easy': 38, 'medium': 48, 'hard': 56}.get(difficulty, 38)
        positions = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(positions)
        for i, j in positions[:cells_to_remove]:
            puzzle[i][j] = 0
        return puzzle, solution

class SudokuGame:
    """游戏状态管理"""
    def __init__(self, difficulty='easy'):
        self.difficulty = difficulty
        self.puzzle, self.solution = SudokuCore.generate_puzzle(difficulty)
        self.board = [row[:] for row in self.puzzle]
        self.original_puzzle = [row[:] for row in self.puzzle]
    
    def is_valid_move(self, row, col, num):
        original = self.board[row][col]
        self.board[row][col] = 0
        valid = SudokuCore._is_valid(self.board, row, col, num)
        self.board[row][col] = original
        return valid
    
    def check_win(self):
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0 or self.board[i][j] != self.solution[i][j]:
                    return False
        return True