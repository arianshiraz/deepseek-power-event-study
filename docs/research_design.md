# Who Captures AI Load? Power-Sector Equity Returns and the DeepSeek Shock

**Pilot study for the PhD proposals** (Economics: "When Compute Meets the Grid", Paper 2; Finance: "Financing the Buildout", Paper 2)
**Status:** pipeline running; firm classification frozen under rule v1.1 (6 November 2026). Contract evidence verified against pre-event 10-K and 10-Q filings (6 November 2026); no flag changed.

---

## 1. Question

On Monday 27 January 2025, after DeepSeek's R1 model raised doubts about how much compute (and so how much electricity) AI would need, US power-sector stocks fell sharply. The fall was not uniform. Competitive (merchant) generators fell by double digits, while regulated utilities were largely spared.

The pilot asks when expectations about AI electricity demand move, whose value moves with them. Stock prices give a forward-looking, market-wide answer to one half of an incidence question that is otherwise hard to observe early: who captures the rents when large, price-inelastic load lands on a constrained grid. Returns do not show who pays. That depends on whether the rents arrive through wholesale and capacity prices, which other consumers bear, or through contract premiums paid by data-centre buyers.

## 2. Link to the PhD proposals

- **Economics, Paper 2 (incidence of AI load):** if generators selling at market prices capture the value of expected AI load, the rents are likely to come at least partly through higher wholesale energy and capacity prices. The cross-section of returns measures the capture side of that incidence. Paper 2 measures the price side directly.
- **Finance, Paper 2 (contracts and bankability):** firms that have locked hyperscaler demand into long-term contracts should be less exposed to news about AI demand. The events test whether contracting insulates value.
- **Thesis link:** the key contrast, market-priced versus administered revenue, is the same distinction the IREX thesis studies.

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

In the DeepSeek estimation the other three events are removed from the estimation window, so they do not inflate residual variance or bias betas. Section 8c treats them as events in their own right.

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

Built on 6 November 2026 by `code/02_build_exposure.py` (output `data/derived/exposure.csv`):

| Measure | Definition |
|---|---|
| `merchant_mw_per_bn` (primary) | Uncontracted non-regulated owned MW per $bn of equity market value at 31 Dec 2024 |
| `nr_mw_per_bn` | Same without the contract adjustment |
| `nr_share`, `pjm_ercot_share`, `nuclear_share` | Shares of owned capacity (EIA-860 2024) |

Exposure is scaled by equity value because a return is a change in value divided by value. The predicted reaction to news about merchant power prices is therefore proportional to merchant MW per dollar of equity, not to merchant MW as a share of the generation fleet.

Still to build:

| Measure | Source | Notes |
|---|---|---|
| Continuous contracted share (replacing the binary flag) | FY2023 10-Ks, already read for the flag | NextEra reports 1,842 MW merchant; Millstone is about half uncontracted |
| Hyperscaler contracts announced before each event | Press releases, 8-Ks | Hand-collected, with dates |
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
| [0,0] | −19.0% (t = −8.75) | −1.7% (t = −1.21) | +1.7% (t = 1.89) | +4.0% (t = 4.06) | −20.8% (t = −8.87) |
| [0,1] | −15.6% (t = −5.07) | −4.9% (t = −2.55) | +0.1% | +2.8% | −15.7% (t = −4.73) |
| [0,5] | −5.6% (t = −1.06) | −3.9% | +1.0% | +4.2% | −6.6% (t = −1.16) |

- **H1 holds on the event day.** The merchant group's Kolari and Pynnönen adjusted t is −5.07 (p = 0.015, N = 4; average residual correlation 0.57). The day-0 merchant slope is larger in magnitude than on all 246 placebo days (p < 0.004).
- **There was no anticipation.** The pre-event window is flat.
- **Most of the fall reversed within about three trading days.** By [0,5] the merchant CAR is −5.6% and no longer significant. Either the first reaction overshot, or investors quickly reconsidered whether cheaper compute raises total compute demand (a Jevons-type rebound). The stacked events and the later windows are the tools for separating the two.
- **The rotation was defensive.** Water and gas utilities rose by 4.0% and regulated electric utilities by only 1.7%. Measured against pure defensives, regulated electrics underperformed by about 2.3 points. That is a small AI-exposure component, even under regulation.
- **The pattern within groups is suggestive.** PEG, whose merchant arm is PJM nuclear, fell 6.4%, while NEE (+1.7%) and AES (−0.3%), which are mostly contracted, did not. Among regulated utilities, ETR (−4.7%) stands out, and Entergy had a large announced data-centre customer. EIX and PCG were exposed to the January 2025 Los Angeles wildfires, a confounder to check.

