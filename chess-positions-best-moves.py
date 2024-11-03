import copy
import json
import chess
from collections import deque

# When creating the list of best moves, keep only the moves that are within 25 centipawns of the best move.
BEST_MOVES_CUTOFF: int = 25

def trimmed_fen(fen: str) -> str:
    return ' '.join(fen.split(' ')[0:4])

def parent_names(initial_fen: str, positions: dict[str, int], names: dict[str, str]) -> dict[str, [str]]:
    # Assign names to positions based on the names of the parents, using a bfs tree search.
    queue = deque([{ 'fen': initial_fen, 'named_parents': [] }])
    visited_nodes = dict()
    while queue:
        node = queue.popleft()
        fen = node['fen']
        if fen in visited_nodes:
            # The same node was queued multiple times before being visited: merge the parents.
            for name in node['named_parents']:
                if name not in visited_nodes[fen]:
                    visited_nodes[fen].append(name)
            continue

        visited_nodes[fen] = copy.deepcopy(node['named_parents'])

        board = chess.Board(fen)
        new_nodes = []
        for move in board.legal_moves:
            board.push(move)
            new_fen = trimmed_fen(board.fen())
            if new_fen not in visited_nodes and new_fen in positions:
                if fen in names:
                    new_nodes.append({ 'fen': new_fen, 'named_parents': [names[fen]] })
                else:
                    new_nodes.append({ 'fen': new_fen, 'named_parents': node['named_parents'] })
            board.pop()
        new_nodes.sort(key=lambda x: positions[x['fen']], reverse=True)
        queue.extend(new_nodes)

    return visited_nodes

def main():
    print("Loading most frequent positions...")
    positions = {}
    with open('positions-db') as positions_data:
        for line in positions_data:
            fen, freq = line.rstrip().split('\t')
            positions[fen] = int(freq)
        positions_data.close()
    print(f"Loaded {len(positions)} positions.")

    print("Loading opening names...")
    initial_fen = trimmed_fen(chess.STARTING_FEN)
    names = { initial_fen: 'Starting position' }
    with open('names-db') as names_data:
        for line in names_data:
            fen, name = line.rstrip().split('\t')
            names[fen] = name
        names_data.close()
    print(f"Loaded {len(names)} names.")

    print("Assigning names based on the names of parent positions...")
    p_names = parent_names(initial_fen, positions, names)

    # Build a dict with the evaluations of all positions reachable from the loaded positions.
    print("Exploring neighbor positions...")
    all_positions_eval = {}
    for fen in positions.keys():
        board = chess.Board(fen)
        if fen not in all_positions_eval:
            all_positions_eval[fen] = None
        for move in board.legal_moves:
            board.push(move)
            new_fen = trimmed_fen(board.fen())
            if new_fen not in all_positions_eval:
                all_positions_eval[new_fen] = None
            board.pop()
    print(f"Created list of {len(all_positions_eval)} positions.")

    print("Assigning evaluations...")
    with open('evaluations-db') as eval_data:
        for line in eval_data:
            fen, ev = line.rstrip().split('\t')
            if fen in all_positions_eval:
                all_positions_eval[fen] = int(ev)
        eval_data.close()

    print("Listing best moves...")
    n = 0
    positions_moves = []
    max_n_moves = 0
    max_n_moves_fen = None
    for fen, freq in positions.items():
        board = chess.Board(fen)
        if board.is_game_over():
            continue

        move_list = []
        for move in board.legal_moves:
            san = board.san(move)
            board.push(move)
            new_fen = trimmed_fen(board.fen())
            if all_positions_eval[new_fen] is not None:
                move_list.append((san, all_positions_eval[new_fen], new_fen))
            elif board.outcome() is not None:
                if board.outcome().winner == chess.WHITE:
                    move_list.append((san, 10000, new_fen))
                elif board.outcome().winner == chess.BLACK:
                    move_list.append((san, -10000, new_fen))
            board.pop()
        if board.turn == chess.WHITE:
            move_list.sort(key=lambda x: x[1], reverse=True)
        elif board.turn == chess.BLACK:
            move_list.sort(key=lambda x: x[1], reverse=False)
        if not move_list:
            print(f"No evaluated moves found for: {fen}")
            continue

        obj = {}
        obj['id'] = f"{n:04d}"
        obj['fen'] = fen
        obj['freq'] = freq
        obj['name'] = names.get(fen, None)
        obj['continuation_of'] = p_names.get(fen, [])
        obj['best_moves'] = []

        best_ev = move_list[0][1]
        for (m, ev, new_fen) in move_list:
            if abs(ev - best_ev) <= BEST_MOVES_CUTOFF:
                obj['best_moves'].append({ 'move': m, 'evaluation': ev, 'name': names.get(new_fen, None) })
        if len(obj['best_moves']) > max_n_moves:
            max_n_moves = len(obj['best_moves'])
            max_n_moves_fen = obj['fen']
        positions_moves.append(obj)
        n += 1

    positions_moves.sort(key=lambda x: x['freq'], reverse=True)

    print(f"Maximum number of moves considered from one position: {max_n_moves} ({max_n_moves_fen})")

    # Sanity check: compare position evaluation with evaluation of best move.
    for obj in positions_moves:
        pos_ev = all_positions_eval[obj['fen']]
        best_move = obj['best_moves'][0]['move']
        best_move_ev = obj['best_moves'][0]['evaluation']
        if pos_ev is None:
            print(f"warning: {obj['fen']} has no evaluation?")
            continue

        if abs(pos_ev - best_move_ev) > 30:
            print(f"warning: {obj['fen']} has evaluation: {pos_ev}; best move: {best_move}; best move evaluation: {best_move_ev}")

    out_filename = 'chess-positions-best-moves.json'
    with open(out_filename, 'w') as f:
        json.dump(positions_moves, f, indent=4)

    print(f"Output written to {out_filename}.")

if __name__ == "__main__":
    main()
