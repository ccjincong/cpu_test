import yaml
import paramiko
import os
import threading

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

main_path = config['main_path']
prompt = config['prompt']


def ssh_worker(server, params):
    for model_path in config['model_path']:
        for thread in config['thread']:

            ip_address = params['ip_address']
            username = params['username']
            password = params['password']
            cores = params['cores']

            if cores < thread or cores / 2 > thread:  # 只跑半线程，和满线程
                continue
            file_name = f"{server}_{model_path[model_path.rfind('-') + 1:model_path.find('.bin')]}" \
                        f"_{thread}.txt"

            # 建立连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip_address, username=username, password=password)

            # 循环输出
            for instruction in config['instruction']:
                command = f"{main_path} -m {model_path} " \
                          f"--temp 0.01 --n_predict 256 --top_p 0.95 " \
                          f"--top_k 40 -c 2048 --repeat_penalty 1.1 -t {thread} -p " \
                          f"\"{prompt} User: {instruction} Assistant:\" " \
                          f">> {server}_{model_path[model_path.rfind('-') + 1:model_path.find('.bin')]}" \
                          f"_{thread}.txt 2>&1"
                print(command)
                stdin, stdout, stderr = ssh.exec_command(command)
                stdin.channel.recv_exit_status()

            # 文件回传
            sftp = ssh.open_sftp()
            remote_path = f"/root/{file_name}"
            local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
            sftp.get(remote_path, local_path)
            sftp.close()

            # 数据清洗

            with open(file_name, 'r') as f:
                lines = f.readlines()

            filtered_lines = [line for line in lines if 'llama_print_timings' in line]
            filtered_lines = [line.replace('llama_print_timings:', '') for line in filtered_lines]
            filtered_lines = [line[line.find('=') + 1:] for line in filtered_lines]


            for i, line in enumerate(filtered_lines):
                if i > 4:
                    print(line)
                    filtered_lines[i % 5] = filtered_lines[i % 5].rstrip()
                    filtered_lines[i % 5] += f"\t{line}"
                    print(line)

            with open(file_name, 'w') as f:
                f.writelines(filtered_lines)

            ssh.exec_command(f"rm {remote_path}")

            ssh.close()


# 多线程
threads = []
for server, params in config['SSH'].items():
    t = threading.Thread(target=ssh_worker, args=(server, params))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