**Limits of a single event.** Four merchant firms is a very small treated group, and one event cannot separate AI news from anything else that hit these firms that day. The stacked events in 8c test whether the same gradient appears, with the opposite sign, on good news.

### 8b. Results with frozen groups and continuous exposure (run of 6 November 2026)

Merchant coefficient across classification versions (day 0, CAR on group dummies, regulated is the base):

| Version | Merchant minus regulated | HC3 s.e. | Placebo-day p |
|---|---|---|---|
| v1.1 (frozen) | −20.5 points | 3.3 | < 0.004 (0 of 246) |
| v1.0 strict (PSEG as merchant) | −17.9 points | 3.8 | < 0.004 |
| Preliminary | −20.8 points | 3.3 | < 0.004 |

Continuous exposure (day 0, with a placebo-sector dummy):

| Measure | Effect of +100 MW per $bn | HC3 p | Placebo-day p |
|---|---|---|---|
| `merchant_mw_per_bn` (contract-adjusted) | −2.6 points | 0.003 | < 0.004 |
| `nr_mw_per_bn` (unadjusted) | −1.8 points | 0.046 | < 0.004 |

- **Contracts insulate value (H3, descriptive).** AES has about as much non-regulated capacity per dollar of equity as Talen (1,016 vs 1,068 MW per $bn), but its fleet is mostly long-term contracted. On the event day AES fell 0.3% and Talen 19.9%. The contracted hybrids (SO, D, BKH, NEE) moved with the regulated utilities. Adjusting for contracts raises the explanatory power of the exposure measure, as H3 predicts.
- **The response rises with exposure.** PSEG's uncontracted intensity is about one fifth of the merchants' (97 vs 460 to 1,068 MW per $bn), and its fall (−6.4%) is about one third of theirs.
- **Within the merchants, the ranking is imperfect.** NRG has high intensity but fell least (−11.8%). One candidate explanation, not yet tested: NRG's large retail business gains when wholesale prices fall, a natural hedge. Its FY2023 10-K supports the mechanism: NRG hedges its wholesale sales and purchases to support its retail load obligations.
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

with event fixed effects (α_e), an event-specific placebo-sector intercept (γ_e), and x_ie in units of 100 MW per $bn. H4 predicts β > 0, and each event-specific slope β_e has sign s_e.

**Inference.**
1. **Primary: placebo-date permutation.** Draw 2,000 sets of four non-event dates (at least 3 trading days from any event), attach the signs (+, +, −, −) in random order, and re-estimate β using residuals from a single market model over the whole sample. One-sided p = share of placebo β ≥ actual β.
2. **Secondary: firm-clustered standard errors.**

**Robustness.** Include the excluded parties; use the [0,0] window; use the merchant group dummy in place of x; drop each event in turn.

### Results (run of 6 November 2026; `output/tables/stacked_*.csv`, figures 2 to 4)

Event-by-event slopes (CAR[0,1], percentage points per 100 MW/$bn, HC3):

| Event | Predicted sign | Slope | s.e. | p |
|---|---|---|---|---|
| PJM capacity auction | + | +0.68 | 0.17 | < 0.001 |
| Crane PPA (CEG excluded) | + | +0.63 | 0.86 | 0.46 |
| FERC rejects Talen ISA (TLN excluded) | − | −0.84 | 1.00 | 0.40 |
| DeepSeek | − | −2.05 | 0.85 | 0.016 |

All four slopes have the predicted sign. If signs were random and independent, that would happen with probability 1/16.

Pooled sign-adjusted slope (H4: β > 0):

| Specification | β (pp per 100 MW/$bn) | Firm-clustered p | Placebo-date p (one-sided) |
|---|---|---|---|
| Main: CAR[0,1], parties excluded | +0.90 (s.e. 0.28) | 0.001 | < 0.0005 (0 of 2,000) |
| Parties included | +0.90 | 0.004 | 0.0005 |
| CAR[0,0] | +0.65 | < 0.001 | < 0.0005 |
| Merchant dummy in place of x | +9.4 pp | < 0.001 | < 0.0005 |
| Drop PJM auction | +1.04 | 0.006 | < 0.0005 |
| Drop Crane PPA | +1.04 | < 0.001 | 0.0005 |
| Drop FERC order | +0.91 | 0.001 | 0.0005 |
| Drop DeepSeek | +0.68 | 0.007 | 0.004 |

