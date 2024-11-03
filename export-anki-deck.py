import chess
import chess.svg
import genanki
import json
import os
import urllib.request

# Number of notes to include in the deck.
N_NOTES = 1000

# Maximum number of moves to show.
MAX_MOVES = 20

# Image size in pixels
IMAGE_SIZE = 300

# Color of the arrows in the images and of the text in the answers
ARROW_COLOR = '#15781B'

class ChessNote(genanki.Note):
    @property
    def guid(self):
        return genanki.guid_for(self.fields[0])

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

def generate_model() -> genanki.Model:
    fields = [
        {'name': 'id'},
        {'name': 'fen'},
        {'name': 'name'},
        {'name': 'freq'},
    ]
    for i in range(MAX_MOVES):
        fields.extend([
            {'name': f"move{i}"},
            {'name': f"eval{i}"},
            {'name': f"name{i}"},
        ])
    fields.extend([
        {'name': 'image-front'},
        {'name': 'image-back'},
    ])

    qfmt = """
{{image-front}}
"""
    afmt = """
{{image-back}}<br>

<b>{{name}}</b><br><br>

<center>
<table>
"""
    for i in range(MAX_MOVES):
        afmt += f"""
  <tr>
    <td><b>{{{{move{i}}}}}</b></td>
    <td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</br>
    <td>{{{{eval{i}}}}}</td>
    <td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</br>
    <td>{{{{name{i}}}}}</td>
  </tr>
"""

    afmt += """
  </tr>
</table>
</center>
<br>

<div>
<a href="https://lichess.org/analysis/standard/{{fen}}"><img style="width: 32px; height: 32px;" src="_lichess.ico"></a>
</div>
"""

    css = f"""
.card {{
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: {ARROW_COLOR};
    background-color: white;
}}
"""
    # One level of opacity for each value of cp_loss.
    for i in range(26):
        css += f"""
.o{i} {{
    opacity: {1-0.02*i:.2f};
}}
"""

    return genanki.Model(
        1738856564,
        'Chess',
        fields=fields,
        templates=[
            {
                'name': 'Chess',
                'qfmt': qfmt,
                'afmt': afmt,
            },
        ],
        css=css)

def generate_notes(positions_moves, model) -> [ChessNote]:
    notes = []
    for p in positions_moves:
        board = chess.Board(p['fen'])

        id = p['id']
        fen = p['fen']
        name = p['name']
        if not name:
            if p['continuation_of']:
                name = '<br>'.join(['<small>(continuation of)</small> ' + x for x in p['continuation_of']])
            else:
                name = ''
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

        fields = [id, fen, name, str(freq)]
        for i in range(MAX_MOVES):
            fields.extend([move[i], ev[i], move_name[i]])
        fields.extend([image_front, image_back])
        notes.append(ChessNote(model=model, fields=fields))
    return notes

def main():
    with open('chess-positions-best-moves.json') as json_data:
        positions_moves = json.load(json_data)
        json_data.close()

    # Keep only the first N_NOTES.
    positions_moves = positions_moves[0:N_NOTES]

    print("Generating notes...")
    model = generate_model()
    notes = generate_notes(positions_moves, model)

    print("Generating images...")
    generate_images(positions_moves, 'images')
    urllib.request.urlretrieve("http://lichess.org/favicon.ico", "images/_lichess.ico")

    print("Creating deck...")
    deck = genanki.Deck(
        1536307405,
        'Chess - Common Positions and Best Moves'
    )

    media_files = [ 'images/_lichess.ico' ]
    for n in notes:
        deck.add_note(n)
        media_files.append(f"images/{n.fields[0]}.svg")
        media_files.append(f"images/{n.fields[0]}-moves.svg")

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file('Chess - Common Positions and Best Moves.apkg')
    print("Created 'Chess - Common Positions and Best Moves.apkg'.")

if __name__ == "__main__":
    main()

