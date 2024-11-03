#import chess
import json
import requests
import sys
import time
from urllib.parse import urlencode

with open('frequencies.json') as json_data:
    fens_freq = json.load(json_data)
    json_data.close()

#print(len(fens_freq))

LIMIT = 2000 # analyze only the most common positions
MAX_CP_LOSS = 30 # keep only the moves that lose less than this amount of centipaws
best_moves = []

# Retrieve the analysis of each position
for i in range(LIMIT):
    p = fens_freq[i]
    while True:
        analysis_url = 'https://lichess.org/api/cloud-eval?{}'
        analysis_params = {'variant': 'standard', 'fen': p['fen'], 'multiPv': 4}
        analysis_call = analysis_url.format(urlencode(analysis_params))
        response = requests.get(analysis_call)
        if response.status_code == 429:
            print("rate limited")
            time.sleep(120)
            continue
        else:
            break
    if response.status_code != 200:
        print(f"failed to retrieve analysis for {p['fen']}: {response.status_code}")
        sys.exit(1)

    print(f"retrieved analysis: {p['names']} - {p['fen']}")
    data = response.json()
    #print(data)

    unique_lines = []
    [unique_lines.append(x) for x in data['pvs'] if x not in unique_lines]

    best_lines = [line for line in unique_lines if abs(line['cp'] - unique_lines[0]['cp']) <= MAX_CP_LOSS]

    best_moves.append({'id': f"{i:04d}", 'fen': p['fen'], 'names': p['names'], 'freq': p['freq'], 'best_lines': best_lines})
    time.sleep(2)

with open('best_moves.json', 'w') as output_file:
    json.dump(best_moves, output_file, indent = 4)
    output_file.close()

