# gpt_nexus/cli.py
import argparse

from nexus.main import run_streamlit


def main():
    parser = argparse.ArgumentParser(description="CLI for Nexus App")
    parser.add_argument("command", help="The command to run")
    parser.add_argument(
        "subcommand", nargs="?", help="An optional subcommand for 'run'"
    )

    args = parser.parse_args()

    if args.command == "run" and (
        args.subcommand == "streamlit" or args.subcommand is None
    ):
        run_streamlit()
    else:
        print(
            f"Unknown command or subcommand: {args.command} {args.subcommand if args.subcommand else ''}"
        )


if __name__ == "__main__":
    main()
