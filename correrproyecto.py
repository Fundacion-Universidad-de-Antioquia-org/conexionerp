import os
import sys

def run_commands():
    try:
        os.system('python3 manage.py makemigrations')
        os.system('python3 manage.py migrate')
        os.system('python3 manage.py runserver')
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_commands()