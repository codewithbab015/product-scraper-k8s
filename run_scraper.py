import subprocess
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import yaml


def load_config(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_filename(template: str, category_name: str, timestamp: str = None) -> str:
    if timestamp:
        return template.format(category_name=category_name, timestamp=timestamp)
    return template.format(category_name=category_name)


def build_args(
    run_mode: str,
    folder_path: Path,
    run_script: Path,
    output_file: str,
    config: dict,
    category_name: str,
    max_number: str,
    destination: str,
    limit_records: str
) -> list:
    args = ["python3", str(run_script), "--path", str(folder_path)]
    match run_mode:
        case "extract":
            args += [
                "--name",
                str(output_file),
                "--url",
                config["url_template"],
                "--min",
                str(config["min_page_index"]),
                "--max",
                str(max_number),
            ]
        case "transform":
            extract_file = format_filename(
                config["extract"]["file-name"], category_name
            )
            args += [
                "--name",
                str(output_file),
                "--extract",
                str(folder_path / extract_file),
                "--limit_records",
                str(limit_records)
            ]
        case "load":
            transform_file = format_filename(
                config["transform"]["file-name"], category_name
            )
            args += [
                "--name",
                str(output_file),
                "--transform",
                str(folder_path / transform_file),
                "--destination",
                str(destination),
            ]
        case "upload":
            args += []
        case _:
            print("Unsupported run_mode: %s", run_mode)
    return args


def parse_arguments():
    parser = ArgumentParser(description="Run Amazon data scraper pipeline.")
    parser.add_argument("--run_group", help="Main category group (e.g., pet-food).")
    parser.add_argument("--run_name", help="Subcategory under run_group.")
    parser.add_argument(
        "--run_mode", help="Stage to run (extract, transform, clean, load)."
    )
    parser.add_argument(
        "--destination",
        help="Directs the destination of the final processed and cleaned data.",
    )
    parser.add_argument("--max", type=int, default=1, help="Maximum page number limit")
    parser.add_argument("--limit_records", default="", help="Limit the maximum record values are required.")
    return parser.parse_args()


def get_config_from_args_or_yaml(config, args):
    # Prefer CLI args if provided
    if args.run_group and args.run_name and args.run_mode:
        print("CLI arguments provided.")
        return args.run_group, args.run_name, args.run_mode

    print("Using config from YAML ...")
    run_group = config["run-group"]
    sub_group = config[run_group]
    return run_group, sub_group["run-name"], sub_group["run-type"]


def run_main():
    config = load_config("configs.yml")
    args = parse_arguments()

    max_page_num = args.max
    run_group, run_name, run_mode = get_config_from_args_or_yaml(config, args)

    sub_group = config[run_group]
    category_group = sub_group[run_name]
    run_type_config = category_group[run_mode]

    # Compose category name and paths
    category_name = f"{run_group.replace('-', '_')}_{run_name.replace('-', '_')}"
    folder_path = Path("data") / run_group / run_name

    # print(category_group)
    # print(run_type_config)
    # Compose output file

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if run_mode == "load" else None
    output_file = folder_path / format_filename(
        run_type_config["file-name"], category_name, timestamp
    )

    output_file = category_name if run_mode == "upload" else output_file
    print(output_file)
    # Build and execute script arguments
    script_path = run_type_config["run-script"]
    command_args = build_args(
        run_mode,
        folder_path,
        script_path,
        output_file,
        category_group,
        category_name,
        max_page_num,
        args.destination,
        args.limit_records
    )

    print(f"Running script with args: {command_args}")
    subprocess.run(command_args)


if __name__ == "__main__":
    run_main()
