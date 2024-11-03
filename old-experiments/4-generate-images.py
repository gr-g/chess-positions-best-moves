import chess.svg
import json

IMAGE_SIZE = 300 # image size in pixel
ARROW_COLOR = '#15781B'

with open('best_moves.json') as json_data:
    best_moves = json.load(json_data)
    json_data.close()

for p in best_moves:
    board = chess.Board(p['fen'])

    # select the best moves to keep
    best_cp_loss = p['best_lines'][0]['cp']
    best_moves = [chess.Move.from_uci(line['moves'].split()[0]) for line in p['best_lines'][0:4]]
    cp_loss = [abs(line['cp']-best_cp_loss) for line in p['best_lines'][0:4]]

    # check en_passant
    en_passant = p['fen'].split(' ')[3]
    if en_passant != '-':
        square = chess.parse_square(en_passant)
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        lastmove = chess.Move(chess.square(file, rank+1), chess.square(file, rank-1))
    else:
        lastmove = None

    # generate normal image
    image1 = chess.svg.board(board, orientation = board.turn, lastmove = lastmove, size = IMAGE_SIZE)

    with open(f"images/{p['id']}.svg", 'w') as output_file:
        output_file.write(image1)
        output_file.close()
    
    # generate image with arrows
    arrows = []
    for i in range(len(best_moves)):
        move = best_moves[i]
        opacity = 200 - cp_loss[i]*4
        color = ARROW_COLOR + hex(opacity)[2:]
        arrows.append(chess.svg.Arrow(move.from_square, move.to_square, color = color))

    image2 = chess.svg.board(board, orientation = board.turn, arrows = arrows, lastmove = lastmove, size = IMAGE_SIZE)

    with open(f"images/{p['id']}-moves.svg", 'w') as output_file:
        output_file.write(image2)
        output_file.close()

