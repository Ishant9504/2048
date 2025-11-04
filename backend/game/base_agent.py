class BaseAgent:
    """All AI agents must implement get_move(board)"""
    def get_move_sequence(self, game_instance, num_moves, params = {}, token = None):
        raise NotImplementedError