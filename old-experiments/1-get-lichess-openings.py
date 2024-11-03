import chess.pgn
import csv
import io
import json
import requests
import sys
import time
from urllib.parse import urlencode

# download the list of openings
url = "https://github.com/someguy/brilliant/blob/master/somefile.txt"

with open('openings.tsv', 'wb') as output_file:
    for x in ['a', 'b', 'c', 'd', 'e']:
        r = requests.get(f"https://github.com/lichess-org/chess-openings/raw/master/{x}.tsv")
        iter_lines = r.iter_lines()
        if x != 'a':
            # skip the headers for files after the first
            next(iter_lines, None)
        for line in iter_lines:
            output_file.write(line + b'\n')
    output_file.close()
    
# Build a set with all positions to analyze (identified by their move sequences).
positions = {''}

with open('openings.tsv') as f:
    reader = csv.DictReader(f, delimiter="\t")

    for row in reader:
        game = chess.pgn.read_game(io.StringIO(row['pgn']))
        if game.end().board().is_game_over():
            continue
        moves = [m for m in game.mainline_moves()]
        for i in range(len(moves)):
            positions.add(','.join([m.uci() for m in moves[0:i+1]]))

print(f"generated list of {len(positions)} positions")

# Retrieve the frequency of each position.
positions_freq = {}
for position in positions:
    while True:
        freq_url = 'https://explorer.lichess.ovh/lichess?{}'
        freq_params = {'variant': 'standard', 'play': position, 'moves': 0, 'topGames': 0, 'recentGames': 0}
        freq_call = freq_url.format(urlencode(freq_params))
        response = requests.get(freq_call)
        if response.status_code == 429:
            print("rate limited")
            time.sleep(120)
            continue
        else:
            break
    if response.status_code != 200:
        print(f"failed to retrieve frequency for {row['name']}: {response.status_code}")
        sys.exit(1)

    data = response.json()
    #print(data)

    board = chess.Board()
    if position:
        for m in position.split(','):
            board.push_uci(m)
        name = data['opening']['name']
    else:
        name = 'Initial position'
    print(f"retrieved position: {name} - {position}")
    
    # Generate the FEN of the position.
    fen = board.fen()

    # Use a simplified fen for detecting duplicates, without the counters
    # In this way transpositions that have different counters are collapsed
    # together.
    fen_without_counters = ' '.join(fen.split(' ')[0:4])
    
    freq = data['white'] + data['draws'] + data['black'];

    if fen_without_counters in positions_freq:
        positions_freq[fen_without_counters].append({'moves': position, 'name': name, 'freq': freq})
    else:
        positions_freq[fen_without_counters] = [{'moves': position, 'name': name, 'freq': freq}]
    time.sleep(2)

with open('positions.json', 'w') as output_file:
    json.dump(positions_freq, output_file, indent = 4)
    output_file.close()

