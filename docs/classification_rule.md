# Firm classification rule (v1.1, frozen 6 November 2026)

Written on 6 November 2026, before computing any firm's exposure measures.

**Disclosure.** The preliminary event-day returns (run of 5 November 2026) had already been seen when this rule was written. To limit the room this leaves for choosing groups after seeing the results:
1. Group assignment follows mechanically from the measures below, using thresholds fixed here.
2. The main cross-sectional test uses the **continuous** exposure measure, not the groups, so the thresholds are not load-bearing.
3. Any firm whose group differs from the preliminary list is reported, together with results under both versions.

## Primary measure: non-regulated capacity share (NR share)

For each firm, NR share is the share of its operable nameplate capacity (MW, owned share) at plants that EIA-860 records as non-regulated (`Regulatory Status = NR`). The data are EIA-860 for 2024, the status as of 31 December 2024, the last year-end before the event.

- **Ownership.** Where a generator appears in EIA-860 Schedule 4 (Owner), the firm's share is its `Percent Owned`. Otherwise the operator is treated as the 100% owner.
- **Parent mapping.** Operator and owner names are mapped to listed parents by regular expressions in `data/classification/eia_name_map.csv`, with explicit exclusions (for example, NRG Yield and NRG Renew assets belong to Clearway, not NRG).

## Secondary measures (same data)

| Measure | Definition |
|---|---|
| `pjm_ercot_share` | Share of owned capacity in the PJM or ERCOT balancing authorities |
| `nuclear_share` | Share of owned capacity that is nuclear |
| `nr_mw`, `total_mw` | Levels, for reference |

## Contract adjustment (10-K)

NR share measures exposure to markets rather than to cost-of-service rates. Non-regulated capacity sold under long-term contracts is largely insulated from short-run news about prices. For every firm with NR share ≥ 10%, the latest 10-K before the event (fiscal year 2024, or 2023 if the 2024 filing came after 27 January 2025) is checked for how much of its non-regulated capacity or margin is contracted. The finding is recorded with a quotation reference in `firms.csv`.

## Group thresholds (fixed)

| Group | Rule |
|---|---|
| merchant | NR share ≥ 50% **and** the 10-K indicates that most non-regulated capacity is not under long-term contract |
| hybrid | NR share ≥ 10% and the firm is not merchant (this includes mostly contracted non-regulated fleets) |
| regulated | NR share < 10% |
| placebo | No electricity generation or electric distribution business (water and gas utilities) |

## Amendments in v1.1 (6 November 2026)

These were made after the EIA measures were computed but before the event study was re-run on them. Each fixes a measurement problem visible in the EIA data, not in the returns. Results under the strict v1.0 rule are reported alongside.

1. **Co-owned plants.** EIA's `Regulatory Status` is a plant-level label that follows the operator. A regulated utility's stake in a plant run by an IPP (for example, Avista's and NorthWestern's shares of Colstrip, which Talen operates) was therefore counted as non-regulated. Now, for a share held by a co-owner other than the operator, the owner's EIA entity type decides: IPP, industrial or commercial means non-regulated. Otherwise the plant label is used.
2. **Stale EIA owner names.** Assets sold before 2024 but still listed under the old owner name are excluded or reassigned (`data/classification/eia_name_map.csv` and `eia_overrides.csv`): Con Edison's clean-energy businesses (sold to RWE), Duke Energy Renewables (sold to Brookfield), AEP's OnSite Partners and AEP Renewables, and PSEG's Keys plant. PSEG's stakes listed under "Public Service Elec & Gas" in plants it does not operate (for example, Peach Bottom) belong to PSEG Power and are set to non-regulated. Each of these needs a sale date confirmed.
3. **Wires-only utilities.** Firms owning under 1,000 MW of generation (Exelon, Eversource, CenterPoint, Con Edison, Sempra) are classified regulated whatever their NR share. Their NR share comes from a few MW and carries no information.
4. **Merchant requires no cost-of-service utility.** Under v1.0, PSEG (98% of owned generation non-regulated) would be merchant, but most of its equity value is the regulated PSE&G utility. Generation capacity share ignores firm value. That is why the **primary continuous measure is now uncontracted non-regulated MW per $bn of equity market value** (31 Dec 2024), `merchant_mw_per_bn`. Under v1.1 PSEG is hybrid. The v1.0 version (PSEG merchant) is reported as `group_v10`.
5. **Contract adjustment as a binary flag.** `merchant_mw_per_bn` is set to zero where the evidence (`contract_status.csv`) says the non-regulated fleet is mostly under long-term contract. The unadjusted `nr_mw_per_bn` is reported too.

## Result of the freeze

| Firm | Preliminary group | v1.1 group | Reason |
|---|---|---|---|
| SO | regulated | hybrid | Southern Power: 8.2 GW non-regulated, mostly contracted |
| D | regulated | hybrid | Millstone and Dominion Renewable: 3.2 GW, mostly contracted |
| BKH | regulated | hybrid | 0.34 GW non-regulated IPP subsidiaries, contracted to affiliates |
| PEG | hybrid | hybrid (v1.0: merchant) | See amendment 4 |

The four merchants (CEG, VST, NRG, TLN) and the placebo group are unchanged.

## Known limits

- **Name mapping misses some assets.** Project-company names that do not reveal the parent are missed, so NR share for developers with many project LLCs (NextEra Energy Resources, AES) is a lower bound. Vistra is the largest known gap: EIA mapping finds about 26 GW against roughly 41 GW in company materials (to verify), so its intensity is understated.
- **Contract evidence is incomplete.** Most entries in `contract_status.csv` come from search summaries of 10-Ks, not full reads, and are marked `partial` or `no`. Reading the FY2023 10-K passages is the remaining verification step.
- **The continuous slope rests on few firms.** It is identified mainly by the four merchants and PSEG; every other electric utility has uncontracted intensity near zero.
- **EIA's regulatory status is a plant-level label.** It does not reflect contracts.
- **Capacity is not earnings.** A firm with a small but high-margin merchant fleet may be more exposed than its capacity share suggests.
