import chess
import chess.svg
import json
import os

# Maximum number of moves to show.
MAX_MOVES = 20

# Image size in pixels
IMAGE_SIZE = 300

# Color of the arrows in the images
ARROW_COLOR = '#15781B'

def generate_images(positions_moves, output_dirname):
    if not os.path.exists(output_dirname):
        os.makedirs(output_dirname)

    for p in positions_moves:
        board = chess.Board(p['fen'])

        # Look at the best moves.
        best_evaluation = p['best_moves'][0]['evaluation']
        moves = [board.parse_san(m['move']) for m in p['best_moves']]
        cp_loss = [abs(m['evaluation']-best_evaluation) for m in p['best_moves']]

        # Check en passant.
        en_passant = p['fen'].split(' ')[3]
        if en_passant != '-':
            square = chess.parse_square(en_passant)
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            lastmove = chess.Move(chess.square(file, rank+1), chess.square(file, rank-1))
        else:
            lastmove = None

        # Generate normal image.
        image1 = chess.svg.board(board, orientation = board.turn, lastmove = lastmove, size = IMAGE_SIZE)

        with open(f"{output_dirname}/{p['id']}.svg", 'w') as output_file:
            output_file.write(image1)
            output_file.close()

        # Generate image with arrows.
        arrows = []
        for i in range(len(moves)):
            move = moves[i]
            opacity = 200 - cp_loss[i]*6
            color = ARROW_COLOR + hex(opacity)[2:]
            arrows.append(chess.svg.Arrow(move.from_square, move.to_square, color = color))

        image2 = chess.svg.board(board, orientation = board.turn, arrows = arrows, lastmove = lastmove, size = IMAGE_SIZE)

        with open(f"{output_dirname}/{p['id']}-moves.svg", 'w') as output_file:
            output_file.write(image2)
            output_file.close()

def generate_deck(positions_moves, output_filename):
    with open(output_filename, 'w') as output_file:
        for p in positions_moves:
            board = chess.Board(p['fen'])

            id = p['id']
            fen = p['fen']
            name = p['name']
            if not name and p['continuation_of']:
                name = '<br>'.join(['<small>(continuation of)</small> ' + x for x in p['continuation_of']])
            freq = p['freq']
            move = [''] * MAX_MOVES
            ev = [''] * MAX_MOVES
            move_name = [''] * MAX_MOVES
            cp_loss = [0] * MAX_MOVES
            for i in range(len(p['best_moves'])):
                x = p['best_moves'][i]['evaluation']
                cp_loss[i] = abs(x-p['best_moves'][0]['evaluation'])
                if x == 10000 or x == -10000:
                    ev[i] = "mate"
                elif x > 9000:
                    ev[i] = f"mate in {10000-x}"
                elif x < -9000:
                    ev[i] = f"mate in {10000+x}"
                else:
                    ev[i] = f"<div class=o{cp_loss[i]}>{x/100:+.1f}</div>"
                move[i] = f"<div class=o{cp_loss[i]}>{p['best_moves'][i]['move']}</div>"
                if p['best_moves'][i]['name']:
                    move_name[i] = f"<div class=o{cp_loss[i]}>{p['best_moves'][i]['name']}</div>"

            image_front = f"<img src=\"{id}.svg\">"
            image_back = f"<img src=\"{id}-moves.svg\">"
            output_file.write(f"{fen}\t\"{name}\"\t{freq}")
            for i in range(MAX_MOVES):
                output_file.write(f"\t{move[i]}\t{ev[i]}\t{move_name[i]}")
            output_file.write(f"\t{image_front}\t{image_back}\n")
        output_file.close()

def main():
    with open('chess-positions-best-moves.json') as json_data:
        positions_moves = json.load(json_data)
        json_data.close()

    generate_deck(positions_moves, 'deck.tsv')
    print("Created 'deck.tsv' (to be imported in Anki).")

    generate_images(positions_moves, 'images')
    print("Images stored under 'images/' (to be moved to Anki multimedia folder).")

if __name__ == "__main__":
    main()
