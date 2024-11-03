import chess.pgn
import json
import sys
from collections import Counter

# Explore up top move 15.
MAX_MOVES = 15;

# Keep positions that occur in at least 0.01% of games.
THRESHOLD_N = 10000;

def trimmed_fen(fen: str) -> str:
    return ' '.join(fen.split(' ')[0:4])

positions = Counter()

n = 0
add_new_positions = True
while True:
    game = chess.pgn.read_game(sys.stdin)
    if not game:
        break

    n += 1
    board = game.board()
    fen = trimmed_fen(board.fen())
    positions[fen] += 1
    for move in game.mainline_moves():
        board.push(move)
        fen = trimmed_fen(board.fen())
        if add_new_positions or fen in positions:
            positions[fen] += 1
        if board.fullmove_number > MAX_MOVES:
            break

    if n % 10000 == 0:
        n_above = sum(c >= n // THRESHOLD_N for c in positions.values())
        sys.stderr.write(f"read {n} games, found {len(positions)} unique positions ({n_above} above threshold)...\n")

    # If a position has never occurred in the first 100 * THRESHOLD_N games,
    # we assume it will not reach the threshold. From now on, we count only
    # previously seen positions.
    if n == (100 * THRESHOLD_N):
        add_new_positions = False

final_threshold = n // THRESHOLD_N
for fen, count in positions.most_common():
    if count < final_threshold:
        break
    sys.stdout.write(f"{fen}\t{count}\n")
