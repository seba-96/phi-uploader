# phi-uploader 🚀
A lightweight **command-line helper** that turns your tabular data (patients / acquisitions / features) into Postman collections and, if you wish, uploads them to **PHI-DB** in a single shot.

---

## Features
* **Two sub-commands**  
  * `build` – generate JSON collections only (offline).  
  * `run`  – generate **and** `POST` them to the API (online).
* Works with **CSV, TSV or Excel** sheets.
* Strict validation of imaging acquisition and feature types according to EBRAINS Data Management Plan.
* Single login per session 

---

## Prerequisites
* Python ≥ 3.9 (download from [python.org](https://www.python.org/downloads/))
* `git` (download from [git-scm.com](https://git-scm.com/downloads))
* A PHI-DB account (e-mail and password) for the `run` step.

---

## Installation

```bash
# grab the source
git clone https://github.com/seba-96/phi-uploader.git
cd phi-uploader

# Create a virtual environment (optional but recommended)
python -m venv .venv 
# Activate the virtual environment (Linux / macOS)
source .venv/bin/activate  
# for Windows run the following instead: . .venv\\Scripts\\Activate.ps1

# install in editable mode (creates the 'phi-uploader' command)
pip install -U pip
pip install -e .
```

## Usage
### Setup
```bash
# Change to the directory where you cloned the repository
cd phi-uploader
# activate the virtual environment if you created one
source .venv/bin/activate  # Linux / macOS
# for Windows run the following instead: . .venv\\Scripts\\Activate.ps1
```
### Show help
```bash
phi-uploader --help
```
### Build a collection
```bash
phi-uploader build \
    --patient participants.tsv \
    --acquisition acquisitions.tsv \
    --dataset MyStudy \
    --behavioral --clinical
```
This will generate the following files in ./API/ depending on the input files:
- MyStudy_add_patient_API.json
- MyStudy_add_acquisition_API.json
- MyStudy_add_feature_API.json

### Run a collection
```bash
phi-uploader run \
    --email hello@world.it \
    --dataset MyStudy \
    --skip-build
```


### CLI Common Flags (used by both commands build and run)

| Flag              | Description                                                                         | Default                        |
| ----------------- | ----------------------------------------------------------------------------------- |--------------------------------|
| `--template`      | Path to the Postman JSON template.                                                | `template/postman.json`        |
| `--dataset`       | Dataset name (used in output file names).                                          | `WashU`                        |
| `--root`          | Root directory for generated files.                                               | `.`  (i.e., current directory) |
| `--n-test N`      | Only generate the first N rows (for debugging/testing purposes).                    | None (optional)                |

### CLI Flags for the `build` Command

| Flag              | Description                                                                         | Default/Required        |
| ----------------- | ----------------------------------------------------------------------------------- | ----------------------- |
| `--patient`       | CSV/TSV/XLSX file with participant data.                                            | Optional                |
| `--acquisition`   | CSV/TSV/XLSX file with acquisitions data.                                           | Optional                |
| `--feature`       | CSV/TSV/XLSX file with features data.                                               | Optional                |
| `--behavioral`    | When present, set the behavioral flag                          | Default: False          |
| `--clinical`      | When present, set the clinical flag                           | Default: False          |

### CLI Flags for the `run` Command

| Flag              | Description                                                                                                       | Default/Required                              |
| ----------------- |-------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| `--patient`       | Optional CSV/TSV/XLSX file with participant data (if not skipping the build, used to generate JSON collections).  | Optional                                      |
| `--acquisition`   | Optional CSV/TSV/XLSX file with acquisitions data (if not skipping the build, used to generate JSON collections). | Optional                                      |
| `--feature`       | Optional CSV/TSV/XLSX file with features data (if not skipping the build, used to generate JSON collections).     | Optional                                      |
| `--email`         | PHI-DB login email used for authentication.                                                                       | Required                                      |
| `--password`      | PHI-DB login password used for authentication.                                                                    | Optional (can be entered later when prompted) |
| `--base-url`      | Base URL for the API                                                                                              | Defined already by the tool                   |
| `--skip-build`    | When present, skips building JSON collections and uses those already available in the `API/` folder.              | Default: True                                 |
| `--retry-failed`  | When present, (re)uploads only collections in `API/not_uploaded` and overwrites their TSV/JSON summaries.         | Default: False                                |


## Typical errors
| Error                                 | Meaning / fix                                                                        |
|---------------------------------------|--------------------------------------------------------------------------------------|
| Remote has already been taken         | Patient already exists in PHI-DB.                                                    |
| Missing patient for id                | Upload the patient **before** its acquisition.                                       |
| Has already been taken                | Each patient may have only **one** acquisition/feature per type.                     |
| Missing root folder for patient       | Patient folder is missing in PHI. Check that participant_id and dataset are correct. |
| Client Error: Unauthorized for url    | Either email or password for accessing PHI-DB are incorrect                          |
| Missing files for type of acquisition | Files are missing for the given acquisition type. Check patient folder in PHI        |
| Wrong feature type                    | Check valid feature types in EBRAINS Data Management Plan                            |



## Updating the tool
```bash
# if you installed in editable mode
git pull
python -m pip install -e .
# if you installed in non-editable mode
python -m pip install -U --force-reinstall .
```

## License
MIT — feel free to use, modify and share.

## What changed?
First release, there are no changes yet.