**Reading.** Good and bad news about AI electricity demand moved firm values in opposite directions, in proportion to the same exposure: uncontracted merchant capacity per dollar of equity. A confounder specific to DeepSeek day cannot produce that pattern. Without DeepSeek, β is +0.68, above all but 7 of the 2,000 placebo draws (p = 0.004).

**Limits.**
- Four events. Crane and FERC are individually imprecise, partly because their most directly affected firm is excluded.
- As in 8b, the slope within each event rests on the four merchants and PSEG.
- Day-0 timing for the auction results and the FERC order is unconfirmed. The [0,1] window covers both possibilities.
- The events were chosen as salient AI-electricity news, not drawn by a rule. A rule-based event list (for example, every hyperscaler power deal above a size threshold) would make the selection harder to question.

## 8d. AI-beta control (pre-specified 7 November 2026)

Written before estimating any of the regressions below.

**Threat.** Merchant generators traded as "AI stocks" through 2024. Their event-day moves may reflect general sensitivity to AI sentiment, or a crowded trade unwinding, rather than their exposure to electricity prices.

**AI factor.** Daily return on the VanEck Semiconductor ETF (SMH), orthogonalised to the market: the residual from regressing SMH returns on SPY returns within each event's estimation window. NVIDIA (NVDA) is the alternative factor. Each firm's AI beta is its loading on this factor in

r_i = a + b_m · r_m + b_ai · r_ai⊥ + e,

estimated over the same window as the market model (days −260 to −11, excluding days −1 to +1 around all four events).

**Specifications** (stacked, CAR[0,1], parties excluded, as in 8c):
1. **Primary: two-factor abnormal returns.** Compute abnormal returns from the two-factor model, so each firm's predicted response to the event-day AI-factor move is removed, then re-estimate the pooled β. Placebo-date inference uses residuals from a full-sample two-factor model.
2. **Cross-sectional control.** Keep market-model CARs and add b_ai with an event-specific coefficient: CAR_ie = α_e + γ_e · placebo_i + δ_e · b_ai,ie + β · (s_e · x_ie) + ε_ie.
3. **Both specifications with NVDA** in place of SMH.
4. **DeepSeek day alone:** CAR[0,0] on x, b_ai and the placebo dummy.

**Prediction (H5).** β stays positive and outside the placebo distribution.

**Interpretation caveat, stated in advance.** This control may be a "bad control". If AI-load news moves merchant values, then merchants' co-movement with AI stocks during 2024 is partly *caused* by their electricity exposure. Controlling for AI beta may then absorb part of the very mechanism being tested.
- If β survives, there is an electricity-specific channel beyond general AI sentiment.
- If β shrinks to zero, the two explanations cannot be separated with these data. That does not show the electricity channel is absent.

### Results (run of 7 November 2026; `output/tables/ai_beta_*.csv`, figure 5)

**Merchant exposure and AI beta are close to the same variable.** Over the DeepSeek estimation window, the mean AI beta (SMH, orthogonalised) is +0.30 for merchants and between −0.35 and −0.42 for every other group. Across firms, AI beta and merchant exposure x are correlated at 0.88 (SMH) and 0.89 (NVDA).

Pooled sign-adjusted slope (pp per 100 MW/$bn, CAR[0,1], four events, parties excluded):

| Specification | SMH | NVDA |
|---|---|---|
| Reference: market model, no control | +0.90 (p 0.001; placebo 0/2000) | +0.90 (p 0.001; placebo 0/2000) |
| 1. Two-factor abnormal returns (primary) | +0.80 (p 0.003; placebo 0/2000) | +0.85 (p 0.002; placebo 0/2000) |
| 2. Free event-specific AI-beta control | +0.13 (p 0.59; placebo p 0.22) | −0.14 (p 0.52; placebo p 0.79) |
| Exploratory: AI beta × that event's AI-factor move | +0.68 (p 0.010; placebo p 0.001) | +0.70 (p 0.013; placebo p 0.003) |

DeepSeek day alone (CAR[0,0]): x on its own is −2.8 pp per 100 MW/$bn (HC3 p 0.006). Adding AI beta takes it to −0.7 (SMH) or −0.2 (NVDA), and it is no longer significant.

