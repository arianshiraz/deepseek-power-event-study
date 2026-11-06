"""Build firm exposure measures and frozen groups (docs/classification_rule.md, v1.1).

Inputs:  EIA-860 2024 (downloaded if absent), data/classification/{firms, eia_name_map,
         eia_overrides, contract_status}.csv, data/raw/mcap_20241231.csv
Outputs: data/derived/exposure.csv          one row per firm: measures and groups
         output/tables/exposure_eia_names.csv  every EIA owner/operator name matched (audit)
"""
import re
import urllib.request
import zipfile

import numpy as np
import pandas as pd

from config import DERIVED, FIRMS, RAW, TABLES

EIA_URL = "https://www.eia.gov/electricity/data/eia860/archive/xls/eia8602024.zip"
EIA_DIR = RAW / "eia860" / "2024"
CLS = FIRMS.parent
NONUTILITY_TYPES = {"Q", "IND", "COM"}  # EIA entity types: IPP, industrial, commercial
MIN_GEN_MW = 1000  # below this owned capacity a firm is a wires utility (rule v1.1)


def ensure_eia() -> None:
    if (EIA_DIR / "3_1_Generator_Y2024.xlsx").exists():
        return
    EIA_DIR.mkdir(parents=True, exist_ok=True)
    zpath = EIA_DIR.parent / "eia8602024.zip"
    req = urllib.request.Request(EIA_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        zpath.write_bytes(r.read())
    with zipfile.ZipFile(zpath) as z:
        z.extractall(EIA_DIR)


def load_rows() -> pd.DataFrame:
    """One row per (operable generator, owner) with owned MW and a non-regulated flag."""
    gen = pd.read_excel(EIA_DIR / "3_1_Generator_Y2024.xlsx", sheet_name="Operable", header=1)
    plant = pd.read_excel(EIA_DIR / "2___Plant_Y2024.xlsx", header=1)
    own = pd.read_excel(EIA_DIR / "4___Owner_Y2024.xlsx", header=1)
    util = pd.read_excel(EIA_DIR / "1___Utility_Y2024.xlsx", header=1)

    key = ["Plant Code", "Generator ID"]
    gen = gen[gen["Plant Code"].notna() & gen["Generator ID"].notna()].copy()
    gen["MW"] = pd.to_numeric(gen["Nameplate Capacity (MW)"], errors="coerce")
    gen = gen[gen["MW"] > 0]
    gen["Plant Code"] = gen["Plant Code"].astype(int)
    gen["Generator ID"] = gen["Generator ID"].astype(str)
    gen["operator_id"] = pd.to_numeric(gen["Utility ID"], errors="coerce")
    plant = plant[plant["Plant Code"].notna()].copy()
    plant["Plant Code"] = plant["Plant Code"].astype(int)
    gen = gen.merge(plant[["Plant Code", "Regulatory Status", "Balancing Authority Code"]],
                    on="Plant Code", how="left")

    own = own[own["Plant Code"].notna() & own["Generator ID"].notna()].copy()
    own["Plant Code"] = own["Plant Code"].astype(int)
    own["Generator ID"] = own["Generator ID"].astype(str)
    own["share"] = pd.to_numeric(own["Percent Owned"], errors="coerce")
    if own["share"].max() > 1.5:
        own["share"] = own["share"] / 100
    util = util[util["Utility ID"].notna()]
    etype = dict(zip(util["Utility ID"].astype(int), util["Entity Type"]))
    own["owner_id"] = pd.to_numeric(own["Ownership ID"], errors="coerce")
    own["owner_entity_type"] = own["owner_id"].map(etype)
    own = own[key + ["Owner Name", "share", "owner_id", "owner_entity_type"]]

    g = gen[key + ["Utility Name", "Plant Name", "operator_id", "MW", "Technology",
                   "Regulatory Status", "Balancing Authority Code"]]
    with_owner = g.merge(own, on=key, how="inner")
    sole = g.merge(own[key].drop_duplicates(), on=key, how="left", indicator=True)
    sole = sole[sole["_merge"] == "left_only"].drop(columns="_merge")
    sole["Owner Name"] = sole["Utility Name"]
    sole["share"] = 1.0
    sole["owner_id"] = sole["operator_id"]
    sole["owner_entity_type"] = np.nan
    rows = pd.concat([with_owner, sole], ignore_index=True)
    rows["owned_MW"] = rows["MW"] * rows["share"]

    # Plant-level Regulatory Status follows the operator. For a share held by a co-owner
    # other than the operator, the owner's EIA entity type decides (rule v1.1).
    rows["third_party"] = rows["owner_id"].notna() & (rows["owner_id"] != rows["operator_id"]) \
        & rows["owner_entity_type"].notna()
    rows["nr"] = np.where(rows["third_party"],
                          rows["owner_entity_type"].isin(NONUTILITY_TYPES),
                          rows["Regulatory Status"] == "NR")
    return rows


def firm_rows(rows: pd.DataFrame, ticker: str, inc: str, exc: str,
              overrides: pd.DataFrame) -> pd.DataFrame:
    inc_re = re.compile(inc, re.I)
    exc_re = re.compile(exc, re.I) if exc else None
    names = pd.Series(rows["Owner Name"].dropna().unique())
    hit = names.map(lambda n: bool(inc_re.search(n)) and not (exc_re and exc_re.search(n)))
    r = rows[rows["Owner Name"].isin(set(names[hit]))].copy()
    for _, o in overrides[overrides["ticker"] == ticker].iterrows():
        m = r["Owner Name"].str.contains(o["owner_regex"], case=False, regex=True) \
            & r["Plant Name"].astype(str).str.contains(o["plant_regex"], case=False, regex=True)
        if o["action"] == "exclude":
            r = r[~m]
        elif o["action"] == "force_nr_if_third_party":
            r.loc[m & r["third_party"], "nr"] = True
    return r


def assign_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Groups under rule v1.1, plus the strict v1.0 rule for comparison."""
    contracted = df["nr_mostly_contracted"].fillna(0).astype(int) == 1
    has_util = df["has_regulated_utility"].fillna(1).astype(int) == 1
    small = df["total_mw"] < MIN_GEN_MW
    nr = df["nr_share"].fillna(0)

    v11 = np.select(
        [df["sector_type"] == "placebo",
         small,
         (nr >= 0.5) & ~contracted & ~has_util,
         nr >= 0.10],
        ["placebo", "regulated", "merchant", "hybrid"], default="regulated")
    v10 = np.select(
        [df["sector_type"] == "placebo",
         (nr >= 0.5) & ~contracted,
         nr >= 0.10],
        ["placebo", "merchant", "hybrid"], default="regulated")
    df["group"] = v11
    df["group_v10"] = v10
    return df


def main() -> None:
    ensure_eia()
    rows = load_rows()
    nmap = pd.read_csv(CLS / "eia_name_map.csv").fillna("")
    overrides = pd.read_csv(CLS / "eia_overrides.csv")

    out, audit = [], []
    for _, m in nmap.iterrows():
        r = firm_rows(rows, m["ticker"], m["include"], m["exclude"], overrides)
        total = r["owned_MW"].sum()
        nr_r = r[r["nr"]]
        out.append({
            "ticker": m["ticker"], "total_mw": total, "nr_mw": nr_r["owned_MW"].sum(),
            "pjm_ercot_mw": r.loc[r["Balancing Authority Code"].isin(["PJM", "ERCO"]),
                                  "owned_MW"].sum(),
            "nuclear_mw": r.loc[r["Technology"].str.contains("Nuclear", case=False, na=False),
                                "owned_MW"].sum(),
        })
        for n, mw in r.groupby("Owner Name")["owned_MW"].sum().sort_values(ascending=False).items():
            audit.append({"ticker": m["ticker"], "owner_or_operator_name": n, "owned_mw": mw})

    exp = pd.DataFrame(out)
    firms = pd.read_csv(FIRMS)
    mcap = pd.read_csv(RAW / "mcap_20241231.csv")[["ticker", "mcap_bn"]]
    cs = pd.read_csv(CLS / "contract_status.csv")[["ticker", "has_regulated_utility",
                                                    "nr_mostly_contracted"]]
    df = firms.merge(exp, on="ticker", how="left").merge(mcap, on="ticker", how="left") \
        .merge(cs, on="ticker", how="left")
    for c in ["total_mw", "nr_mw", "pjm_ercot_mw", "nuclear_mw"]:
        df[c] = df[c].fillna(0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        df["nr_share"] = df["nr_mw"] / df["total_mw"]
        df["pjm_ercot_share"] = df["pjm_ercot_mw"] / df["total_mw"]
        df["nuclear_share"] = df["nuclear_mw"] / df["total_mw"]
    df["nr_mw_per_bn"] = df["nr_mw"] / df["mcap_bn"]
    uncontracted = df["nr_mostly_contracted"].fillna(0).astype(int) == 0
    # Primary continuous exposure: uncontracted non-regulated MW per $bn of equity value.
    df["merchant_mw_per_bn"] = np.where(uncontracted, df["nr_mw_per_bn"], 0.0)
    df = assign_groups(df)

    DERIVED.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(DERIVED / "exposure.csv", index=False, float_format="%.4f")
    pd.DataFrame(audit).to_csv(TABLES / "exposure_eia_names.csv", index=False, float_format="%.1f")

    cols = ["ticker", "group_prelim", "group_v10", "group", "total_mw", "nr_share",
            "mcap_bn", "nr_mw_per_bn", "merchant_mw_per_bn", "pjm_ercot_share", "nuclear_share"]
    with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
        print(df[cols].sort_values("nr_mw_per_bn", ascending=False).to_string(index=False))
    changed = df[df["group"] != df["group_prelim"]]
    print("\nGroup changes vs preliminary:", changed[["ticker", "group_prelim", "group"]]
          .to_dict("records"))


if __name__ == "__main__":
    main()
