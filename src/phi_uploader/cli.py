#!/usr/bin/env python3
r"""phi_uploader.py
========================================

Usage examples are present in the README.md file.

"""




from __future__ import annotations

import argparse
import getpass
import json
import logging
import sys
import time
from pathlib import Path
from importlib import resources  # std-lib 3.9+
from typing import Dict, List, TypedDict, Any, Final, Iterable

import pandas as pd
import requests
import typing as t

LOGGER = logging.getLogger(__name__)
_DEFAULT_BASE_URL: Final[str] = "https://phidb.pnc.unipd.it/api/v1"

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------
class RequiredFields(TypedDict):
    patient: List[str]
    acquisition: List[str]
    feature: List[str]


REQUIRED: Final[RequiredFields] = RequiredFields(
    patient=[
        "disease_id",
        "center_id",
        "data_id",
        "remote_id",
        "dataset",
        "disease_notes",
        "education",
        "sex",
        "clinical",
        "behavioral",
    ],
    acquisition=[
        "remote_id",
        "acquisition_type",
        "general_comments",
        "head_coil",
        "tesla_field",
        "manufacturer",
        "machine",
        "resolution_acquis",
        "resolution_recon",
        "resolution_x",
        "resolution_y",
        "resolution_z",
        "time_repetition",
        "echo_time",
        "flip_angle",
        "bval",
        "bval_bin",
        "bvecs_num",
        "vol_num",
        "acquisition_plan",
        "injec_info",
    ],
    feature=[
        "remote_id",
        "feature_type",
    ],
)

VALID_ACQ_TYPES: Final[set[str]] = {
    "fMRI_rest",
    "perf",
    "T2w",
    "UTE",
    "DIXON",
    "hdeeg",
    "pet",
    "T1w",
    "T1w_pre",
    "lesion",
    "Flair",
    "T1w_wca",
    "dMRI",
    "fMRI_task",
    "TOF",
    "tof",
    "SWI",
    "SE",
    "PCM"
}

VALID_FEATURE_TYPES: Final[set[str]] = {
    "dwi",
    "anat",
    "lesion",
    "pet",
    "eeg",
    "func",
    "perf",
}

ID_COLUMNS: Final[tuple[str, ...]] = ("participant_id", "remote_id", "data_id")

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _read_table(path: str | Path | None, string_cols: Iterable[str] | None = None) -> pd.DataFrame | None:
    """Open *path* (csv/tsv/xlsx) to a :class:`pandas.DataFrame`.

    Returns ``None`` if *path* is ``None``. Raises ``FileNotFoundError`` or
    ``ValueError`` for unsupported extensions.
    """
    if path is None:
        return None

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    string_cols = tuple(dict.fromkeys(string_cols or ()))

    def _select_converters(
        reader: t.Callable[..., pd.DataFrame],
        *,
        kwargs: dict[str, Any],
    ) -> dict[str, t.Callable[[Any], str | None]]:
        if not string_cols:
            return {}
        header_kwargs = {**kwargs, "nrows": 0}
        try:
            header_df = reader(path, **header_kwargs)
            available = set(header_df.columns)
        except Exception:
            available = set(string_cols)
        return {col: _coerce_raw_string for col in string_cols if col in available}

    if path.suffix == ".csv":
        kwargs = {"sep": ","}
        converters = _select_converters(pd.read_csv, kwargs=kwargs)
        return pd.read_csv(path, converters=converters or None, **kwargs)
    if path.suffix == ".tsv":
        kwargs = {"sep": "\t"}
        converters = _select_converters(pd.read_csv, kwargs=kwargs)
        return pd.read_csv(path, converters=converters or None, **kwargs)
    if path.suffix in (".xls", ".xlsx"):
        kwargs: dict[str, Any] = {}
        converters = _select_converters(pd.read_excel, kwargs=kwargs)
        return pd.read_excel(path, converters=converters or None, **kwargs)

    raise ValueError(f"Unsupported table format: {path.suffix}")


