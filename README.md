# Anki deck for most common chess positions and best moves

The code in this repository can be used to generate a list of the most common chess positions with the best moves that can be played in those positions (according to engine evaluations).

## Usage
First we need a big dataset of PGN files to determine the most common chess positions. A month of games played on lichess (dowloaded from [here](https://database.lichess.org/#standard_games)) can be a good choice.
A file `positions-db` can be created from the PGN files using `create-position-db.py`. Alternatively, you can use the `positions-db` file included in this repository.
By default, `create-position-db.py` considers positions up to move 15 and includes in the output all positions that occur in at least 0.01% of the games in the dataset. This can be changed in the code.

```shell
# Warning: the processing is not very efficient, this will take a looooooong time.
$ zstdcat lichess_db_standard_rated_2024-09.pgn.zst | python create-position-db.py > positions-db
```

Next, we need the engine evaluations to identify the best moves in each position. For this purpose we rely on the lichess evaluations database (dowloaded from [here](https://database.lichess.org/#evals)).
A file `evaluations-db` can be created using `create-evaluations-db.py`

```shell
# Note: the size of the output will be around 5GB.
$ zstdcat lichess_db_eval.jsonl.zst | python create-evaluations-db.py > evaluations-db
```

Finally, we generate a file `names-db` with the names of the openings. These are taken from the lichess [`chess-openings`](https://github.com/lichess-org/chess-openings/) repository.

```shell
$ python create-position-db.py > positions-db
```

Assuming the files `positions-db`, `evaluations-db`, and `names-db` are in the working folder, the main program can run:

```shell
$ python chess-positions-best-moves.py
...
Output written to chess-positions-best-moves.json.
```

The content of `chess-positions-best-moves.json` will look like this:

```json
[
    {
        "id": "0000",
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -",
        "freq": 87713430,
        "name": "Starting position",
        "continuation_of": [],
        "best_moves": [
            {
                "move": "e4",
                "evaluation": 18,
                "name": "King's Pawn Game"
            },
            {
                "move": "Nf3",
                "evaluation": 17,
                "name": "Zukertort Opening"
            },
            {
                "move": "d4",
                "evaluation": 17,
                "name": "Queen's Pawn Game"
            },
            {
                "move": "c4",
                "evaluation": 12,
                "name": "English Opening"
            },
            {
                "move": "g3",
                "evaluation": 8,
                "name": "Hungarian Opening"
            },
            {
                "move": "e3",
                "evaluation": 3,
                "name": "Van't Kruijs Opening"
            },
            {
                "move": "b3",
                "evaluation": 0,
                "name": "Nimzo-Larsen Attack"
            },
            {
                "move": "h3",
                "evaluation": -3,
                "name": "Clemenz Opening"
            },
            {
                "move": "a3",
                "evaluation": -3,
                "name": "Anderssen's Opening"
            },
            {
                "move": "Nc3",
                "evaluation": -5,
                "name": "Van Geet Opening"
            }
        ]
    },
    {
        "id": "0001",
        "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq -",
        "freq": 51064394,
        "name": "King's Pawn Game",
        "continuation_of": [
            "Starting position"
        ],
        "best_moves": [
            {
                "move": "e5",
                "evaluation": 21,
                "name": "King's Pawn Game"
            },
            {
                "move": "c5",
                "evaluation": 25,
                "name": "Sicilian Defense"
            },
            {
                "move": "e6",
                "evaluation": 28,
                "name": "French Defense"
            },
            {
                "move": "c6",
                "evaluation": 28,
                "name": "Caro-Kann Defense"
            },
            {
                "move": "d6",
                "evaluation": 34,
                "name": "Pirc Defense"
            },
            {
                "move": "Nc6",
                "evaluation": 36,
                "name": "Nimzowitsch Defense"
            },
...
```

By default, the best moves listed for each position will be the moves with an evaluation within 25 centipawns from the best move.

The information in `chess-positions-best-moves.json` can be converted in a tab-separated file and a set of SVG images suitable to be used to create an Anki deck:

```shell
$ python export-anki-deck.py
Created 'deck.tsv' (to be imported in Anki).
Images stored under 'images/' (to be moved to Anki multimedia folder).
```