**Reading.**
- **H5 holds under the pre-specified primary test.** Once each firm's predicted response to the AI-stock move is removed from its returns, the exposure slope barely changes: +0.80 to +0.85 against +0.90. It still lies above every placebo draw.
- **The free control removes the effect but cannot separate the channels.** With x and AI beta correlated at 0.88 and a separate AI-beta coefficient for each event, the control can reproduce whatever pattern x shows on each date. That is the over-control the caveat anticipated.
- **Two events separate the channels.** The orthogonalised AI factor fell on the Crane day (SMH −1.0%) while merchants rose, and rose on the FERC day (+0.7%) while merchants fell. A general AI-sentiment channel predicts the wrong sign on both days. The exploratory specification uses this: it ties the AI channel to what AI stocks actually did that day, lets its scale be estimated freely, and β stays at +0.68 to +0.70. It was added after seeing specifications 1 and 2, so it is labelled exploratory.
- **DeepSeek alone cannot separate the explanations.** On that day the AI shock and the electricity-demand shock are the same news, and in this sample the merchants are also the high-AI-beta firms. The electricity-specific interpretation rests on the stacked design, especially the two events where AI stocks and merchants moved in opposite directions.

## 9. Threats and responses

| Threat | Response | Status |
|---|---|---|
| The market proxy absorbs part of the shock | Equal-weighted and ex-technology market proxies, both reported | Planned |
| Classification choices drive the result | Written rule frozen before re-estimation (`classification_rule.md`), continuous exposure, three classification versions reported | Done |
| Merchant exposure proxies for AI-stock beta | Two-factor abnormal returns and AI-beta controls (8d) | Done |
| Few merchant firms | Portfolio and placebo-day inference, plus Canadian IPPs (TransAlta, Capital Power) as a robustness sample | Inference done; Canadian sample planned |
| Firm-specific news on the event day | News check for every firm in [−1,+1], dropping or flagging hits (EIX and PCG wildfires) | Planned |
| Later AI news contaminates long windows | Interpret only [0,0] to [0,5] for DeepSeek and treat [0,20] as descriptive | Done |
| Yahoo data revisions | Raw download kept unedited with a timestamp, and a cross-check against CRSP if university access allows | Partly done |

## 10. Literature

| Reference | Role | Verified |
|---|---|---|
| Bushnell, J., Chong, H., & Mansur, E. T. (2013). Profiting from Regulation: Evidence from the European Carbon Market. *AEJ: Economic Policy*, 5(4), 78 to 106. | Closest precedent: equity returns of power firms to a common market-wide shock, with exposure gradients | Yes |
| Eisfeldt, A. L., Schubert, G., & Zhang, M. B. (2023). Generative AI and Firm Values. NBER Working Paper 31222. | Precedent for using an AI release as an equity event | Yes |
| Kolari, J. W., & Pynnönen, S. (2010). Event Study Testing with Cross-sectional Correlation of Abnormal Returns. *Review of Financial Studies*, 23(11), 3996 to 4025. | Inference with a common event date | Yes |
| Fabra, N., & Reguant, M. (2014). Pass-Through of Emissions Costs in Electricity Markets. *AER*, 104(9), 2872 to 2899. | Incidence framework the proposal builds on | Yes |
| International Energy Agency (2025). *Energy and AI*. | Demand context (about 415 TWh in 2024 to about 945 TWh by 2030) | Yes (IEA release) |
| MacKinlay, A. C. (1997). Event Studies in Economics and Finance. *Journal of Economic Literature*, 35(1), 13 to 39. | Standard method reference | Yes |
| Boehmer, E., Musumeci, J., & Poulsen, A. B. (1991). Event-study methodology under conditions of event-induced variance. *Journal of Financial Economics*, 30(2), 253 to 272. | BMP test | Yes |
| Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics*, 116(1), 1 to 22. | Robustness normal-return model | Yes |

**Novelty check.** Searches on 5 November 2026 found press coverage of the power-sector sell-off but no academic event study of it. SSRN and Google Scholar have not yet been searched directly. The repository is public, so this is the most urgent open check.

## 11. Status and remaining work

Done by 7 November 2026: classification frozen with sources, continuous exposure measures, 10-K contract checks, stacked events (H4), AI-beta control (H5).

Remaining:

| Work | Notes |
|---|---|
| SSRN and Google Scholar novelty check | Most urgent, since the repository is public |
| Firm news check in [−1,+1] for every event | Flag or drop confounded firms |
| Fama and French five-factor and equal-weighted market robustness | Section 7 |
| Confirm release times of the auction results and the FERC order | Would allow a day-0 window for those events |
| 6 to 8 page note (PDF) | For the writing sample and applications |

**Sentence for the research statement:** in four dated AI-electricity events, investors repriced generators that sell at market prices in proportion to their uncontracted capacity, upward on good news and downward on bad news, while regulated utilities and firms with long-term contracts barely moved.
