import sys
from argparse import ArgumentParser

from loader_db import run_loader_db
from loader_filesys import run_filesys

if __name__ == "__main__":
    # CLI: Arguments
    parser = ArgumentParser()
    parser.add_argument(
        "--destination",
        required=True,
        help="Directs the destination of the final processed and cleaned data.",
    )

    # Pre-define all potential arguments before parsing
    parser.add_argument(
        "--path", help="File path or folder output to save new results or read CSV."
    )
    parser.add_argument("--transform", help="File name from previous run.")
    parser.add_argument("--name", help="File name to save results.")

    args = parser.parse_args()

    if args.destination == "dir":
        run_filesys(args)
    elif args.destination == "db":
        run_loader_db(args)
    else:
        print(
            (
                "The input destination argument must be either 'db' or"
                "'dir'. Review README documentation."
            )
        )
        sys.exit(1)
