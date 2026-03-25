import os

def get_unique_prefixes(directory):
    unique_prefixes = set()
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            # Split the filename by the last two dots
            parts = filename.rsplit('.', 2)
            if len(parts) == 3:
                prefix = parts[0]
                unique_prefixes.add(prefix)
    return sorted(unique_prefixes)

def determine_name(prefix):
    if 'Digital' in prefix:
        name = 'D-'
    elif 'Hybrid' in prefix:
        name = 'H-'
    else:
        name = ''

    if 'GREEDY-BITRATE_MAXIMIZATION' in prefix:
        name += 'BM'
    elif 'GREEDY-PF_MAXIMIZATION' in prefix:
        name += 'PFM'
    elif 'GREEDY-QUEUE_AWARE_PF_MAXIMIZATION' in prefix:
        name += 'QPFM'
    elif 'GREEDY-QUEUE_LENGTH_MINIMIZATION' in prefix:
        name += 'QLM'
    else:
        name += 'UNKNOWN'

    return name

def write_scenarios_to_file(directory, output_file):
    unique_prefixes = get_unique_prefixes(directory)
    with open(output_file, 'w') as f:
        f.write("scenarios = [\n")
        for prefix in unique_prefixes:
            name = determine_name(prefix)
            f.write(f"    {{'prefix': '{prefix}', 'name': '{name}'}},\n")
        f.write("]\n")

if __name__ == "__main__":
    directory = 'output'  # Directory where the JSON files are stored
    output_file = os.path.join(directory, 'scenarios.txt')
    write_scenarios_to_file(directory, output_file)
    print(f"Scenarios written to {output_file}")
