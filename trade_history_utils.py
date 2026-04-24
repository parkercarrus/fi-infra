from __future__ import annotations

from csv import DictReader
from datetime import datetime
from decimal import Decimal
from pathlib import Path


RELEVANT_SECURITY_TO_TICKER = {
    "APOLLO GLOBAL MGMT INC N USD 0.0001": "APO",
    "BERKSHIRE HATHAWAY INC SH B 0.0033": "BRK.B",
    "BLACKSTONE INC USD 0.00001": "BX",
    "BWX TECHNOLOGIES INC USD 0.01": "BWXT",
    "CATERPILLAR INC USD 1.0": "CAT",
    "CHEMOURS CO USD 0.01": "CC",
    "COINBASE GLOBAL INC USD 0.00001": "COIN",
    "DUTCH BROS INC USD 0.00001": "BROS",
    "GE VERNOVA INC USD 0.01": "GEV",
    "JPMORGAN CHASE + CO USD 1.0": "JPM",
    "KKR + CO INC USD 0.01": "KKR",
    "KRONOS WORLDWIDE INC USD 0.01": "KRO",
    "META PLATFORMS INC USD 0.000006": "META",
    "MICRON TECHNOLOGY INC USD 0.1": "MU",
    "MICROSOFT COM USD0.00000625": "MSFT",
    "NOBLE CORP PLC USD 0.00001": "NE",
    "NU HOLDINGS LTD/CAYMAN USD 0.000007": "NU",
    "NVIDIA CORP USD 0.001": "NVDA",
    "PVH CORP USD 1.0": "PVH",
    "RALPH LAUREN CORP USD 0.01": "RL",
    "ROBINHOOD MKTS INC USD 0.0001": "HOOD",
    "SOMNIGROUP INTERNATIONAL INC.": "SGI",
    "STATE STREET SPDR S+P 500 ETF TRUST": "SPY",
    "TESLA INC USD 0.001": "TSLA",
    "TIDEWATER INC NEW USD 0.001": "TDW",
    "WOODWARD INC USD 0.00292": "WWD",
    "ALPHABET INC CLASS C": "GOOG",
}

RELEVANT_TRANSACTION_TYPES = {"Buy", "Sell"}

TRADE_HISTORY_COLUMNS = [
    ("timestamp", "TIMESTAMP"),
    ("ticker", "VARCHAR"),
    ("num_shares", "DECIMAL(18,4)"),
    ("price", "DECIMAL(18,6)"),
]


def parse_decimal(raw_value: str) -> Decimal:
    cleaned = raw_value.strip().replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    return Decimal(cleaned or "0")


def load_relevant_trade_history(csv_path: Path) -> list[tuple[datetime, str, Decimal, Decimal]]:
    rows: list[tuple[datetime, str, Decimal, Decimal]] = []

    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = DictReader(handle)
        for row in reader:
            security_name = row["Security Name"]
            transaction_type = row["Transaction Type"]
            if security_name not in RELEVANT_SECURITY_TO_TICKER:
                continue
            if transaction_type not in RELEVANT_TRANSACTION_TYPES:
                continue

            rows.append(
                (
                    datetime.strptime(row["Trade Date"], "%m/%d/%Y"),
                    RELEVANT_SECURITY_TO_TICKER[security_name],
                    parse_decimal(row["Units"]),
                    parse_decimal(row["Price"]),
                )
            )

    rows.sort()
    return rows
