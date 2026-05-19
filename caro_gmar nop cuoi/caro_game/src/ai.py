import math
from src.board import BOARD_SIZE, WIN_LENGTH, EMPTY, PLAYER, AI

ALGO_MINIMAX = "minimax"
ALGO_ALPHABETA = "alphabeta"


class AIPlayer:
    def __init__(self, depth=2, algo=ALGO_ALPHABETA):
        self.depth = depth
        self.algo = algo          # ALGO_MINIMAX hoặc ALGO_ALPHABETA
        self.nodes_evaluated = 0

    def set_depth(self, depth):
        self.depth = depth

    def set_algo(self, algo):
        self.algo = algo

    def get_best_move(self, board):
        self.nodes_evaluated = 0
        best_score = -math.inf
        best_move = None

        grid_copy = [row[:] for row in board.grid]
        candidates = board.get_candidates()

        for (r, c) in candidates:
            grid_copy[r][c] = AI
            if self.algo == ALGO_ALPHABETA:
                score = self._minimax_ab(grid_copy, self.depth - 1, -math.inf, math.inf, False, r, c, AI)
            else:
                score = self._minimax(grid_copy, self.depth - 1, False, r, c, AI)
            grid_copy[r][c] = EMPTY
            if score > best_score:
                best_score = score
                best_move = (r, c)

        return best_move

    # ── Minimax thuần (không cắt tỉa) ──────────────────────────
    def _minimax(self, grid, depth, is_max, last_r, last_c, last_p):
        self.nodes_evaluated += 1

        if last_r is not None and self._check_win(grid, last_r, last_c, last_p):
            return (-100000 - depth) if is_max else (100000 + depth)

        if depth == 0:
            return self._evaluate(grid)

        moves = self._get_candidates(grid)
        if not moves:
            return 0

        if is_max:
            best = -math.inf
            for (r, c) in moves:
                grid[r][c] = AI
                val = self._minimax(grid, depth - 1, False, r, c, AI)
                grid[r][c] = EMPTY
                best = max(best, val)
            return best
        else:
            best = math.inf
            for (r, c) in moves:
                grid[r][c] = PLAYER
                val = self._minimax(grid, depth - 1, True, r, c, PLAYER)
                grid[r][c] = EMPTY
                best = min(best, val)
            return best

    # ── Minimax + Alpha-Beta Pruning ────────────────────────────
    def _minimax_ab(self, grid, depth, alpha, beta, is_max, last_r, last_c, last_p):
        self.nodes_evaluated += 1

        if last_r is not None and self._check_win(grid, last_r, last_c, last_p):
            return (-100000 - depth) if is_max else (100000 + depth)

        if depth == 0:
            return self._evaluate(grid)

        moves = self._get_candidates(grid)
        if not moves:
            return 0

        if is_max:
            best = -math.inf
            for (r, c) in moves:
                grid[r][c] = AI
                val = self._minimax_ab(grid, depth - 1, alpha, beta, False, r, c, AI)
                grid[r][c] = EMPTY
                best = max(best, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break   # Beta cut-off
            return best
        else:
            best = math.inf
            for (r, c) in moves:
                grid[r][c] = PLAYER
                val = self._minimax_ab(grid, depth - 1, alpha, beta, True, r, c, PLAYER)
                grid[r][c] = EMPTY
                best = min(best, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break   # Alpha cut-off
            return best

    # ── Helpers ────────────────────────────────────────────────
    def _check_win(self, grid, row, col, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            for sign in (1, -1):
                for i in range(1, WIN_LENGTH):
                    r, c = row + dr * i * sign, col + dc * i * sign
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and grid[r][c] == player:
                        count += 1
                    else:
                        break
            if count >= WIN_LENGTH:
                return True
        return False

    def _get_candidates(self, grid, radius=2):
        candidates = set()
        has_piece = False
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if grid[r][c] != EMPTY:
                    has_piece = True
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and grid[nr][nc] == EMPTY:
                                candidates.add((nr, nc))
        if not has_piece:
            candidates.add((BOARD_SIZE // 2, BOARD_SIZE // 2))
        return list(candidates)

    def _evaluate(self, grid):
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                for dr, dc in directions:
                    score += self._line_score(grid, r, c, dr, dc, AI)
                    score -= self._line_score(grid, r, c, dr, dc, PLAYER)
        return score

    def _line_score(self, grid, r, c, dr, dc, player):
        count, open_ends = 0, 0
        for i in range(WIN_LENGTH):
            nr, nc = r + dr * i, c + dc * i
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                return 0
            if grid[nr][nc] == player:
                count += 1
            elif grid[nr][nc] == EMPTY:
                open_ends += 1
            else:
                return 0
        if count == 0:
            return 0
        if count == WIN_LENGTH:
            return 100000
        if count == WIN_LENGTH - 1 and open_ends == 1:
            return 1000
        if count == WIN_LENGTH - 2 and open_ends == 2:
            return 100
        if count == WIN_LENGTH - 3 and open_ends == 3:
            return 10
        return count
