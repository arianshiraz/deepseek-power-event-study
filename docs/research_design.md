# Who Captures AI Load? Power-Sector Equity Returns and the DeepSeek Shock

**Pilot study for the PhD proposals** (Economics: "When Compute Meets the Grid", Paper 2; Finance: "Financing the Buildout", Paper 2)
**Status:** pipeline running; firm classification frozen under rule v1.1 (6 November 2026). Contract evidence partly verified.

---

## 1. Question

On Monday 27 January 2025, after DeepSeek's R1 model raised doubts about how much compute (and so how much electricity) AI would need, US power-sector stocks fell sharply. The fall was not uniform. Competitive (merchant) generators fell by double digits, while regulated utilities were largely spared.

The pilot asks: **when expectations about AI electricity demand move, whose value moves with them?** Stock prices give a forward-looking, market-wide answer to an incidence question that is otherwise hard to observe early: who captures the rents when large, price-inelastic load lands on a constrained grid?

## 2. Why this question, for these proposals

- **Economics, Paper 2 (incidence of AI load).** If market-priced generators capture the value of expected AI load, then other consumers pay for it through higher wholesale energy and capacity prices. The cross-section of returns is an early, market-implied measure of that incidence.
- **Finance, Paper 2 (contracts and bankability).** Firms that have locked hyperscaler demand into long-term contracts should be less exposed to news about AI demand. The event tests whether contracting insulates value.
- **Thesis link.** The key contrast, market-priced versus administered revenue, is the same distinction the IREX thesis studies.

## 3. Hypotheses

| | Hypothesis | Test |
|---|---|---|
| H1 | Merchant generators earn large negative abnormal returns on the event day; regulated utilities do not. | Group CARs; portfolio test |
| H2 | Within the sector, the size of the fall rises with exposure to market prices, the PJM and ERCOT markets, and nuclear capacity (the asset class hyperscalers contract for). | Cross-sectional regression of CAR on exposure measures |
| H3 | Holding merchant exposure fixed, firms with long-term hyperscaler contracts announced before the event fall less. | Interaction term (small sample: descriptive) |
| H4 | The same exposure gradient appears with the opposite sign on positive AI-load news (capacity auction, Crane PPA). | Stacked events (Stage 2) |

H4 is the strongest test. One event can reflect anything that happened that Monday. A gradient that flips sign on good news and bad news is much harder to explain away.

## 4. Events

| Date (day 0) | Event | Sign for AI load | Status |
|---|---|---|---|
| 2025-01-27 | DeepSeek sell-off (first session after R1 drew wide attention) | Negative | Main event |
| 2024-07-30 | PJM 2025/26 capacity auction clears at $269.92/MW-day (vs $28.92 the year before) | Positive | Date verified; check whether results were posted after the close |
| 2024-09-20 | Constellation and Microsoft announce the 20-year Crane (TMI-1) restart PPA | Positive | Date verified from the 8-K |
| 2024-11-01 | FERC rejects the amended Talen and Amazon Susquehanna ISA (2 to 1 vote) | Negative | Order date from press reports; confirm on FERC eLibrary, use window [0,1] |

The secondary events are currently removed from the estimation window so they do not inflate residual variance or bias betas. In Stage 2 they become events in their own right.

## 5. Sample

45 US-listed firms. Groups were frozen on 6 November 2026 under a written rule (`docs/classification_rule.md`, v1.1) using EIA-860 2024 ownership data, market caps at 31 December 2024, and 10-K contract evidence (`data/classification/contract_status.csv`):

| Group | n | Definition |
|---|---|---|
| merchant | 4 | Non-regulated share of owned capacity ≥ 50%, mostly uncontracted, no cost-of-service utility: VST, CEG, NRG, TLN |
| hybrid | 6 | Non-regulated share ≥ 10% otherwise: PEG (uncontracted), NEE, AES, SO, D, BKH (mostly contracted) |
| regulated | 29 | Non-regulated share < 10%, or under 1,000 MW owned (wires utilities) |
| placebo | 6 | Water and gas distribution utilities, with no electricity generation exposure |

ALLETE (ALE) was dropped because Yahoo Finance returned no data for it. Relative to the preliminary list, SO, D and BKH moved from regulated to hybrid. Under the strict v1.0 rule, PEG would be merchant, and that version is reported as a robustness check.

## 6. Exposure measures

**Built (6 November 2026; `code/02_build_exposure.py`, output `data/derived/exposure.csv`):**

| Measure | Definition |
|---|---|
| `merchant_mw_per_bn` (primary) | Uncontracted non-regulated owned MW per $bn of equity market value at 31 Dec 2024 |
| `nr_mw_per_bn` | Same without the contract adjustment |
| `nr_share`, `pjm_ercot_share`, `nuclear_share` | Shares of owned capacity (EIA-860 2024) |

