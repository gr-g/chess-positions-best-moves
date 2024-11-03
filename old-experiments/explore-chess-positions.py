import requests
import json
import time
import chess
from collections import deque
from urllib.parse import urlencode
 
# Explore positions that occur in at least 0.1% of the games in the database.
THRESHOLD: float = 0.001
 
# For a position above the threshold, evaluate all moves even if they lead to a position below the threshold
# unless the frequency of the move is extremely low.
EVALUATION_THRESHOLD: float = THRESHOLD * 0.01
 
# When creating a list of best moves, keep only the moves that are within 25 centipawns of the best move
BEST_MOVES_CUTOFF: int = 25
 
def trimmed_fen(fen: str) -> str:
    return ' '.join(fen.split(' ')[0:4])
 
class Node:
    def __init__(self, fen: str):
        self.fen = fen # This stores the FEN of the position without the move counters (the first 4 parts of the real FEN)
        self.frequency = None # Will be filled when visiting the node.
        self.name = None # Name in case the position corresponds exactly to a named opening. Will be filled when visiting the node.
        self.evaluation = None # Evaluation of the position in centipawns. Will be filled when visiting the node.
        self.named_parents = [] # Will be filled with the parent name(s) when the new node is added to the queue. If the same node is added to the queue multiple times, the values are merged together.
        self.best_moves = [] # List of objects with: move, fen, evaluation, name. The evaluation and name fields will be filled when running fill_best_moves().
 
    def set_parent(self, other):
        if other.name:
            self.named_parents.append(other.name)
        else:
            for name in other.named_parents:
                if name not in self.named_parents:
                    self.named_parents.append(name)
 
    def add_child(self, move: str, fen: str):
        self.best_moves.append({'move': move, 'fen': fen, 'evaluation': None, 'name': None})
 
def get_position_data(fen: str) -> str:
    url = 'https://explorer.lichess.ovh/lichess?{}'
    params = {'variant': 'standard', 'fen': fen, 'moves': 20, 'topGames': 0, 'recentGames': 0}

    while True:
        response = requests.get(url.format(urlencode(params)))
        if response.status_code == 429:
            print("Rate limited. Waiting for 120 seconds...")
            time.sleep(120)
            continue
        elif response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            exit(1)
        return response.json()
 
def get_evaluation_data(fen: str) -> str:
    url = 'https://lichess.org/api/cloud-eval?{}'
    params = {'variant': 'standard', 'fen': fen}

    while True:
        response = requests.get(url.format(urlencode(params)))
        if response.status_code == 429:
            print("Rate limited. Waiting for 120 seconds...")
            time.sleep(120)
            continue
        elif response.status_code == 404:
            return None
        elif response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            exit(1)
        return response.json()
 
def bfs(initial_fen: str) -> dict[str, Node]:
    initial_data = get_position_data(initial_fen)
    initial_frequency = initial_data['white'] + initial_data['draws'] + initial_data['black']
    root = Node(initial_fen)
    root.name = 'Initial position'
    queue = deque([root])
    visited_nodes = dict()
 
    while queue:
        current_node = queue.popleft()
        fen = current_node.fen
        if fen in visited_nodes:
            # The same node was queued multiple times before being visited: merge the parents.
            for name in current_node.named_parents:
                if name not in visited_nodes[fen].named_parents:
                    visited_nodes[fen].named_parents.append(name)
            continue
 
        position_data = get_position_data(fen)
        evaluation_data = get_evaluation_data(fen)
        time.sleep(2) # Wait a bit after the API calls to be nice to the server
 
        # Set frequency, name and evaluation for the position.
        current_node.frequency = position_data['white'] + position_data['draws'] + position_data['black']
        if position_data['opening'] is not None:
            current_node.name = position_data['opening']['name']
        if evaluation_data:
            current_node.evaluation = evaluation_data['pvs'][0].get('cp', None)
 
        visited_nodes[fen] = current_node
        if current_node.name:
            print(f"visited node {fen} (freq: {current_node.frequency / initial_frequency:.4%}; \"{current_node.name}\")")
        else:
            print(f"visited node {fen} (freq: {current_node.frequency / initial_frequency:.4%})")
 
        if current_node.frequency < (initial_frequency * THRESHOLD):
            continue
 
        moves = position_data['moves']
        for move in moves:
            move_frequency = move['white'] + move['draws'] + move['black']
            move_san = move['san']
            # The frequency here is the frequency of occurrence of the position
            # *from this move*, the same position can be reached also from other
            # moves. We also want to visit the node to get its evaluation, in case
            # it turns out to be one of the best moves.
            if move_frequency >= (initial_frequency * THRESHOLD * 0.01):
                board = chess.Board(current_node.fen)
                board.push_san(move_san)
                new_fen = trimmed_fen(board.fen())
                current_node.add_child(move_san, new_fen)
                if new_fen not in visited_nodes:
                    new_node = Node(new_fen)
                    new_node.set_parent(current_node)
                    queue.append(new_node)

        print(f"Added {len(current_node.best_moves)} nodes. Queue: {len(queue)}.")
 
    return visited_nodes
 
def fill_best_moves(visited_nodes: dict[str, Node]):
    for node in visited_nodes.values():
        new_best_moves = []
        side_to_move = chess.Board(node.fen).turn
        for m in node.best_moves:
            next_node = visited_nodes[m['fen']]
            if next_node.evaluation:
                new_best_moves.append({'move': m['move'], 'fen': m['fen'], 'evaluation': next_node.evaluation, 'name': next_node.name})
 
        # Sort moves from best to worst
        if side_to_move == chess.WHITE:
            new_best_moves.sort(key=lambda x: x['evaluation'], reverse=True)
        elif side_to_move == chess.BLACK:
            new_best_moves.sort(key=lambda x: x['evaluation'], reverse=False)
 
        node.best_moves.clear()
        for m in new_best_moves:
            if abs(m['evaluation'] - new_best_moves[0]['evaluation']) <= BEST_MOVES_CUTOFF:
                node.best_moves.append(m)
 
def main():
    initial_fen = trimmed_fen(chess.STARTING_FEN)
    visited_nodes = bfs(initial_fen)
    print(f"Visited {len(visited_nodes)} positions.")

    fill_best_moves(visited_nodes)
 
    # Select the entries above the threshold and store them in a list, sorted by frequency
    selected_nodes = [v for v in visited_nodes.values() if v.frequency >= (visited_nodes[initial_fen].frequency * THRESHOLD)]
    selected_nodes.sort(key=lambda x: x.frequency, reverse=True)
   
    with open('visited_nodes.json', 'w') as f:
        json.dump(selected_nodes, f, indent=4, default=vars)

    print(f"wrote {len(selected_nodes)} positions to visited_nodes.json")

if __name__ == "__main__":
    main()