def _ensure_columns(df: pd.DataFrame, required: Iterable[str]) -> pd.DataFrame:
    """Add *required* columns missing from *df* (filled with ``None``)."""
    for col in required:
        if col not in df.columns:
            LOGGER.warning("Adding missing column: %s", col)
            df[col] = None
    return df[list(required)]


def _fill_nans(obj: dict[str, Any]) -> dict[str, Any]:
    """Replace NaNs in *obj* **in‑place** with ``None`` and return it."""
    for k, v in obj.items():
        if isinstance(v, float) and pd.isna(v):
            obj[k] = None
    return obj


def _stringify_ids(obj: dict[str, Any]) -> dict[str, Any]:
    for field in ("data_id", "remote_id"):
        value = obj.get(field)
        if value is not None and not isinstance(value, str):
            obj[field] = str(value)
    return obj


def _coerce_raw_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    return str(value)


# ---------------------------------------------------------------------------
# Postman collection generation
# ---------------------------------------------------------------------------

def _load_postman_template(template_path: str | Path, item_name: str) -> dict:
    """Return a deep copy of *item_name* from an existing Postman collection."""
    collection = json.loads(Path(template_path).read_text(encoding="utf-8"))
    for it in collection.get("item", []):
        if it.get("name") == item_name:
            return it  # shallow copy is fine – we deepcopy later
    raise ValueError(f"{item_name!r} not found in {template_path}")


def _build_collection(
    payloads: pd.DataFrame,
    template_item: dict,
    login_snippet: dict,
    out_path: str | Path,
    n_rows: int | None = None,
) -> None:
    """Write a Postman collection to *out_path*.

    Each row of *payloads* becomes a copy of *template_item* with its
    ``body.raw`` replaced.
    """
    if n_rows:
        LOGGER.info("Building collection with only %d rows (testing purpose)", n_rows)
    n = int(n_rows or len(payloads))
    collection: dict = {"item": [json.loads(json.dumps(template_item)) for _ in range(n)]}

    for idx, row in payloads.iloc[:n].iterrows():
        body = _fill_nans(row.to_dict())
        body = _stringify_ids(body)
        collection["item"][idx]["request"]["body"]["raw"] = json.dumps(body, indent=4)

    collection["item"].append(login_snippet)
    Path(out_path).write_text(json.dumps(collection, indent=4), encoding="utf-8")
    LOGGER.info("Wrote %s", out_path)


# ---------------------------------------------------------------------------
# Authentication & upload
# ---------------------------------------------------------------------------

