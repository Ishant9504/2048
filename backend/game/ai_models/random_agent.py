from game.base_agent import BaseAgent
import random

class RandomAgent(BaseAgent):
    def get_move_sequence(self, game_instance, num_moves):

        # Returns a list of dictionaries where each dictionary represents the game state after a move

        temp_game = game_instance.clone()

        move_sequence  = []
        possible_moves = ['up', 'down', 'left', 'right']

        while len(move_sequence) < num_moves and not temp_game.over:

            move_direction = random.choice(possible_moves)
            if temp_game.move(move_direction): # if the random move is valid
                current_state = {
                    'board': temp_game.board,
                    'score': temp_game.score,
                    'over': temp_game.over,
                    'move_made': move_direction 
                }
                move_sequence.append(current_state)
        
        return move_sequence