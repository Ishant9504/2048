from game.base_agent import BaseAgent
import copy
import random
import math
import time

class MCTSNode:
    """A node in the Monte Carlo Tree."""
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = self.get_legal_moves()

    def get_legal_moves(self):
        """Get a list of valid moves from this state."""
        moves = []
        for move in ['up', 'down', 'left', 'right']:
            temp_game = self.state.clone()
            if temp_game.simulate_move(move):
                moves.append(move)
        return moves

    def ucb1(self, exploration_constant):
        """Upper Confidence Bound 1 applied to trees formula."""
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

    def select_child(self, exploration_constant):
        """Select a child node using the UCB1 formula."""
        return max(self.children, key=lambda c: c.ucb1(exploration_constant))

    def add_child(self, move, state):
        """Add a new child node for a move."""
        child = MCTSNode(state=state, parent=self, move=move)
        self.untried_moves.remove(move)
        self.children.append(child)
        return child

    def update(self, result_score):
        """Update this node's visits and wins (score)."""
        self.visits += 1
        self.wins += result_score


class MCTSAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        # Transposition table: board_hash -> (total_score, visit_count)
        self.transposition_table = {}
    
    def get_move_sequence(self, game_instance, num_moves, params={}, token = None):
        temp_game = game_instance.clone()
        move_sequence = []
        
        # Calculate adaptive time budget based on number of moves requested
        total_time_budget = params.get('total_time_budget', None)
        if total_time_budget is None:
            # Default: ensure at least 0.2s per move, with more time for fewer moves
            base_time_per_move = max(0.2, 1.0 - (num_moves / 200))
            total_time_budget = base_time_per_move * num_moves
        
        time_per_move = total_time_budget / num_moves if num_moves > 0 else 1.0

        for move_idx in range(num_moves):

            if temp_game.over:
                break
            
            if token and token.get('cancelled'):
                print("AI task cancelled by token. Stopping sequence generation.")
                break 

            # Adaptive simulation budget: reduce as game progresses
            base_simulations = params.get('simulations', 500)
            decay_rate = params.get('simulation_decay', 0.3)
            progress_ratio = move_idx / max(num_moves, 1)
            adjusted_simulations = max(
                100,  # Minimum simulations
                int(base_simulations * (1 - decay_rate * progress_ratio))
            )
            
            # Update params with adjusted values
            adjusted_params = params.copy()
            adjusted_params['simulations'] = adjusted_simulations
            adjusted_params['time_per_move'] = time_per_move
            
            # Find the best move using MCTS from the current state
            best_move = self.mcts(temp_game, adjusted_params)
            
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
    
    def evaluate_monotonicity(self, board):
        """
        A simple heuristic to reward boards where tiles are in decreasing
        order from left-to-right and top-to-bottom.
        """
        score = 0
        for i in range(4):
            # Row monotonicity
            for j in range(3):
                if board[i][j] >= board[i][j+1]:
                    score += board[i][j]
            # Column monotonicity
            for j in range(3):
                if board[j][i] >= board[j+1][i]:
                    score += board[j][i]
        return score
    
    def mcts(self, game_instance, params):
        """
        The main MCTS loop with optimizations:
        - Time-based cutoff
        - Early playout termination
        - Transposition table caching
        """
        max_simulations = params.get('simulations', 500)
        time_per_move = params.get('time_per_move', 0.5)
        exploration_constant = params.get('C_EXP', 1.5)
        playout_greed = params.get('playout_greed', 0.2)
        monotonicity_focus = params.get('monotonicity_focus', 0.3)
        max_playout_depth = params.get('max_playout_depth', 60)
        use_transposition = params.get('use_transposition', True)

        root = MCTSNode(state=game_instance)
        start_time = time.time()
        simulations_done = 0

        # Run MCTS iterations until time budget or simulation limit
        while simulations_done < max_simulations:
            # Check time budget
            if time.time() - start_time >= time_per_move:
                break
            
            node = root
            
            # 1. Selection: traverse tree using UCB1
            while node.untried_moves == [] and node.children != []:
                node = node.select_child(exploration_constant)

            # 2. Expansion: add a new child node
            if node.untried_moves != []:
                move = random.choice(node.untried_moves)
                new_state = node.state.clone()
                new_state.simulate_move(move)
                new_state.add_random_tile()
                node = node.add_child(move, new_state)

            # 3. Simulation (Playout) with early termination
            playout_result = self.run_playout(
                node.state, 
                playout_greed, 
                monotonicity_focus, 
                max_playout_depth,
                use_transposition
            )

            # 4. Backpropagation
            current = node
            while current is not None:
                current.update(playout_result)
                current = current.parent
            
            simulations_done += 1

        # Choose the most visited child (robust choice)
        if not root.children:
            return None
            
        return max(root.children, key=lambda c: c.visits).move
    
    def run_playout(self, start_state, playout_greed, monotonicity_focus, max_depth, use_transposition):
        """
        Run a single playout from the given state with optimizations:
        - Early termination after max_depth moves
        - Consolidated move evaluation (fix redundant code)
        - Optional transposition table lookup
        """
        playout_state = start_state.clone()
        moves_made = 0
        
        while not playout_state.over and moves_made < max_depth:
            # Check transposition table if enabled
            if use_transposition:
                board_key = self.board_hash(playout_state.board)
                if board_key in self.transposition_table:
                    cached_score, cached_visits = self.transposition_table[board_key]
                    if cached_visits > 5:  # Only use if we have enough data
                        return cached_score / cached_visits
            
            # Evaluate all possible moves once
            possible_moves = []
            move_scores = {}
            
            for m in ['up', 'down', 'left', 'right']:
                m_sim = playout_state.clone()
                if m_sim.simulate_move(m):
                    possible_moves.append(m)
                    # Pre-calculate scores for both greedy and monotonicity
                    move_scores[m] = {
                        'score': m_sim.score,
                        'monotonicity': self.evaluate_monotonicity(m_sim.board)
                    }
            
            if not possible_moves:
                break  # Game over
            
            # Choose move based on strategy
            chosen_move = None
            
            if random.random() < playout_greed:
                # Greedy: choose move with highest immediate score
                chosen_move = max(possible_moves, key=lambda m: move_scores[m]['score'])
            elif random.random() < monotonicity_focus:
                # Monotonicity-focused: choose move with best board structure
                chosen_move = max(possible_moves, key=lambda m: move_scores[m]['monotonicity'])
            else:
                # Random exploration
                chosen_move = random.choice(possible_moves)
            
            playout_state.move(chosen_move)
            moves_made += 1
        
        # Cache the result if transposition table is enabled
        final_score = playout_state.score
        if use_transposition:
            board_key = self.board_hash(playout_state.board)
            if board_key in self.transposition_table:
                old_score, old_visits = self.transposition_table[board_key]
                self.transposition_table[board_key] = (old_score + final_score, old_visits + 1)
            else:
                self.transposition_table[board_key] = (final_score, 1)
        
        return final_score