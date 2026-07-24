import random
from game.base_agent import BaseAgent


class RandomAgent(BaseAgent):
    def get_move(self, board):
        directions = ["up", "down", "left", "right"]
        random.shuffle(directions)
        for d in directions:
            if self._would_move(board, d):
                return d
        return "up"

    def _would_move(self, board, direction):
        copy = [row[:] for row in board]

        if direction == "left":
            for r in range(4):
                row = [v for v in copy[r] if v != 0]
                for i in range(len(row) - 1):
                    if row[i] == row[i + 1]:
                        row[i] *= 2
                        row[i + 1] = 0
                row = [v for v in row if v != 0] + [0] * (4 - len([v for v in row if v != 0]))
                if row != copy[r]:
                    return True
            return False

        if direction == "right":
            for r in range(4):
                row = [v for v in copy[r] if v != 0][::-1]
                for i in range(len(row) - 1):
                    if row[i] == row[i + 1]:
                        row[i] *= 2
                        row[i + 1] = 0
                row = [v for v in row if v != 0]
                row = row[::-1] + [0] * (4 - len(row))
                if row != copy[r]:
                    return True
            return False

        if direction == "up":
            for c in range(4):
                col = [copy[r][c] for r in range(4) if copy[r][c] != 0]
                for i in range(len(col) - 1):
                    if col[i] == col[i + 1]:
                        col[i] *= 2
                        col[i + 1] = 0
                col = [v for v in col if v != 0] + [0] * (4 - len([v for v in col if v != 0]))
                for r in range(4):
                    if col[r] != copy[r][c]:
                        return True
            return False

        if direction == "down":
            for c in range(4):
                col = [copy[r][c] for r in range(4) if copy[r][c] != 0][::-1]
                for i in range(len(col) - 1):
                    if col[i] == col[i + 1]:
                        col[i] *= 2
                        col[i + 1] = 0
                col = [v for v in col if v != 0]
                col = col[::-1] + [0] * (4 - len(col))
                for r in range(4):
                    if col[r] != copy[r][c]:
                        return True
            return False

        return False