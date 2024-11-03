import json

with open('positions.json') as json_data:
    positions_freq = json.load(json_data)
    json_data.close()

fens_freq = []

for k, v in positions_freq.items():
    # the same position might appear multiple times with different names (depending on the order of the moves)
    # of course all entries will have the same frequency

    # collect the list of unique names
    names = sorted(set([elem['name'] for elem in v]))
    names = '\n'.join(names)
    
    # create a single record per position
    fens_freq.append({'fen': k, 'names': names, 'freq': v[0]['freq']})

# sort positions from highest to lowest frequency
fens_freq.sort(key=lambda x: x['freq'], reverse=True)

with open('frequencies.json', 'w') as output_file:
    json.dump(fens_freq, output_file, indent = 4)
    output_file.close()

