import yaml
import paramiko
import os

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

main_path = config['main_path']
model_path = config['model_path']
thread = config['thread']

for server, params in config['SSH'].items():
    file_name = f"{server}_{model_path[model_path.rfind('-') + 1:model_path.find('.bin')]}" \
                f"_{thread}.txt"

    with open(file_name, 'r') as f:
        lines = f.readlines()

    filtered_lines = [line for line in lines if 'llama_print_timings' in line]
    filtered_lines = [line.replace('llama_print_timings:', '') for line in filtered_lines]
    filtered_lines = [line[line.find('=')+1:] for line in filtered_lines]

    for i,line in enumerate(filtered_lines):
        if i>4:
            print(line)
            filtered_lines[i % 5]=filtered_lines[i % 5].rstrip()
            filtered_lines[i%5] += f"\t{line}"
            print(line)



    with open(file_name, 'w') as f:
        f.writelines(filtered_lines)


