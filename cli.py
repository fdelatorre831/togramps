
import argparse
from pathlib import Path
import pandas as pd

from src.togramps.core import extract_data_ftt, gramps_dfs_to_file, interim_to_gramps_dfs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert FTZ file to Gramps CSV")
    parser.add_argument('--ftz-source', type=str, help='Path to source .ftz file')
    parser.add_argument('--interim-person-csv', type=str, help='Path to intermediary person .csv file')
    parser.add_argument('--interim-relationship-csv', type=str, help='Path to intermediary relationship .csv file')
    parser.add_argument('--temp_dir', type=str, default="temp", help='Path to data directory')
    parser.add_argument('--output_dir', type=str, default="output", help='Path to output directory')
    args = parser.parse_args()

    if not all([args.interim_person_csv, args.interim_relationship_csv]) and any([
        args.interim_person_csv, args.interim_relationship_csv
    ]):
        parser.error(
            "--interim-relationship-csv and --interim-person-csv must be provided together"
        )
    if args.ftz_source and any([args.interim_person_csv, args.interim_relationship_csv]):
        parser.error(
            "Only one of --ftz-source or interim sources can be provided"
        )
    if not any([args.ftz_source, args.interim_person_csv, args.interim_relationship_csv]):
        parser.error(
            "One of --ftz-source or interim sources must be provided"
        )
        
    temp_dir = Path(args.temp_dir)
    output_dir = Path(args.output_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_files = []
    if args.ftz_source:
        source_files.append(Path(args.ftz_source))
    else:
        source_files.append(Path(args.interim_person_csv))
        source_files.append(Path(args.interim_relationship_csv))
    
    for source_file in source_files:
        if not source_file.exists():
            raise FileNotFoundError(f"Source file {source_file} does not exist.")

    if len(source_files) == 1: # .ftz source
        source_file = source_files[0]
        name = source_file.stem
        person_df, relationship_df = extract_data_ftt(source_file, temp_dir)
        person_path = temp_dir / (name + "_person.csv")
        relationship_path = temp_dir / (name + "_relationship.csv")
        person_df.to_csv(person_path, index=False, encoding='utf-8')
        relationship_df.to_csv(relationship_path, index=False, encoding='utf-8')
        print(f"Extracted person from {source_file} to {person_path} and {relationship_path}. Continuing to Gramps generation. If you find issues, manually inspect/postprocess and pass interim sources directly.")
        source_files = [person_path, relationship_path]
    if len(source_files) == 2: # interim csv sources
        person_source_file = source_files[0]
        relationship_source_file = source_files[1]
        name = person_source_file.stem.replace("_person", "")

        person_df = pd.read_csv(person_source_file, encoding='utf-8')
        relationship_df = pd.read_csv(relationship_source_file, encoding='utf-8')

        gramps_place_df, gramps_person_df, gramps_marriage_df, family_df = interim_to_gramps_dfs(person_df, relationship_df)

        file_path = output_dir / (name + ".csv")
        gramps_dfs_to_file(file_path, gramps_place_df, gramps_person_df, gramps_marriage_df, family_df)
        print(f"Converted interim files to Gramps CSV at {file_path}.")
    else:
        raise ValueError("Found invalid number of source files.")