Scaling by market value matters. A return is a change in value divided by value, so the predicted reaction to news about merchant power prices is proportional to merchant MW per dollar of equity, not to merchant MW as a share of the generation fleet.

**Still to build:**

| Measure | Source | Notes |
|---|---|---|
| Contract shares from full 10-K reads | FY2023 10-Ks | Replace the binary contract flag |
| Share of capacity in PJM and ERCOT | EIA-860 plant balancing authority | The markets where data-centre load and capacity prices moved most |
| Nuclear share of capacity | EIA-860 | Firm, carbon-free supply: the asset class hyperscalers contract for |
| Hyperscaler contracts announced before the event | Press releases, 8-Ks | Hand-collected, with dates |
| Announced large-load or data-centre pipeline (regulated utilities) | Q4 2024 earnings materials | Regulated utilities gain from load through rate-base growth, not prices |

## 7. Method

**Normal returns.** Market model on SPY, estimated over trading days −260 to −11, excluding the secondary event days. Robustness:
- Fama and French five-factor model.
- An equal-weighted market proxy. SPY is heavy in AI-exposed technology stocks, so on 27 January the market return itself contains the shock. High-beta merchants then have part of their fall absorbed by the market term, which makes the baseline estimates conservative.

**Event windows.** [0,0], [0,1], [0,5], [0,20], and pre-event [−5,−1] to check for anticipation. Read [0,20] with care: it overlaps later, unrelated AI news.

**Inference with a common event date.** Every firm shares the same day 0, so abnormal returns are correlated across firms and ordinary cross-sectional t-tests over-reject. Three approaches:
1. **Portfolio test:** one equal-weighted return series per group (and merchant minus regulated), tested against its own residual s.d. Cross-correlation does not arise.
2. **BMP t with the Kolari and Pynnönen (2010) adjustment,** using the average residual correlation within each group.
3. **Placebo-day distribution for the cross-sectional slope:** run the same CAR-on-group regression on every non-event day of the estimation window. The p-value is the share of placebo slopes at least as large in absolute value as the event-day slope.

## 8. Preliminary results (run of 5 November 2026; classification not yet frozen)

Abnormal returns (market model), equal-weighted portfolios:

| Window | Merchant | Hybrid | Regulated | Placebo (water/gas) | Merchant minus regulated |
|---|---|---|---|---|---|
| [−5,−1] | +1.8% (t = 0.36) | −1.7% | −2.0% | −3.2% | +3.8% (t = 0.73) |
| [0,0] | **−19.0%** (t = −8.75) | −1.7% (t = −1.21) | +1.7% (t = 1.89) | +4.0% (t = 4.06) | **−20.8%** (t = −8.87) |
| [0,1] | −15.6% (t = −5.07) | −4.9% (t = −2.55) | +0.1% | +2.8% | −15.7% (t = −4.73) |
| [0,5] | −5.6% (t = −1.06) | −3.9% | +1.0% | +4.2% | −6.6% (t = −1.16) |

- **H1 holds on the event day.** The merchant group's Kolari and Pynnönen adjusted t is −5.07 (p = 0.015, N = 4; average residual correlation 0.57). The day-0 merchant slope is larger in magnitude than on all 246 placebo days (p < 0.004).
- **There was no anticipation.** The pre-event window is flat.
- **Most of the fall reversed within about three trading days.** By [0,5] the merchant CAR is −5.6% and no longer significant. This partial reversal is a finding in its own right. Either the first reaction overshot, or investors quickly reconsidered whether cheaper compute raises total compute demand (a Jevons-type rebound). Telling these apart is the job of the stacked-event design and the later-window analysis.
- **The rotation was defensive.** Water and gas utilities rose by 4.0% and regulated electric utilities by only 1.7%. Measured against pure defensives, regulated electrics underperformed by about 2.3 points. That is a small AI-exposure component, even under regulation.
- **The pattern within groups is suggestive.** PEG, whose merchant arm is PJM nuclear, fell 6.4%, while NEE (+1.7%) and AES (−0.3%), which are mostly contracted, did not. Among regulated utilities, ETR (−4.7%) stands out, and Entergy had a large announced data-centre customer. EIX and PCG were exposed to the January 2025 Los Angeles wildfires, a confounder to check.

**What this does not yet show.** Four merchant firms is a very small treated group. A single event cannot separate AI news from anything else that hit these firms that day. Stacked events with opposite signs (H4) are what turn a stylised fact into evidence.

### 8b. Results with frozen groups and continuous exposure (run of 6 November 2026)

**Merchant coefficient across classification versions** (day 0, CAR on group dummies, regulated is the base):

