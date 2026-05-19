BOARD_SIZE = 9
WIN_LENGTH = 4

EMPTY = 0
PLAYER = 1  # X
AI = 2      # O


class Board:
    def __init__(self):
        self.grid = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.move_history = []  # list of (row, col, player)

    def reset(self):
        self.grid = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.move_history = []

    def is_valid(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.grid[row][col] == EMPTY

    def place(self, row, col, player):
        self.grid[row][col] = player
        self.move_history.append((row, col, player))

    def undo(self):
        if self.move_history:
            row, col, _ = self.move_history.pop()
            self.grid[row][col] = EMPTY

    def is_full(self):
        return all(self.grid[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

    def check_win(self, row, col, player):
        """Return list of winning cells if player wins at (row, col), else None."""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            cells = [(row, col)]
            for sign in (1, -1):
                for i in range(1, WIN_LENGTH):
                    r, c = row + dr * i * sign, col + dc * i * sign
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.grid[r][c] == player:
                        cells.append((r, c))
                    else:
                        break
            if len(cells) >= WIN_LENGTH:
                return cells
        return None

    def get_candidates(self, radius=2):
        """Return empty cells near existing pieces."""
        candidates = set()
        has_piece = False
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.grid[r][c] != EMPTY:
                    has_piece = True
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.grid[nr][nc] == EMPTY:
                                candidates.add((nr, nc))
        if not has_piece:
            candidates.add((BOARD_SIZE // 2, BOARD_SIZE // 2))
        return list(candidates)
