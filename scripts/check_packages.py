import subprocess
import sys

packages = ['torch', 'transformers', 'bitsandbytes', 'accelerate', 'qwen-vl-utils']
for pkg in packages:
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', pkg], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if line.startswith('Name:') or line.startswith('Version:'):
                    print(line)
        else:
            print(f"{pkg}: not installed")
    except Exception as e:
        print(f"{pkg}: error - {e}")
    print("---")
