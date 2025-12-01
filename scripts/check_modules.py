import json
import os
import platform
import subprocess
import time


def find_file_recursively(filename, path='.'):
    """
    Searches for a file with the specified name recursively starting from the
    given directory path.

    This function traverses through directories and subdirectories recursively
    to locate files that match the specified filename. It uses a generator to
    yield full file paths whenever a match is found.

    :param filename: The name of the file to search for.
    :type filename: str
    :param path: The directory path to start the search from. Defaults to the
        current directory.
    :type path: str
    :return: A generator that yields the full paths of files matching the
        specified filename.
    :rtype: Generator[str, None, None]
    """

    def recurse(path):
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                yield from recurse(full_path)
            else:
                if os.path.basename(full_path) == filename:
                    yield full_path

    yield from recurse(path)


def generate():
    """
    :return:
    """
    modules = set()
    for mod_file in find_file_recursively("go.mod", path='..'):
        with open(mod_file, 'r') as f:
            for line in f:
                pieces = line.strip().split(' ')
                index = 1 if pieces[0] == 'require' else 0
                if '/' in pieces[index]:
                    modules.add("@".join(pieces[index:index + 2]))

    modules_list = sorted(list(modules))
    results = {}
    for go_proxy in ["https://goproxy.cn,direct", "https://goproxy.io,direct", "direct"]:
        command = "go clean -modcache"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{command} failed")
            exit(result.returncode)
        go_proxy_environment = os.environ.copy()
        go_proxy_environment["GOPROXY"] = go_proxy
        for module in modules_list:
            if "github.com/OpenNHP/opennhp/nhp" in module:
                continue
            command = f"go mod download -json {module}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, env=go_proxy_environment)
            if result.returncode != 0:
                resultMap = results.get(module, {})
                resultMap[go_proxy] = json.loads(result.stdout)
                print(resultMap[go_proxy]['Error'])
                results[module] = resultMap
    return results


def main():
    prefix = "-".join([platform.system(), platform.release()])
    filename = prefix + '.json'
    with open(filename, 'w') as g:
        results = generate()
        json.dump(results, g, indent=4)


if __name__ == '__main__':
    main()
