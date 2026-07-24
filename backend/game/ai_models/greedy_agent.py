from game.base_agent import BaseAgent


class GreedyAgent(BaseAgent):
    def get_move(self, board):
        best_direction = "up"
        best_score = -1

        for d in ["up", "down", "left", "right"]:
            new_board, score_gain, moved = self._simulate(board, d)
            if not moved:
                continue

            heur = self._evaluate(new_board, score_gain)
            if heur > best_score:
                best_score = heur
                best_direction = d

        return best_direction

    def _simulate(self, board, direction):
        copy = [row[:] for row in board]
        score = 0
        moved = False

        if direction == "left":
            for r in range(4):
                row = [v for v in copy[r] if v != 0]
                for i in range(len(row) - 1):
                    if row[i] == row[i + 1]:
                        score += row[i] * 2
                        row[i] *= 2
                        row[i + 1] = 0
                row = [v for v in row if v != 0] + [0] * (4 - len([v for v in row if v != 0]))
                if row != copy[r]:
                    moved = True
                copy[r] = row

        elif direction == "right":
            for r in range(4):
                row = [v for v in copy[r] if v != 0][::-1]
                for i in range(len(row) - 1):
                    if row[i] == row[i + 1]:
                        score += row[i] * 2
                        row[i] *= 2
                        row[i + 1] = 0
                row = [v for v in row if v != 0]
                row = row[::-1] + [0] * (4 - len(row))
                if row != copy[r]:
                    moved = True
                copy[r] = row

        elif direction == "up":
            for c in range(4):
                col = [copy[r][c] for r in range(4) if copy[r][c] != 0]
                for i in range(len(col) - 1):
                    if col[i] == col[i + 1]:
                        score += col[i] * 2
                        col[i] *= 2
                        col[i + 1] = 0
                col = [v for v in col if v != 0] + [0] * (4 - len([v for v in col if v != 0]))
                for r in range(4):
                    if col[r] != copy[r][c]:
                        moved = True
                    copy[r][c] = col[r]

        elif direction == "down":
            for c in range(4):
                col = [copy[r][c] for r in range(4) if copy[r][c] != 0][::-1]
                for i in range(len(col) - 1):
                    if col[i] == col[i + 1]:
                        score += col[i] * 2
                        col[i] *= 2
                        col[i + 1] = 0
                col = [v for v in col if v != 0]
                col = col[::-1] + [0] * (4 - len(col))
                for r in range(4):
                    if col[r] != copy[r][c]:
                        moved = True
                    copy[r][c] = col[r]

        return copy, score, moved

    def _evaluate(self, board, score_gain):
        empty = sum(row.count(0) for row in board)

        mono = self._monotonicity(board)
        smooth = self._smoothness(board)

        max_tile = max(max(row) for row in board)

        return score_gain + empty * 100 + mono * 10 + smooth * 5 + max_tile * 2

    def _monotonicity(self, board):
        total = 0
        for r in range(4):
            for c in range(3):
                if board[r][c] >= board[r][c + 1] and board[r][c + 1] != 0:
                    total += 1
                if board[r][c] <= board[r][c + 1] and board[r][c] != 0:
                    total += 1
        for c in range(4):
            for r in range(3):
                if board[r][c] >= board[r + 1][c] and board[r + 1][c] != 0:
                    total += 1
                if board[r][c] <= board[r + 1][c] and board[r][c] != 0:
                    total += 1
        return total

    def _smoothness(self, board):
        total = 0
        for r in range(4):
            for c in range(3):
                if board[r][c] and board[r][c + 1]:
                    total += 10 - abs(board[r][c] - board[r][c + 1]).bit_length()
        for c in range(4):
            for r in range(3):
                if board[r][c] and board[r + 1][c]:
                    total += 10 - abs(board[r][c] - board[r + 1][c]).bit_length()
        return total