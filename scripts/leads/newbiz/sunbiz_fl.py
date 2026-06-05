"""FL Sunbiz daily cor file — fetch, parse, filter.

Daily file: sftp.floridados.gov:/Public/doc/cor/yyyymmddc.txt (1440-char fixed-width).
Layout spec: https://dos.sunbiz.org/data-definitions/cor.html
Public creds (per https://dos.fl.gov/sunbiz/other-services/data-downloads/):
  Username: Public   Password: PubAccess1845!
Override with SUNBIZ_SFTP_PASS env var if the creds rotate.

LLC filing-type codes:
  FLAL  Florida Limited Liability Co.
  FORL  Foreign Limited Liability Co.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Iterator, Optional

from .ra_blocklist import is_blocklisted_ra

SFTP_HOST = "sftp.floridados.gov"
SFTP_USER = "Public"
SFTP_PASS = os.environ.get("SUNBIZ_SFTP_PASS", "PubAccess1845!")
REMOTE_DIR = "/Public/doc/cor"

# (1-indexed start, length) per cor.html.
FIELDS: dict[str, tuple[int, int]] = {
    "corp_no":     (1, 12),
    "name":        (13, 192),
    "status":      (205, 1),
    "filing_type": (206, 15),
    "addr1":       (221, 42),
    "addr2":       (263, 42),
    "city":        (305, 28),
    "state":       (333, 2),
    "zip":         (335, 10),
    "mail_addr1":  (347, 42),
    "mail_addr2":  (389, 42),
    "mail_city":   (431, 28),
    "mail_state":  (459, 2),
    "mail_zip":    (461, 10),
    "file_date":   (473, 8),
    "fei":         (481, 14),
    "ra_name":     (545, 42),
    "ra_addr":     (588, 42),
    "ra_city":     (630, 28),
    "ra_state":    (658, 2),
}

LLC_FILING_TYPES: set[str] = {"FLAL", "FORL"}
CORP_FILING_TYPES: set[str] = {"DOMP", "DOMNP"}


@dataclass
class CorRecord:
    corp_no: str
    name: str
    status: str
    filing_type: str
    addr1: str
    addr2: str
    city: str
    state: str
    zip: str
    mail_addr1: str
    mail_addr2: str
    mail_city: str
    mail_state: str
    mail_zip: str
    file_date: str  # raw MMDDYYYY from Sunbiz
    fei: str
    ra_name: str
    ra_addr: str
    ra_city: str
    ra_state: str
    source_file: str

    @property
    def file_date_ymd(self) -> Optional[str]:
        """Normalized YYYYMMDD for string compare. Sunbiz stores MMDDYYYY."""
        s = self.file_date
        if len(s) == 8 and s.isdigit():
            return f"{s[4:8]}{s[0:2]}{s[2:4]}"
        return None

    @property
    def file_date_iso(self) -> Optional[str]:
        ymd = self.file_date_ymd
        return f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}" if ymd else None

    @property
    def is_llc(self) -> bool:
        return self.filing_type in LLC_FILING_TYPES


def _slice(line: str, start: int, length: int) -> str:
    return line[start - 1 : start - 1 + length].strip()


def parse_record(line: str, source_file: str) -> CorRecord:
    return CorRecord(
        corp_no=_slice(line, *FIELDS["corp_no"]),
        name=_slice(line, *FIELDS["name"]),
        status=_slice(line, *FIELDS["status"]),
        filing_type=_slice(line, *FIELDS["filing_type"]),
        addr1=_slice(line, *FIELDS["addr1"]),
        addr2=_slice(line, *FIELDS["addr2"]),
        city=_slice(line, *FIELDS["city"]),
        state=_slice(line, *FIELDS["state"]),
        zip=_slice(line, *FIELDS["zip"]),
        mail_addr1=_slice(line, *FIELDS["mail_addr1"]),
        mail_addr2=_slice(line, *FIELDS["mail_addr2"]),
        mail_city=_slice(line, *FIELDS["mail_city"]),
        mail_state=_slice(line, *FIELDS["mail_state"]),
        mail_zip=_slice(line, *FIELDS["mail_zip"]),
        file_date=_slice(line, *FIELDS["file_date"]),
        fei=_slice(line, *FIELDS["fei"]),
        ra_name=_slice(line, *FIELDS["ra_name"]),
        ra_addr=_slice(line, *FIELDS["ra_addr"]),
        ra_city=_slice(line, *FIELDS["ra_city"]),
        ra_state=_slice(line, *FIELDS["ra_state"]),
        source_file=source_file,
    )


def iter_records(path: Path) -> Iterator[CorRecord]:
    """Yield parsed CorRecord for every well-formed line in the daily file."""
    with path.open("r", encoding="latin-1", errors="replace") as f:
        for line in f:
            if len(line.rstrip("\r\n")) < 700:
                continue
            yield parse_record(line, source_file=path.name)


def fetch_daily(d: date, out_dir: Path) -> Path:
    """SFTP-fetch one day's cor file. Cached locally; idempotent.

    Requires `sshpass` and `sftp` on PATH. Raises if the file is missing or empty.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = d.strftime("%Y%m%d") + "c.txt"
    local = out_dir / fname
    if local.exists() and local.stat().st_size > 0:
        return local
    remote = f"{REMOTE_DIR}/{fname}"
    cmd = f"get {remote} {local}\nbye\n"
    proc = subprocess.run(
        [
            "sshpass", "-p", SFTP_PASS,
            "sftp", "-oBatchMode=no", "-oStrictHostKeyChecking=accept-new",
            f"{SFTP_USER}@{SFTP_HOST}",
        ],
        input=cmd, text=True, capture_output=True, timeout=300,
    )
    if not local.exists() or local.stat().st_size == 0:
        raise RuntimeError(
            f"Sunbiz SFTP fetch failed for {fname}\n"
            f"stdout: {proc.stdout[-400:]}\nstderr: {proc.stderr[-400:]}"
        )
    return local


def filter_new_llcs(
    records: Iterable[CorRecord],
    entity_types: Optional[set[str]] = None,
    min_file_date: Optional[str] = None,
    drop_ra_trap: bool = True,
) -> Iterator[CorRecord]:
    """Yield active LLC formations within window, dropping the RA trap."""
    et = entity_types or LLC_FILING_TYPES
    for r in records:
        if r.status != "A":
            continue
        if r.filing_type not in et:
            continue
        if min_file_date:
            ymd = r.file_date_ymd
            if not ymd or ymd < min_file_date:
                continue
        if drop_ra_trap and is_blocklisted_ra(r.ra_name):
            continue
        # Sunbiz omits the principal-state field for FL formations (it's
        # implied by the source). Check addr+city+zip only.
        if not (r.addr1 and r.city and r.zip):
            continue
        yield r