| Version | Merchant minus regulated | HC3 s.e. | Placebo-day p |
|---|---|---|---|
| v1.1 (frozen) | −20.5 points | 3.3 | < 0.004 (0 of 246) |
| v1.0 strict (PSEG as merchant) | −17.9 points | 3.8 | < 0.004 |
| Preliminary | −20.8 points | 3.3 | < 0.004 |

**Continuous exposure** (day 0, with a placebo-sector dummy):

| Measure | Effect of +100 MW per $bn | HC3 p | Placebo-day p |
|---|---|---|---|
| `merchant_mw_per_bn` (contract-adjusted) | −2.6 points | 0.003 | < 0.004 |
| `nr_mw_per_bn` (unadjusted) | −1.8 points | 0.046 | < 0.004 |

- **Contracts insulate value (H3, descriptive).** AES has about as much non-regulated capacity per dollar of equity as Talen (1,016 vs 1,068 MW per $bn), but its fleet is mostly long-term contracted. On the event day AES fell 0.3% and Talen 19.9%. The contracted hybrids (SO, D, BKH, NEE) moved with the regulated utilities. Adjusting for contracts raises the explanatory power of the exposure measure, as H3 predicts.
- **The response rises with exposure.** PSEG's uncontracted intensity is about one fifth of the merchants' (97 vs 460 to 1,068 MW per $bn), and its fall (−6.4%) is about one third of theirs.
- **Within the merchants, the ranking is imperfect.** NRG has high intensity but fell least (−11.8%). One candidate explanation, not yet tested: NRG's large retail business gains when wholesale prices fall, a natural hedge.
- **Caveat.** The continuous slope is identified mainly by the four merchants and PSEG, because almost every other electric utility has intensity near zero. It refines the group contrast rather than adding independent variation.

## 8c. Stacked-event test of H4 (pre-specified 6 November 2026)

Written before computing any returns for the three secondary events. Only the DeepSeek returns had been seen.

**Events and predicted signs** (`code/config.py`, `EVENTS`):

| Event | Day 0 | Sign s_e | Firm excluded in main spec |
|---|---|---|---|
| PJM 2025/26 capacity auction results | 2024-07-30 | +1 | none |
| Constellation and Microsoft Crane PPA | 2024-09-20 | +1 | CEG (party to the deal) |
| FERC rejects Talen and Amazon ISA | 2024-11-01 | −1 | TLN (party to the order) |
| DeepSeek sell-off | 2025-01-27 | −1 | none |

**Window.** [0,1] for every event is the primary window, because the intraday release times of the auction results and the FERC order are not yet confirmed. [0,0] is secondary.

**Normal returns.** A market model for each event, estimated over trading days −260 to −11 relative to that event, excluding days −1 to +1 around all four events.

**Exposure.** `merchant_mw_per_bn` recomputed for each event with pre-event equity value: the 31 Dec 2024 market cap scaled by the adjusted price ratio between event day −11 and 31 Dec 2024. Merchant market values rose sharply during 2024, so year-end values would understate exposure at the earlier events. Megawatts are the end-2024 EIA values throughout.

**Specification.**

CAR_ie = α_e + γ_e · placebo_i + β · (s_e · x_ie) + ε_ie

with event fixed effects (α_e), an event-specific placebo-sector intercept (γ_e), and x_ie in units of 100 MW per $bn. **H4 predicts β > 0**, and each event-specific slope β_e has sign s_e.

**Inference.**
1. **Primary: placebo-date permutation.** Draw 2,000 sets of four non-event dates (at least 3 trading days from any event), attach the signs (+, +, −, −) in random order, and re-estimate β using residuals from a single market model over the whole sample. One-sided p = share of placebo β ≥ actual β.
2. **Secondary: firm-clustered standard errors.**

**Robustness.** Include the excluded parties; use the [0,0] window; use the merchant group dummy in place of x; drop each event in turn.

### Results (run of 6 November 2026; `output/tables/stacked_*.csv`, figures 2 to 4)

**Event-by-event slopes** (CAR[0,1], percentage points per 100 MW/$bn, HC3):

| Event | Predicted sign | Slope | s.e. | p |
|---|---|---|---|---|
| PJM capacity auction | + | +0.68 | 0.17 | < 0.001 |
| Crane PPA (CEG excluded) | + | +0.63 | 0.86 | 0.46 |
| FERC rejects Talen ISA (TLN excluded) | − | −0.84 | 1.00 | 0.40 |
| DeepSeek | − | −2.05 | 0.85 | 0.016 |

All four slopes have the predicted sign. If signs were random and independent, that would happen with probability 1/16.

**Pooled sign-adjusted slope** (H4: β > 0):

