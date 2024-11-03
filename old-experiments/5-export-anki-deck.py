import chess
import copy
import csv
import json

def line_to_san(board: chess.Board, line: str) -> str:
    b = copy.deepcopy(board)
    line_san = []
    for m in line.split():
        move = chess.Move.from_uci(m)
        line_san.append(b.san(move))
        b.push(move)
    return ' '.join(line_san)

with open('best_moves.json') as json_data:
    best_moves = json.load(json_data)
    json_data.close()

output_file = open('deck.tsv', 'w')
#output_file.write("id\tfen\tnames\tfreq\tline0\teval0\tline1\teval1\tline2\teval2\tline3\teval3\timage_front\timage_back\n")

for p in best_moves:
    board = chess.Board(p['fen'])

    id = p['id']
    fen = p['fen']
    names = p['names'].replace("\n", "<br>")
    freq = p['freq']
    line = ['', '', '', '']
    cp = ['', '', '', '']
    for i in range(min(len(p['best_lines']), 4)):
        line[i] = line_to_san(board, p['best_lines'][i]['moves'])
        cp[i] = p['best_lines'][i]['cp']

    image_front = f"<img src=\"{id}.svg\">"
    image_back = f"<img src=\"{id}-moves.svg\">"
    output_file.write(f"{id}\t{fen}\t\"{names}\"\t{freq}\t{line[0]}\t{cp[0]}\t{line[1]}\t{cp[1]}\t{line[2]}\t{cp[2]}\t{line[3]}\t{cp[3]}\t{image_front}\t{image_back}\n")

output_file.close()
