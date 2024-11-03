import chess.pgn
import io
import requests
import sys

def trimmed_fen(fen: str) -> str:
    return ' '.join(fen.split(' ')[0:4])

# Download the list of openings.
for x in ['a', 'b', 'c', 'd', 'e']:
    r = requests.get(f"https://github.com/lichess-org/chess-openings/raw/master/{x}.tsv")
    iter_lines = r.iter_lines()
    # Skip the headers
    next(iter_lines, None)
    for line in iter_lines:
        eco, name, pgn = line.split(b'\t')
        game = chess.pgn.read_game(io.StringIO(pgn.decode('UTF-8')))
        fen = trimmed_fen(game.end().board().fen())
        name = name.decode('UTF-8')
        sys.stdout.write(f"{fen}\t{name}\n")
