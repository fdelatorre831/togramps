# ToGramps

ToGramps is a conversion tool to migrate data from the [QuickFamilyTree](https://apps.apple.com/us/app/quick-family-tree/id1447075049) iOS/iPadOS application to [GrampsWeb](https://github.com/gramps-project/gramps-web), an application designed for the collaborative creation and management of genealogical family trees.

There are two reasons why such a migration is of interest:
1. `QuickFamilyTree` enables a quick way to build a family tree on a local device in a privacy-aware manner. If one used `QuickFamilyTree` prior or to speed up the generation of a tree, a conversion is needed to move to a cloud-based and collaborative management of the family tree data.
2. If one is interested in creating visualizations enabled by `GrampsWeb` from `QuickFamilyTree` data but does not wish to migrate to `GrampsWeb`, this tool can simply enable this visualization approach on a need basis.

## Usage

1. Clone this repository and install dependencies (e.g. `pip install .`)
2. Export the QuickFamilyTree and store the `.ftz` file.
3. Run the CLI `python cli.py --ftz-source <path/name.ftz>`
4. Find the resulting gramps `.csv` file by default under `output/<name.csv>`

## Example

The input [Example.ftz](./example/Example.ftz) file represent the exported family tree file by `QuickFamilyTree`. The program extracts the archive containing the person and relationship data into a [node.ftt](example/node.ftt) automatically and processes the data to map it into the Gramps csv format as seen in [Example.csv](example/Example.csv). 

<hl>

Note: Intermediary dataframes are saved into the `temp/` folder to enable overriding and correcting for possible conversion mistakes.