| Specification | β (pp per 100 MW/$bn) | Firm-clustered p | Placebo-date p (one-sided) |
|---|---|---|---|
| Main: CAR[0,1], parties excluded | **+0.90** (s.e. 0.28) | 0.001 | < 0.0005 (0 of 2,000) |
| Parties included | +0.90 | 0.004 | 0.0005 |
| CAR[0,0] | +0.65 | < 0.001 | < 0.0005 |
| Merchant dummy in place of x | +9.4 pp | < 0.001 | < 0.0005 |
| Drop PJM auction | +1.04 | 0.006 | < 0.0005 |
| Drop Crane PPA | +1.04 | < 0.001 | 0.0005 |
| Drop FERC order | +0.91 | 0.001 | 0.0005 |
| Drop DeepSeek | +0.68 | 0.007 | 0.004 |

**Reading.** Good and bad news about AI electricity demand moved firm values in opposite directions, in proportion to the same exposure: uncontracted merchant capacity per dollar of equity. A single DeepSeek-day confounder cannot produce that pattern. The result does not depend on DeepSeek: without it, β is +0.68 and still above every placebo draw but a handful.

**Limits.**
- Four events. Crane and FERC are individually imprecise, partly because their most directly affected firm is excluded.
- Within each event the slope is identified by the four merchants and PSEG.
- Day-0 timing for the auction results and the FERC order is unconfirmed; the [0,1] window covers both possibilities.
- The events were chosen as salient AI-electricity news, not drawn by a rule. A rule-based event list (for example, every hyperscaler power deal above a size threshold) would make the selection harder to question.

## 9. Threats and responses

| Threat | Response |
|---|---|
| The market proxy absorbs part of the shock | Equal-weighted and ex-technology market proxies; report both |
| Classification choices drive the result | Document and freeze the classification before Stage 2; use continuous exposure measures |
| Few merchant firms | Portfolio and placebo-day inference; add Canadian IPPs (TransAlta, Capital Power) as a robustness sample |
| Firm-specific news on the event day | News check for every firm in [−1,+1]; drop or flag (EIX, PCG wildfires) |
| Later AI news contaminates long windows | Interpret only [0,0] to [0,5] for DeepSeek; treat [0,20] as descriptive |
| Yahoo data revisions | Raw download kept unedited with a timestamp; cross-check against CRSP if university access allows |

## 10. Literature

| Reference | Role | Verified |
|---|---|---|
| Bushnell, J., Chong, H., & Mansur, E. T. (2013). Profiting from Regulation: Evidence from the European Carbon Market. *AEJ: Economic Policy*, 5(4), 78 to 106. | Closest precedent: equity returns of power firms to a common market-wide shock, with exposure gradients | Yes |
| Eisfeldt, A. L., Schubert, G., & Zhang, M. B. (2023). Generative AI and Firm Values. NBER Working Paper 31222. | Precedent for using an AI release as an equity event | Yes |
| Kolari, J. W., & Pynnönen, S. (2010). Event Study Testing with Cross-sectional Correlation of Abnormal Returns. *Review of Financial Studies*, 23(11), 3996 to 4025. | Inference with a common event date | Yes |
| Fabra, N., & Reguant, M. (2014). Pass-Through of Emissions Costs in Electricity Markets. *AER*, 104(9), 2872 to 2899. | Incidence framework the proposal builds on | Yes |
| International Energy Agency (2025). *Energy and AI*. | Demand context (about 415 TWh in 2024 to about 945 TWh by 2030) | Yes (IEA release) |
| MacKinlay, A. C. (1997). Event Studies in Economics and Finance. *Journal of Economic Literature*, 35(1). | Standard method reference | Not yet |
| Boehmer, E., Musumeci, J., & Poulsen, A. B. (1991). Event-study methodology under conditions of event-induced variance. *Journal of Financial Economics*, 30(2). | BMP test | Not yet |
| Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics*, 116(1). | Robustness normal-return model | Not yet |

**Novelty check.** Searches on 5 November 2026 found press coverage of the power-sector sell-off but no academic event study of it. SSRN and Google Scholar have not been searched directly. Do that before any external use.

## 11. Deliverables and timeline (about 3 weeks part-time)

| Week | Work |
|---|---|
| 1 | ~~Freeze the classification with sources; build continuous exposure measures~~ (done 6 Nov); read the FY2023 10-K contract passages; firm news check |
| 2 | ~~Stacked events for H4~~ (done 6 Nov); robustness (FF5, equal-weighted market, Canadian IPPs); confirm auction and FERC release times |
| 3 | 6 to 8 page note (PDF) and repo cleanup; one paragraph for the research statement |

**What goes in the research statement (one sentence, once Stage 2 holds):** preliminary evidence from the DeepSeek shock shows that investors price expected AI load as a gain to generators selling at market prices, not to regulated utilities, which implies that other consumers pay for it.
