import sys
from argparse import ArgumentParser

from db_loader import run_loader_db
from filesys_loader import run_loader


# Parse CLI arguments for marketplace metadata and output destination
def cli_arguments() -> ArgumentParser:
    parser = ArgumentParser(description="Route cleaned data to 'db' or 'dir' output.")
    parser.add_argument(
        "-m", "--marketplace", default="amazonae", help="Marketplace name."
    )
    parser.add_argument(
        "-c", "--category", default="pet food", help="Product category."
    )
    parser.add_argument(
        "-s", "--subcategory", default="wet food", help="Product subcategory."
    )
    parser.add_argument(
        "-d",
        "--destination",
        required=True,
        help="Target output destination: 'db' or 'dir'.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # Parse CLI arguments
    args = cli_arguments()

    # Route based on specified destination
    if args.destination == "dir":
        run_loader(args)
    elif args.destination == "db":
        run_loader_db(args)
    else:
        print("Destination must be either 'db' or 'dir'. Refer to documentation.")
        sys.exit(1)
