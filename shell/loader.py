import argparse
import shutil
import subprocess
import sys
import time
from queue import Queue
from threading import Thread

from nailpolish import BLUE, GRAY, GREEN, RED, RESET

BRAILLE_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def get_terminal_size():
    return shutil.get_terminal_size((80, 20))


def clear_lines(n):
    for _ in range(n):
        sys.stdout.write("\033[1A")  # Move cursor up one line
        sys.stdout.write("\033[K")  # Clear the line


def enqueue_output(out, queue):
    for line in iter(out.readline, b""):
        queue.put(line.decode().strip())
    out.close()


def main():
    parser = argparse.ArgumentParser(
        description="A loading spinner with command output"
    )
    parser.add_argument("message", help="The message to display")
    parser.add_argument("command", help="The command to run", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    message = args.message
    command = args.command

    if not command:
        print("Error: No command provided.")
        sys.exit(1)

    spinner_index = 0
    output_queue = Queue()
    output_lines = []

    terminal_width, terminal_height = get_terminal_size()
    max_output_lines = terminal_height - 3  # Reserve 3 lines for spinner and message

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        # Start thread to read output
        t = Thread(target=enqueue_output, args=(process.stdout, output_queue))
        t.daemon = True
        t.start()

        while process.poll() is None:
            # Get all lines currently in the queue
            while not output_queue.empty():
                line = output_queue.get_nowait()
                output_lines.append(line)
                if len(output_lines) > max_output_lines:
                    output_lines.pop(0)

            # Clear previous output
            clear_lines(len(output_lines) + 2)

            # Print the message and spinner
            print(f"{BLUE}{message}{RESET}")
            print(f"{BRAILLE_SPINNER[spinner_index]}", end="", flush=True)

            # Print scrolling output
            for line in output_lines:
                print(f"\n{GRAY}{line[:terminal_width-1]}{RESET}", end="")

            spinner_index = (spinner_index + 1) % len(BRAILLE_SPINNER)
            time.sleep(0.1)

        # Get any remaining output
        while not output_queue.empty():
            line = output_queue.get_nowait()
            output_lines.append(line)
            if len(output_lines) > max_output_lines:
                output_lines.pop(0)

        # Clear the spinner line
        print("\r", end="", flush=True)

        # Print final status
        exit_code = process.returncode
        status = "OK" if exit_code == 0 else f"NOT OK ({exit_code})"
        if status == "OK":
            print(f"{GREEN}{message} ... {status}{RESET}")
        else:
            print(f"{RED}{message} ... {status}{RESET}")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
