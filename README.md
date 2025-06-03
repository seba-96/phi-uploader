# phi-uploader
This app uploads patients, acquisitions and features to the PHI-DB database.

## Quick start

### Install 

```bash
# clone the repo
git clone https://github.com/<YOUR-ORG>/phi-uploader.git
cd phi-uploader

# create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# install in editable mode – pulls in pandas + requests automatically
pip install -U pip
pip install -e .
```

### Basic usage

```bash
# show built-in help
phi-uploader --help            # or python -m phi_uploader.cli --help

# generate Postman collections only
phi-uploader build \
    --template postman_base.json \
    --participants participants.csv \
    --dataset MyStudy

# build and upload in one go
phi-uploader run \
    --template postman_base.json \
    --participants participants.csv \
    --email alice@example.com \
    --password ********
```
## Typical 422 Error Responses

A 422 status code means the request was well-formed but contained semantic errors. Some common examples include:

- **{"error": "Remote has already been taken"}**  
  Indicates that the patient has been already uploaded.

- **{"errors": ["Missing patient for <participant_id>"]}**  
  Indicates that the patient related to the given acquisition has been not yet uploaded. First upload the patient, then the acquisition.

- **{"acquisition_type": ["has already been taken"]}**  
  Indicates that the acquisition provided for the given patient has been already uploaded. Each patient can have only one acquisition of each type.


### App Updating

To update the app, run:

```bash
git pull
pip install -e .  # re-installs only if requirements changed
```



