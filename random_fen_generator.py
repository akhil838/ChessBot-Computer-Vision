import chess
import random
from tqdm import trange
def generate_random_fen():
    board = chess.Board()
    moves = random.randint(0, 200)  # Randomize the board with up to 100 moves
    for _ in range(moves):
        if board.is_game_over():
            break
        move = random.choice(list(board.legal_moves))
        board.push(move)

    return board.fen().split()[0]

random_fen = generate_random_fen()
print('Random FEN:', random_fen)

n_fens = 6000
print(f"GENERATING {n_fens} FENS")
random_fens = []
for i in trange(n_fens):
    random_fens.append(generate_random_fen())

file_path = "assets/random_fens.txt"
with open(file_path, "w") as f:
    for line in random_fens:
        f.write(line+'\n')
print("DONE, saved to",file_path)
