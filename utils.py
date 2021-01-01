from typing import Dict


def read_commands_from_file(filename: str) -> Dict[str, str]:
    commands = {}
    with open(filename, 'r') as file:
        for line in file:
            cmd_name = line.split(' ')[0]
            commands[cmd_name] = line
    file.close()
    return commands
