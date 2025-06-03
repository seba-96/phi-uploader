# phi-uploader 🚀
A lightweight **command-line helper** that turns your tabular data (patients / acquisitions / features) into Postman collections and, if you wish, bulk-uploads them to **PHI-DB** in a single shot.

---

## Features
* **Two sub-commands**  
  * `build` – generate JSON collections only (offline).  
  * `run`  – generate **and** `POST` them to the API (online).
* Works with **CSV, TSV or Excel** sheets.
* Strict validation of acquisition / feature types.
* Single login per session 

---

## Prerequisites
* Python ≥ 3.9 (download from [python.org](https://www.python.org/downloads/))
* `git` (download from [git-scm.com](https://git-scm.com/downloads))
* A PHI-DB account (e-mail and password) for the `run` step.

---

## Installation (5 lines)

```bash
# grab the source
git clone https://github.com/seba-96/phi-uploader.git
cd phi-uploader

# Create virtual environment (optional but recommended)
python -m venv .venv 
# Activate the virtual environment (Linux / macOS)
source .venv/bin/activate  
# for Windows run the following instead: . .venv\\Scripts\\Activate.ps1

# install in editable mode (creates the 'phi-uploader' command)
pip install -U pip
pip install -e .
```

## Usage
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

MyStudy_add_patient_API.json
MyStudy_add_acquisition_API.json
MyStudy_add_feature_API.json

### Run a collection
```bash
phi-uploader run \
    --email hello@world.it --password xxxxxx \
    --dataset MyStudy \
    --skip-build
```

| Flag              | Purpose                                                    |
| ----------------- |------------------------------------------------------------|
| `--features FILE` | table with feature rows                                    |
| `--n-test 10`     | build/upload **first 10 rows only** (for testing purposes) |
| `--skip-build`    | in `run` mode: reuse JSON already in `API/`                |

## Typical 422 errors
| JSON response                | Meaning / fix                                                                       |
|------------------------------|-------------------------------------------------------------------------------------|
| Remote has already been taken | Patient already exists in PHI-DB.                                                   |
| Missing patient for <id>     | Upload the patient **before** its acquisition.                                      |
| has already been taken       | Each patient may have only **one** acquisition per type.                            |
| Missing root folder for patient | Patient folder is missing in PHI. Check that participant_id and dataset are correct |



## Updating the tool
```bash
# if you installed in editable mode
git pull
pip install -e .
# if you installed in non-editable mode
pip install -U --force-reinstall .
```

## License
MIT — feel free to use, modify and share.

## What changed?
First release, there are no changes yet.




