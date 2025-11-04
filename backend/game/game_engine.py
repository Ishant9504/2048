import random
import copy

class Game2048:
    def __init__(self):
        self.board = [[0]*4 for _ in range(4)]
        self.score = 0
        self.over = False
        self.ai_assisted = False
        self.add_random_tile()
        self.add_random_tile()
        self.last_move = None

    def add_random_tile(self):
        empty = [(r,c) for r in range(4) for c in range(4) if self.board[r][c]==0]
        if not empty:
            return
    
        r,c = random.choice(empty)
        # 90% chance of 2, 10% chance of 4
        self.board[r][c] = random.choices([2,4],[0.9, 0.1])[0]

    def compress(self, row):
        """Removes zeros by moving non-zero tiles to the left."""
        new_row = [i for i in row if i!=0]
        new_row += [0]*(4- len(new_row))
        return new_row
    
    def merge(self, row):
        """Merges tiles in a compressed row (leftward). Returns the merged row and a flag if a merge occurred."""
        merged = False
        for i in range(3):
            if row[i] == row[i+1] and row[i] != 0:
                row[i] *= 2
                self.score += row[i]
                row[i+1] = 0  # CRITICAL: Set the merged tile to 0
                merged = True
        return row, merged
    
    def move_left(self):
        """Performs one full move-left operation (compress, merge, compress)."""
        moved = False
        new_board = []
        
        for r in range(4):
            original_row = list(self.board[r])
            
            # 1. Compress (Move all non-zero tiles to the left)
            compressed_row = self.compress(original_row)
            
            # 2. Merge (Merge tiles)
            merged_row, merge_occurred = self.merge(compressed_row)
            
            # 3. Compress again (Move the newly created zeros from merging to the right)
            final_row = self.compress(merged_row)
            
            # Check if any change occurred (either compression or merging)
            if final_row != original_row:  # Compare with original_row, not self.board[r]
                moved = True
                
            new_board.append(final_row)
            
        self.board = new_board
        
        # Add a new tile if the board changed
        # if moved:
        #     self.add_random_tile()
        #     print("Added random tile after move")
            
        return moved


    def move(self, direction):
        moved = False
        
        # Keep a copy of the board before the move to check if any change occurred
        board_before_move = [list(row) for row in self.board]

        if direction == 'up':
            # Transpose (rotate 90 degrees counter-clockwise)
            self.board = [list(row) for row in zip(*self.board)] 
            
            # Move Left (which is now Up in the original orientation)
            moved = self.move_left() 
            
            # Transpose back (rotate 90 degrees clockwise)
            self.board = [list(row) for row in zip(*self.board)]

        elif direction == 'down':
            # Transpose (turn rows into columns)
            self.board = [list(row) for row in zip(*self.board)] 
            # Reverse each row (to make 'left' act like 'right' on the columns)
            self.board = [row[::-1] for row in self.board]
            
            # Move Left (which is now Down in the original orientation)
            moved = self.move_left() 

            # Reverse each row back
            self.board = [row[::-1] for row in self.board]
            # Transpose back
            self.board = [list(row) for row in zip(*self.board)]

        elif direction == 'right':
            # Reverse each row
            self.board = [row[::-1] for row in self.board]
            
            # Move Left (which is now Right in the original orientation)
            moved = self.move_left()
            
            # Reverse each row back
            self.board = [row[::-1] for row in self.board]
            
        elif direction == 'left': 
            moved = self.move_left()
            
        # The move_left method will add a tile if it moved
        # We don't need additional logic here as each direction calls move_left
        # which handles adding the random tile internally
        
        # Update the game over status
        self.over = self.is_game_over()
        
        # For debugging
        if moved:
            self.add_random_tile()
            print(f"Move {direction} was valid, new score: {self.score}")
            self.last_move = direction
        else:
            print(f"Move {direction} was invalid")
            self.last_move = None
            
        # Return whether the move was valid

        self.over = self.is_game_over()
        return moved


    def is_game_over(self):
        # 1. Check for empty spots
        for r in range(4):
            for c in range(4):
                if self.board[r][c] == 0:
                    return False
        
        # 2. Check for possible horizontal merges
        for r in range(4):
            for c in range(3):
                if self.board[r][c] == self.board[r][c+1]:
                    return False
                    
        # 3. Check for possible vertical merges
        for r in range(3):
            for c in range(4):
                if self.board[r][c] == self.board[r+1][c]:
                    return False
                    
        return True
    
    def get_state(self):
        return {
            'board':self.board,
            'score':self.score,
            'over':self.over
        }
    
    def clone(self):
        # Creates a deep copy of the current game instance
        return copy.deepcopy(self)
    
    def get_empty_cells(self):
        # Returns a list of (row, col) tuples for all empty cells.
        return [(r, c) for r in range(4) for c in range(4) if self.board[r][c] == 0]
    
    def simulate_move(self, direction):
        """
        Performs a move and updates the board, BUT DOES NOT add a random tile.
        This is for AI simulation purposes only. Returns True if the board changed.
        """
        board_before_move = [list(row) for row in self.board]

        # This reuses the same core logic as the main `move` method
        # but omits the `add_random_tile()` step.
        if direction == 'up':
            self.board = [list(row) for row in zip(*self.board)] 
            self.move_left() 
            self.board = [list(row) for row in zip(*self.board)]
        elif direction == 'down':
            self.board = [list(row) for row in zip(*self.board)] 
            self.board = [row[::-1] for row in self.board]
            self.move_left() 
            self.board = [row[::-1] for row in self.board]
            self.board = [list(row) for row in zip(*self.board)]
        elif direction == 'right':
            self.board = [row[::-1] for row in self.board]
            self.move_left()
            self.board = [row[::-1] for row in self.board]
        elif direction == 'left': 
            self.move_left()
        
        moved = self.board != board_before_move
        if moved:
            self.over = self.is_game_over()
        
        return moved