def get_authenticated_session(
    email: str,
    password: str,
    base_url: str = _DEFAULT_BASE_URL,
    *,
    verify_tls: bool | str = True,
    timeout: int = 30,
) -> requests.Session:
    """Return a :pyclass:`requests.Session` with the *Authorization* header set."""
    sess = requests.Session()
    resp = sess.post(
        f"{base_url}/auth/sign_in",
        json={"email": email, "password": password},
        timeout=timeout,
        verify=verify_tls,
    )
    resp.raise_for_status()
    token = resp.headers.get("Authorization")
    if not token:
        raise RuntimeError("Login ok but no Authorization header!")
    sess.headers.update({
        "Authorization": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    return sess


def bulk_upload(
    sess: requests.Session,
    url: str,
    payloads: list[dict[str, t.Any]],
    *,
    max_retries: int = 3,
    base_backoff: int = 2,
) -> list[dict[str, t.Any]]:
    """
    POST each payload to *endpoint*. Returns a tiny per-record summary.
    """
    res: list[dict[str, t.Any]] = []
    for pl in payloads:
        remote_id = pl.get("remote_id")
        acq_type = pl.get("acquisition_type")
        feat_type = pl.get("feature_type")

        LOGGER.debug(
            "Uploading payload ‒ remote_id=%s, acquisition_type=%s, feature_type=%s",
            remote_id,
            acq_type,
            feat_type,
        )

        try:
            attempt = 0
            while True:
                r = sess.post(url, json=pl)
                # Retry on “Too Many Requests”
                if r.status_code != 429 or attempt >= max_retries:
                    break

                retry_after = r.headers.get("Retry-After")
                wait = int(retry_after) if retry_after else base_backoff**attempt
                attempt += 1
                LOGGER.warning(
                    "429 received (remote_id=%s) – retrying in %s s (attempt %d/%d)",
                    remote_id,
                    wait,
                    attempt,
                    max_retries,
                )
                time.sleep(wait)

            ok = r.status_code in (200, 201)

            # Try to read the server feedback – it usually helps understanding 4xx / 5xx errors
            try:
                body = r.json()
            except ValueError:
                body = r.text

            if not ok:
                LOGGER.error(
                    "Upload failed ‒ remote_id=%s, acquisition_type=%s, "
                    "feature_type=%s ‒ HTTP %s ‒ %s",
                    remote_id,
                    acq_type,
                    feat_type,
                    r.status_code,
                    body,
                )
            else:
                LOGGER.info(
                    "Successful uploading ‒ remote_id=%s, acquisition_type=%s, "
                    "feature_type=%s ‒ HTTP %s",
                    remote_id,
                    acq_type,
                    feat_type,
                    r.status_code,
                )

            res.append(
                {
                    "ok": ok,
                    "status": r.status_code,
                    "body": body,
                    "remote_id": remote_id,
                    "acquisition_type": acq_type,
                    "feature_type": feat_type,
                }
            )
        except Exception as exc:  # pragma: no cover
            LOGGER.error(
                "Unexpected error while uploading remote_id=%s: %s",
                remote_id,
                exc,
                exc_info=True,
            )
            res.append(
                {
                    "ok": False,
                    "status": None,
                    "body": str(exc),
                    "remote_id": remote_id,
                    "acquisition_type": acq_type,
                    "feature_type": feat_type,
                }
            )
    return res


# ---------------------------------------------------------------------------
# CLI layer
# ---------------------------------------------------------------------------

def _add_common_io_args(p: argparse.ArgumentParser) -> None:

    p.add_argument("--template", default=str(resources.files("phi_uploader").joinpath("template/postman.json")), help="Path to Postman JSON template")
    p.add_argument("--dataset", default="MyDataset", help="Dataset name (used in output file names)")
    p.add_argument("--root", default=".", help="Root directory for generated files")
    p.add_argument("--n-test", type=int, metavar="N", help="Only generate the first N rows (debug)")
    p.add_argument("--five-m", dest="patient_5m", action="store_true", help="Use the 'Add patient 5M' Postman item for patient uploads")


# Build sub‑command ---------------------------------------------------------

def cli_build(argv: list[str]) -> None:
    ap = argparse.ArgumentParser("build", description="Generate Postman collections only.")
    _add_common_io_args(ap)
    ap.add_argument("--patient", default='participants.tsv', help="CSV/TSV/XLSX with participant data")
    ap.add_argument("--acquisition", default='acquisitions.tsv', help="CSV/TSV/XLSX with acquisitions data")
    ap.add_argument("--feature", help="CSV/TSV/XLSX with features data")
    ap.add_argument("--behavioral", default=False, action="store_true")
    ap.add_argument("--clinical", default=False, action="store_true")
    ns = ap.parse_args(argv)

    patient_item_name = "Add patient 5M" if ns.patient_5m else "Add patient"

    # Load login snippet + reusable templates ---------------------------
    template_path = ns.template
    root = Path(ns.root).resolve()
    api_dir = root / "API"
    api_dir.mkdir(parents=True, exist_ok=True)

    with open(template_path, encoding="utf-8") as f:
        full_template = json.load(f)
    login_snippet = [it for it in full_template["item"] if it["name"] == "Login"][-1]

    patient_df = _read_table(ns.patient, string_cols=ID_COLUMNS)
    acquisition_df = _read_table(ns.acquisition, string_cols=ID_COLUMNS)
    feature_df = _read_table(ns.feature, string_cols=ID_COLUMNS)

    # Helper to process each entity ------------------------------------
    def _process(
        kind: str,
        df: pd.DataFrame | None,
        *,
        valid_types: set[str] | None = None,
        item_name: str | None = None,
        template_source_name: str | None = None,
    ):
        if df is None or df.empty:
            return
        LOGGER.info("%s rows in %s", len(df), kind)
        req = REQUIRED[kind]  # type: ignore[index]
        if kind == "patient":
            if ns.behavioral:
                df["behavioral"] = True
            if ns.clinical:
                df["clinical"] = True
            df["remote_id"] = df.get("participant_id")
            df["data_id"] = df.get("participant_id")
        elif kind in ("acquisition", "feature"):
            df["remote_id"] = df.get("participant_id")
        if valid_types:
            if kind == 'acquisition':
                invalid = set(df['acquisition_type'].unique()) - valid_types
            elif kind == 'feature':
                invalid = set(df['feature_type'].unique()) - valid_types
            else:
                invalid = set()
            if invalid:
                raise ValueError(f"Invalid {kind} types: {sorted(invalid)}")
        df = _ensure_columns(df, req)
        outfile = api_dir / f"{ns.dataset}_add_{kind}_API.json"
        template_source = template_source_name or f"Add {kind}"
        target_name = item_name or template_source
        tmpl = _load_postman_template(template_path, template_source)
        if target_name != tmpl.get("name"):
            tmpl = json.loads(json.dumps(tmpl))
            tmpl["name"] = target_name
        _build_collection(df, tmpl, login_snippet, outfile, ns.n_test)

    _process(
        "patient",
        patient_df,
        item_name=patient_item_name,
        template_source_name="Add patient",
    )
    _process("acquisition", acquisition_df, valid_types=VALID_ACQ_TYPES)
    _process("feature", feature_df, valid_types=VALID_FEATURE_TYPES)


# Run (=build+upload) sub‑command -----------------------------------------

def cli_run(argv: list[str]) -> None:
    ap = argparse.ArgumentParser("run", description="Build collections AND upload them.")
    _add_common_io_args(ap)
    ap.add_argument("--patient")
    ap.add_argument("--acquisition")
    ap.add_argument("--feature")
    ap.add_argument("--email", required=True, help="API login email")
    ap.add_argument("--password", help="API login password")
    ap.add_argument("--base-url", default=_DEFAULT_BASE_URL)
    ap.add_argument("--skip-build", default=True, action="store_true", help="Assume JSON collections already exist under --root/API")
    ap.add_argument("--retry-failed", default=False, action="store_true", help="(Re)upload only collections stored in API/not_uploaded")
    ns = ap.parse_args(argv)
    patient_item_name = "Add patient 5M" if ns.patient_5m else "Add patient"

    if ns.password is None:
        ns.password = getpass.getpass("Enter PHI-DB password: ")

    if not ns.skip_build:
        args_for_build = [
            "--template", ns.template,
            "--dataset", ns.dataset,
            "--root", ns.root,
        ]
        if ns.patient:
            args_for_build += ["--patient", ns.patient]
        if ns.acquisition:
            args_for_build += ["--acquisition", ns.acquisition]
        if ns.feature:
            args_for_build += ["--feature", ns.feature]
        if ns.patient_5m:
            args_for_build += ["--five-m"]
        cli_build(args_for_build)  # type: ignore[arg-type]

    root = Path(ns.root).resolve()
    api_dir = root / "API"
    source_dir = api_dir / "not_uploaded" if ns.retry_failed else api_dir

    sess = get_authenticated_session(ns.email, ns.password, base_url=ns.base_url)

    def _upload(kind: str, endpoint: str, src: Path, item_name: str):
        f = src / f"{ns.dataset}_add_{kind}_API.json"
        if not f.exists():
            LOGGER.warning("%s not found, skipping %s", f, kind)
            return
        payloads = load_payloads(f, item_name)
        for p in payloads:
            LOGGER.debug(
                "Prepared %s payload ‒ remote_id=%s, acquisition_type=%s, feature_type=%s",
                kind,
                p.get("remote_id"),
                p.get("acquisition_type"),
                p.get("feature_type"),
            )

        LOGGER.info("Uploading %d %s …", len(payloads), kind)
        res = bulk_upload(sess, f"{ns.base_url}/{endpoint}", payloads)
        ok = sum(r["ok"] for r in res)  # type: ignore[arg-type]
        LOGGER.info("%s/%s %s uploaded ok", ok, len(res), kind)

        # Set paths for TSV summaries and JSON for failed uploads
        uploaded_dir: Path = f.parent.parent / "uploaded" if f.parent.name in ["uploaded", "not_uploaded"] else f.parent / "uploaded"
        not_uploaded_dir: Path = f.parent.parent / "not_uploaded" if f.parent.name in ["uploaded", "not_uploaded"] else f.parent / "not_uploaded"
        uploaded_dir.mkdir(exist_ok=True, parents=True)
        not_uploaded_dir.mkdir(exist_ok=True, parents=True)

        succ_payloads = [pl for pl, r in zip(payloads, res, strict=False) if r["ok"]]
        fail_payloads = [pl for pl, r in zip(payloads, res, strict=False) if not r["ok"]]

        def _basename() -> str:
            if kind == "patient":
                return "participants"
            if kind == "acquisition":
                return "acquisitions"
            return "features"

        # Function to update TSV file by appending new rows to any existing ones
        def update_tsv(folder: Path, label: str, new_rows: list[dict[str, t.Any]]) -> None:
            tsv_path = folder / f"{_basename()}_{label}.tsv"
            df_new = pd.DataFrame(new_rows)
            if tsv_path.exists():
                try:
                    df_old = pd.read_csv(tsv_path, sep="\t")
                    df_merged = pd.concat([df_old, df_new], ignore_index=True)
                except Exception:
                    df_merged = df_new
            else:
                df_merged = df_new
            try:
                df_merged.to_csv(tsv_path, sep="\t", index=False)
            except Exception as exc:  # pragma: no cover
                LOGGER.error("Could not write TSV summary %s: %s", tsv_path, exc)

        if succ_payloads:
            update_tsv(uploaded_dir, "uploaded", succ_payloads)
        if fail_payloads:
            # Write TSV summary for failed payloads (this will replace any existing file)
            pd.DataFrame(fail_payloads).to_csv(not_uploaded_dir / f"{_basename()}_not_uploaded.tsv", sep="\t", index=False)
            # Write JSON collection for failed payloads (replacing any existing file)
            col_path = not_uploaded_dir / f"{ns.dataset}_add_{kind}_API.json"
            try:
                col_json = [{
                    "name": item_name,
                    "request": {
                        "method": "POST",
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps(_stringify_ids(pl), indent=4),
                        },
                    },
                } for pl in fail_payloads]
                col_obj = {"item": col_json}
                col_path.write_text(json.dumps(col_obj, indent=4), encoding="utf-8")
            except Exception as exc:  # pragma: no cover
                LOGGER.error("Could not write collection %s: %s", col_path, exc)

    _upload("patient", "patients", source_dir, patient_item_name)
    _upload("acquisition", "imaging_acquisitions", source_dir, "Add acquisition")
    _upload("feature", "features", source_dir, "Add feature")


# Utility extracted from legacy script -------------------------------------

def load_payloads(collection_path: str | Path, item_name: str) -> List[Dict[str, Any]]:
    col = json.loads(Path(collection_path).read_text(encoding="utf-8"))
    out: List[Dict[str, Any]] = []
    for it in col.get("item", []):
        if it.get("name") == item_name and it["request"]["body"]["mode"] == "raw":
            out.append(json.loads(it["request"]["body"]["raw"]))
    if not out:
        raise ValueError(f"{item_name!r} not found in {collection_path}")
    return out


# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    argv = argv or sys.argv[1:]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        print("\nCommands: build, run")
        sys.exit(0)

    cmd, *rest = argv
    if cmd == "build":
        cli_build(rest)
    elif cmd == "run":
        cli_run(rest)
    else:
        sys.exit(f"Unknown command: {cmd}\nUse --help for usage.")


if __name__ == "__main__":
    main()
