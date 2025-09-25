import subprocess
import argparse
import venv
import sys
from pathlib import Path
from py_exporter import PyExporter


def get_args():
  parser = argparse.ArgumentParser('init.py', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--build', '-b', help='Build script for your system', action='store_true')
  parser.add_argument('--install', '-i', help='Install dependencies for script', dest='env_dir', action='store', metavar='ENV_NAME', type=str)
  parser.add_argument('--requirements', '-r', help='Requirements path for script', action='store', metavar='PATH', type=str, default='./requirements.txt')
  return parser.parse_args()

def main():
  args = get_args()

  requirements_path = Path(args.requirements)
  if args.env_dir:
    env_dir = Path(args.env_dir)
    if Path.exists(env_dir):
      raise FileExistsError(f"Folder with '{env_dir}' already exists")
    
    venv.create(args.env_dir, with_pip=True)

    if not Path.exists(requirements_path):
      raise FileNotFoundError(f"File {requirements_path} not found")
    
    pip_path = Path.joinpath(env_dir, 'bin', 'pip') if sys.platform != 'win32' else Path.joinpath(env_dir, 'Scripts', 'pip')

    subprocess.run([pip_path,  'install',  '-r', requirements_path])

    add_gitignore(str(env_dir))

    if sys.platform == 'win32':
        print(f"{env_dir}\\Scripts\\activate.bat")
    else:
        print(f"source {env_dir}/bin/activate")
        
  if args.build:
    requirements = subprocess.check_output(['pip', 'freeze'], text=True)
    with open(requirements_path, 'w') as file:
      file.write(requirements)
    PyExporter('myousic.py', name='myousic').run()

def add_gitignore(name: str, path: Path = Path('./.gitignore'), raise_error: bool = False) -> None:
  if not Path.exists(path):
    if raise_error:
      raise FileNotFoundError(f"gitignore file not exists: '{path}'")
    return
  with open(path, 'r+') as file_r, open(path, 'a+') as file_w:
    if any([line == name for line in file_r.readlines()]):
      return
    file_w.write('\n' + name)

if __name__ == "__main__":
  main()