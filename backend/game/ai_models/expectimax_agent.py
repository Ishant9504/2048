from game.base_agent import BaseAgent
import copy
import random

class ExpectimaxAgent(BaseAgent):
    
    def __init__(self):
        super().__init__()
        self.transposition_table = {}
    
    def get_move_sequence(self, game_instance, num_moves, params={}, token = None):
        """
        Generates a sequence of moves by repeatedly finding the best move
        using the Expectimax algorithm.
        """
        temp_game = game_instance.clone()
        move_sequence = []
        
        # Clear transposition table periodically to avoid memory bloat
        if len(self.transposition_table) > 10000:
            self.transposition_table.clear()

        search_depth = params.get('depth', 2)

        for _ in range(num_moves):
            if temp_game.over:
                break

            if token and token.get('cancelled'):
                print("AI task cancelled by token. Stopping sequence generation.")
                break 

            best_move = self.find_best_move(temp_game, search_depth, params)
            
            if best_move:
                temp_game.move(best_move)
                move_sequence.append({
                    'board': copy.deepcopy(temp_game.board),
                    'score': temp_game.score,
                    'over': temp_game.over,
                    'move_made': best_move
                })
            else:
                break
                
        return move_sequence
    
    def board_hash(self, board):
        """Create a hashable representation of the board for transposition table."""
        return tuple(tuple(row) for row in board)

    def find_best_move(self, game_instance, depth, params):
        """
        Iterates through the 4 possible moves and returns the one
        that yields the highest expectimax score.
        With move ordering optimization.
        """
        # Quick evaluation of each move for ordering
        move_scores = []
        for move in ['up', 'down', 'left', 'right']:
            sim_game = game_instance.clone()
            if sim_game.simulate_move(move):
                # Quick heuristic score for ordering
                quick_score = self.evaluate_board(sim_game.board, params)
                move_scores.append((move, quick_score, sim_game))
        
        if not move_scores:
            return None
        
        # Sort moves by quick evaluation (best first)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        
        best_score = -float('inf')
        best_move = None
        
        # Try moves in order of promise
        for move, _, sim_game in move_scores:
            score = self.expectimax(sim_game, depth - 1, False, params)
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move

    def expectimax(self, game_instance, depth, is_player_turn, params):
        """
        The recursive core of the algorithm with optimizations:
        - Transposition table caching
        - Sampling at CHANCE nodes
        - Adaptive depth
        """
        # Check transposition table first
        use_transposition = params.get('use_transposition', True)
        if use_transposition:
            board_key = self.board_hash(game_instance.board)
            cache_key = (board_key, depth, is_player_turn)
            if cache_key in self.transposition_table:
                return self.transposition_table[cache_key]
        
        # Terminal condition
        if depth == 0 or game_instance.over:
            result = self.evaluate_board(game_instance.board, params)
            return result

        if is_player_turn:
            # --- MAX NODE (Player's Turn) ---
            max_score = -float('inf')
            for move in ['up', 'down', 'left', 'right']:
                sim_game = game_instance.clone()
                if sim_game.simulate_move(move):
                    score = self.expectimax(sim_game, depth - 1, False, params)
                    max_score = max(max_score, score)
            
            # Cache the result
            if use_transposition:
                self.transposition_table[cache_key] = max_score
            
            return max_score
        
        else:
            # --- CHANCE NODE (Computer's Turn) with SAMPLING ---
            empty_cells = game_instance.get_empty_cells()
            num_empty = len(empty_cells)

            if num_empty == 0:
                return -float('inf')

            # OPTIMIZATION: Sample only a subset of empty cells
            sample_size = params.get('sample_size', None)
            adaptive_depth = params.get('adaptive_depth', True)
            
            # Adaptive sampling: sample more when fewer empty cells
            if sample_size is None:
                if num_empty <= 4:
                    sample_size = num_empty  # Try all if few cells
                # elif num_empty <= 8:
                #     sample_size = min(6, num_empty)
                else:
                    sample_size = min(6, num_empty)  # Sample fewer for complex boards
            else:
                sample_size = min(sample_size, num_empty)
            
            # Adaptive depth: reduce depth for complex boards
            next_depth = depth - 1
            if adaptive_depth and num_empty > 8:
                next_depth = max(0, depth - 2)  # Skip a level for complex boards
            
            # Sample random positions instead of trying all
            sampled_cells = random.sample(empty_cells, sample_size) if sample_size < num_empty else empty_cells
            
            total_score = 0
            
            # OPTIMIZATION: Combine 2 and 4 placement in single loop
            for r, c in sampled_cells:
                sim_game = game_instance.clone()
                
                # Try placing a 2 (90% probability)
                sim_game.board[r][c] = 2
                score_2 = self.expectimax(sim_game, next_depth, True, params)
                total_score += 0.9 * score_2
                
                # Try placing a 4 (10% probability) - modify same clone
                sim_game.board[r][c] = 4
                score_4 = self.expectimax(sim_game, next_depth, True, params)
                total_score += 0.1 * score_4

            result = total_score / sample_size
            
            # Cache the result
            if use_transposition:
                self.transposition_table[cache_key] = result
            
            return result

    def evaluate_board(self, board, params):
        """
        Calculates a "goodness" score for a board state using weighted heuristics.
        """
        weight_empty = params.get('NEC', 250)
        weight_smoothness = params.get('SMO', 10)
        weight_corner = params.get('LCC', 500)
        
        # Heuristic 1: Number of Empty Cells
        empty_cells = sum(row.count(0) for row in board)

        # Heuristic 2: Smoothness
        smoothness = 0
        for r in range(4):
            for c in range(4):
                if board[r][c] != 0:
                    val = board[r][c]
                    if c < 3 and board[r][c+1] != 0:
                        smoothness -= abs(val - board[r][c+1])
                    if r < 3 and board[r+1][c] != 0:
                        smoothness -= abs(val - board[r+1][c])
        
        # Heuristic 3: Largest Cell at Corner
        max_tile = max(max(row) for row in board)
        corner_bonus = 0
        if board[0][0] == max_tile:
            corner_bonus = max_tile

        return (
            empty_cells * weight_empty +
            smoothness * weight_smoothness +
            corner_bonus * weight_corner
        )