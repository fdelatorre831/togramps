from pathlib import Path
from zipfile import ZipFile
import pandas as pd
import re
import datetime
from typing import Tuple

FTT_PERSON_COLS = ["person_id",None,"parent_set_id","sibling_index",None,None,None,None,None,None,None,None,"last_name","first_name",None,"birth_year","birth_month","birth_day",None,"death_year","death_month","death_day","gender","notes"]
FTT_RELATIONSHIPS_COLS = ["parent_set_id","marriage_status","parent_1",None,"parent_2","relationship_index",None,None,None,None,None,None]

GRAMPS_CSV_PLACE_COLS = ["Place","Title","Name","Type","Latitude","Longitude","Code","Enclosed_by","Date"]
GRAMPS_CSV_PERSON_COLS = ["Person","Surname","Given","Call","Nickname","Suffix","Prefix","Title","Gender","Birth date","Birth place","Birth source","Baptism date","Baptism place","Baptism source","Death date","Death place","Death source","Burial date","Burial place","Burial source","Note"]
GRAMPS_CSV_MARRIAGE_COLS = ["Marriage","Husband","Wife","Date","Place","Source","Note"]
GRAMPS_CSV_FAMILY_COLS = ["Family", "Child"]

def extract_data_ftt(source_file: Path, temp_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    with ZipFile(source_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    name = source_file.stem

    # load data from node.ftt file
    node_file = Path(temp_dir) / name / "node.ftt"
    person_data = []
    relationship_data = []

    with open(node_file, 'r', encoding='utf-8') as file:
        for i, line in enumerate(file):
            if i == 0: # skip header
                continue
            tokens = line.rstrip("\n").split()

            if len(tokens) > 12:
                # fixed-width numeric section
                base = tokens[:12]

                # everything between col 12 and the first numeric birth field is name
                rest = tokens[12:]

                # find first numeric field (birth_year)
                split_idx = None
                for i, t in enumerate(rest):
                    if re.fullmatch(r"-?\d+", t):
                        split_idx = i
                        break

                if split_idx is None:
                    name_tokens = rest
                    numeric = []
                else:
                    name_tokens = rest[:split_idx]
                    numeric = rest[split_idx:]

                # last token of name = given name, rest = surname
                if len(name_tokens) == 0:
                    last_name = ""
                    first_name = ""
                elif len(name_tokens) == 1:
                    last_name = name_tokens[0]
                    first_name = ""
                else:
                    last_name = " ".join(name_tokens[:-1])
                    first_name = name_tokens[-1]

                # normalize casing
                last_name = last_name.strip()
                first_name = first_name.strip()

                # pad numeric fields safely
                numeric = numeric + [""] * (11 - len(numeric))

                birth_year, birth_month, birth_day = numeric[0:3]
                death_year, death_month, death_day = numeric[4:7]
                gender = numeric[7]
                notes = " ".join(numeric[8:]).strip()

                row = base + [
                    last_name,
                    first_name,
                    None,
                    birth_year,
                    birth_month,
                    birth_day,
                    None,
                    death_year,
                    death_month,
                    death_day,
                    gender,
                    notes
                ]

                person_data.append(row)

    person_df = pd.DataFrame(person_data, columns=FTT_PERSON_COLS)
    relationship_df = pd.DataFrame(relationship_data, columns=FTT_RELATIONSHIPS_COLS)

    return (person_df, relationship_df)

def date_cols_to_iso(df: pd.DataFrame, year_col: str, month_col: str, day_col: str) -> list[str]:
    dates = []
    for _, row in df.iterrows():
        try:
            if pd.notnull(row[year_col]) and pd.notnull(row[month_col]) and pd.notnull(row[day_col]):
                date = datetime.date(int(row[year_col]), int(row[month_col]), int(row[day_col]))
                dates.append(date.isoformat())
            else:
                dates.append("")
        except ValueError:
            dates.append("")
    return dates

def interim_to_gramps_dfs(person_df: pd.DataFrame, relationship_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    gramps_place_df = pd.DataFrame(columns=GRAMPS_CSV_PLACE_COLS)
    # NOTE: No current use

    # Person
    gramps_person_df = pd.DataFrame(columns=GRAMPS_CSV_PERSON_COLS)
    person_series = person_df.index.to_series().apply(lambda x: f"I{str(x).zfill(4)}")
    gramps_person_df["Person"] = person_series
    gramps_person_df["Surname"] = person_df["last_name"]
    gramps_person_df["Given"] = person_df["first_name"]
    gramps_person_df["Gender"] = person_df["gender"].map({1: "male", 2: "female"}).fillna("")
    gramps_person_df["Birth date"] = date_cols_to_iso(person_df, "birth_year", "birth_month", "birth_day")
    gramps_person_df["Death date"] = date_cols_to_iso(person_df, "death_year", "death_month", "death_day")
    gramps_person_df["Note"] = person_df["notes"]
    print(gramps_person_df.head(3))

    # Marriage
    gramps_marriage_df = pd.DataFrame(columns=GRAMPS_CSV_MARRIAGE_COLS)
    gramps_marriage_df["Marriage"] = relationship_df.index.to_series().apply(lambda x: f"F{str(x).zfill(4)}")
    # NOTE: Husband = parent_1, Wife = parent_2 (irrespective of gender)
    gramps_marriage_df["Husband"] = relationship_df["parent_1"].map(
        lambda x: f"I{str(person_df.index[person_df['person_id'] == x][0]).zfill(4)}" if x in person_df['person_id'].values else pd.NA
    )
    gramps_marriage_df["Wife"] = relationship_df["parent_2"].map(
        lambda x: f"I{str(person_df.index[person_df['person_id'] == x][0]).zfill(4)}" if x in person_df['person_id'].values else pd.NA
    )
    print(gramps_marriage_df.head(3))

    family_df = pd.DataFrame(columns=GRAMPS_CSV_FAMILY_COLS)
    for _, row in relationship_df.iterrows():
        parent_set_id = row["parent_set_id"]
        marriage_id = f"F{str(relationship_df.index[relationship_df['parent_set_id'] == parent_set_id][0]).zfill(4)}"
        children = person_df[person_df["parent_set_id"] == parent_set_id]
        for _, child_row in children.iterrows():
            child_person_id = f"I{str(person_df.index[person_df['person_id'] == child_row['person_id']][0]).zfill(4)}"
            family_df = pd.concat([family_df, pd.DataFrame({
                "Family": [marriage_id],
                "Child": [child_person_id]
            })], ignore_index=True)
    print(family_df.head(3))
    return gramps_place_df, gramps_person_df, gramps_marriage_df, family_df

def gramps_dfs_to_file(file_path: Path, 
                       gramps_place_df: pd.DataFrame, 
                       gramps_person_df: pd.DataFrame, 
                       gramps_marriage_df: pd.DataFrame, 
                       family_df: pd.DataFrame) -> None:
    dfs = [gramps_place_df, gramps_person_df, gramps_marriage_df, family_df]
    with open(file_path, 'w', encoding='utf-8') as f:
        for df in dfs:
            df.to_csv(f, index=False, encoding='utf-8')
            f.write("\n")