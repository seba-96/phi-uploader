# phi-uploader 🚀
A lightweight **command-line helper** that turns your tabular data (patients / acquisitions / features) into Postman collections and, if you wish, uploads them to **PHI-DB** in a single shot.

---

## Features
* **Two sub-commands**  
  * `build` – generate JSON collections only (offline).  
  * `run`  – generate **and** `POST` them to the API (online).
* Strict validation of imaging acquisition and feature types according to EBRAINS Data Management Plan.
* Single login per session

---

## Installation

First install docker if you don't have it already (https://docs.docker.com/get-docker/)
Then, you can install (or update, if it is already installed) the phi-uploader tool by opening a terminal and running the following commands:

```bash
# first change the directory where the participants.tsv and acquisitions.tsv files are stored
cd /path/to/your/data
docker build -t phi-uploader:latest https://github.com/seba-96/phi-uploader.git
```

## Usage
### Setup
Open the docker application and run the following commands to build and run the collection.

#### Build a collection
For linux/macOS
```bash
docker run --rm -it -v "$PWD":/work -w /work phi-uploader:latest build --behavioral --clinical --dataset MyStudy 
```
For Windows (PowerShell)
```bash
docker run --rm -it -v ${PWD}:/work -w /work phi-uploader:latest build --behavioral --clinical --dataset MyStudy 
```
This will generate the following files in ./API/ depending on the input files:
- MyStudy_add_patient_API.json
- MyStudy_add_acquisition_API.json
- MyStudy_add_feature_API.json

### Run a collection
For linux/macOS
```bash
docker run --rm -it -v "$PWD":/work -w /work phi-uploader:latest run --dataset MyStudy --email hello@world.it 
```
For Windows (PowerShell)
```bash
docker run --rm -it -v ${PWD}:/work -w /work phi-uploader:latest run --dataset MyStudy --email hello@world.it 
```


### CLI Common Flags (used by both commands build and run)

| Flag              | Description                                                                         | Default                        |
| ----------------- | ----------------------------------------------------------------------------------- |--------------------------------|
| `--template`      | Path to the Postman JSON template.                                                | `template/postman.json`        |
| `--dataset`       | Dataset name (used in output file names).                                          | `WashU`                        |
| `--root`          | Root directory for generated files.                                               | `.`  (i.e., current directory) |
| `--n-test N`      | Only generate the first N rows (for debugging/testing purposes).                    | None (optional)                |

### CLI Flags for the `build` Command

| Flag              | Description                                                                             | Default/Required        |
| ----------------- |-----------------------------------------------------------------------------------------| ----------------------- |
| `--patient`       | CSV/TSV/XLSX file with participant data.                                                | participants.tsv                |
| `--acquisition`   | CSV/TSV/XLSX file with acquisitions data.                                               | acquisitions.tsv                |
| `--feature`       | CSV/TSV/XLSX file with features data.                                                   | Optional                |
| `--behavioral`    | When behavioral information is present in the participants.tsv, set the behavioral flag | Default: False          |
| `--clinical`      | When clinical information is present in the participants.tsv, set the clinical flag     | Default: False          |

### CLI Flags for the `run` Command

| Flag              | Description                                                                                                       | Default/Required                              |
| ----------------- |-------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| `--patient`       | Optional CSV/TSV/XLSX file with participant data (if not skipping the build, used to generate JSON collections).  | participants.tsv                                      |
| `--acquisition`   | Optional CSV/TSV/XLSX file with acquisitions data (if not skipping the build, used to generate JSON collections). | acquisitions.tsv                                      |
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
| FileNotFoundError: participants.tsv                                      | Change the directory to where the participants.tsv file is stored                    |


## What changed?
First release, there are no changes yet.




