# Camera-ready audit — MeshCrowd (DESSERT 2026)

**Manuscript audited:** `paper-17-Oct/MeshCrowd_camera_ready.tex` (compiled: `MeshCrowd_camera_ready.pdf`, **8 pp.** — cut from 12 pp. to the venue limit; see Part G).
**Reviews audited:**
- **R1** — *IEEE Peer-Review Report — Referee Copy* (Major Revision, 2.5/5): M1–M6, m1–m8, Q1–Q4
  (`.../workspace-.../merged/review_MeshCrowd_IEEE.md`).
- **R2** — second-round report, **Accept with minor revision**: 4 concerns + general comments
  (wording captured in `.../workspace-.../MeshCrowd/reviews/response-to-reviewers.md`).

**Legend:** **A** = addressed · **P** = partially addressed / addressed within constraints · **N** = not addressed.

---

## Part A — Reviewer 1 (major revision)

| Item | Status | Evidence / where in the camera-ready |
|---|---|---|
| **M1** Denominators & percentages incompatible (unrealizable at stated *n*); recompute intervals; regenerate Fig. 6 | **A** | E1 per-cell denominator corrected to *n* = 60 (20 crossings × 3 blocks; 420 crossings), and the per-cell integer counts are now printed in Table I (detection 58/56/52/44/36/30/9; classification 56/52/48/40/32/24/6) with recomputed 95 % Wilson CIs — e.g. 56/60 = [84.1, 97.4], reproducing the paper's own §V-G value. Fig. `field_envelope.png` regenerated at *n* = 60. Table III keeps its stated *n* = 20/cell; the two cells whose printed rates (91.7 %, 58.3 %) are not realizable at *n* = 20 are **de-claimed**: the invalid CI column is removed and the caption states they are recorded observer proportions whose per-cell tallies were not preserved. No counts invented. |
| **M2** Title/abstract overclaim | **P** | (a) title now "…Crowd and Vehicle **Sensing**…" (was "Estimation"); (b) privacy substantiated via §II-E rather than removed; (c) abstract demotes mesh/gamification to "design contributions … distributed validation is future work"; (d) "20/20" now explicitly attributed to the **hybrid fuser**. Title noun "Crowd" and the phrase "Privacy-Preserving" remain, but the title is fixed by conference policy. |
| **M3** No baselines / ablations / comparison to prior art | **N** | No ablation table and no related-work comparison table. The per-band (BLE-only / Wi-Fi-only) ablation is explicitly deferred: "not reported because the campaign logged the fused output; the per-link records in the session-log release permit that ablation." |
| **M4** External validity = single point; add 2nd handset/site, scan-cadence histogram, observer agreement E1–E4, or a generalization-limit section | **P** | A threats-to-validity/generalization-limit block is present (items 1–7, incl. single handset/site, weather, Android-16 meter caveat, no usability study). Scan randomness is now partly measured (§V-H: epoch gaps to 427.8 s, 23.5–50.4 % honoured-scan ratios, ninefold link-density collapse with the screen off). Still **no** second field handset/site and **no** observer-agreement statistics for E1–E4 (only κ = 0.96 for G4). |
| **M5** Privacy threat model | **A** | New §II-E: adversary model (curious peer, passive sniffer, fixed observer), concrete fields shared, minimizations (salted-SHA-256 per session, on-device dBm tables, aggregate-only egress), plus measured 0 B attributable mobile traffic. |
| **M6** Statistical-reporting gaps | **P** | (i) intervals: Table III has CIs, Table I has only a classification "typ." CI and **no detection CI**; (ii) Bland–Altman paired differences/plot still absent ([−18.3, 4.7] pp quoted, unverifiable); (iii) the 25 m denominator change is now described in the ITT prose but **no exclusion table**; (iv) **no** κ CI, no trend test, no multiple-comparison correction. |
| **m1** Ref entries lacking authors | **A** | The three author-less entries (cnnrti2025, dmip2023, mobisys2024) are gone from the rebuilt bibliography. |
| **m2** "illustrative session" screenshots | **P/A** | Deployment section now states all figures are real captures from single sessions on the campaign handset; app *projections* remain caption-guarded. |
| **m3** Fig. 6 duplicates Tables I/III; bands depend on M1 | **A** | `field_envelope.png` regenerated from the corrected *n* = 60 counts; panel (b) shows pedestrian Wilson intervals (*n* = 60) and vehicle markers as recorded proportions (no invalid intervals). |
| **m4** Derive the 2.355 speed constant; give τe's estimator window | **A** | Text now reads `|v| = 2.355 σc/τe` with `2.355 = 2√(2 ln 2)` (Gaussian FWHM), σc = class lateral profile (§II-C, 1.15 m vehicle), τe = dip duration returned by `DipDetector` (§II-B). |
| **m5** Availability promised only "upon acceptance"; provide link now | **P** | Data Availability offers the package "to the reviewers during review upon request" — still **no actual link/anonymized repository**. |
| **m6** Keywords omit the two evaluated novelties | **A** | Both `entity classification` and `transit counting` are now in the Index Terms (a redundant `RF sensing` was dropped in exchange). |
| **m7** Give the version/commit used for the campaign | **P** | Release "pins this build by hash" stated, but **no commit hash is printed**. |
| **m8** DESSERT header / author block = camera-ready format; confirm stage | **A** | Camera-ready stage confirmed: DESSERT running head + `\IEEEpubid` copyright line present. (See Part F on page length.) |
| **Q1** Which denominator produced each Table I/III percentage? | **A** | E1: per-cell integer counts at *n* = 60 (Table I). Vehicle: reported as recorded observer proportions at *n* = 20/cell, tallies not preserved (Table III). |
| **Q2** Why were the 3 blocked 15 m trials dropped only from the BLE cell, and how does the hybrid recover them? | **N** | The ITT paragraph addresses the 25 m cell, not the 15 m triple-block/BLE-only exclusion. |
| **Q3** Which fields leave the device in a mesh confirmation message? | **A** | Enumerated in §II-E (derived, time-bucketed crossing records; no raw identifiers). |
| **Q4** Will per-band dip-depth curves and scan-cadence histograms ship? | **P** | Scan-cadence evidence is now in the §V-H prose (epoch gaps, honoured-scan ratios); per-band dip-depth curves are not included, only "planned in the release". |

**R1 bottom line:** M1 is now closed (E1 integer counts and Wilson intervals corrected; Fig. 6 regenerated; vehicle table de-claimed rather than fabricated). M3 (baselines/ablations) remains the main open item; M4, M6, Q2 partially open.

---

## Part B — Reviewer 2 (minor revision)

| Item | Status | Evidence |
|---|---|---|
| **C1** Privacy claim incomplete/overstated (7 risk bullets; no model/adversary/retention/crypto/access/consent/minimisation) | **A** | §II-E covers data items, minimisation, retention, access control, adversary model, residual risks, and consent; measured 0 B attributable mobile traffic. The reviewer's suggested **renaming away from "privacy-preserving" was not adopted** because the conference fixes the title (R1-M2), so the route taken is substantiation. |
| **C2** Transit exclusions → intent-to-treat reporting: (a) ITT rate over all initiated trials, (b) failure categories, (c) per-config CIs, (d) predefined "evaluable" rule | **A** | §IV-B defines the evaluable rule; §V-G gives both denominators (16/20, 11/20, 20/20 ITT), failure categories, and Wilson CIs. **All quoted CIs independently recomputed and correct**: 16/20→[58.4,91.9], 11/20→[34.2,74.2], 20/20→[83.9,100], 16/17→[73.0,99.0], 11/18→[38.6,79.7]. |
| **C3** No energy/background/usability measurements | **A** | §IV-D (method) + §V-H (results) with table `tab:cost` from **real** legs B2/B3/B5 (the scan-cadence figures are folded into the §V-H prose). Every value reconciles exactly with `New Evaluations etc/Eval-Phone.md` (82.7/196.0/179.8 mA; 22.4/33.4/20.4 min; 117/579/774 bursts·h⁻¹; 0.235/0.504/0.0095 honoured-scan ratios; 0 B mobile traffic; 0.0 kB/h storage; 5604 mAh). Honest caveats embedded (n = 1/leg; Android 16 ≠ campaign platform; B2/B5 SOC = n/m not 0; B3 ±50 %; B5 display-on). Usability is stated as not run. |
| **C4** Correct headers per template | **A** | `\markboth{DESSERT 2026 Conference, Corfu, IEEE}{…}` + `\IEEEpubid` copyright line `979-8-3195-6683-6/26/$31.00 ©2026 IEEE` (string verified in the PDF). |
| **General** — narrow claims; fully specify classifier; add held-out + multi-device testing; separate measured from proposed | **P** | Claims narrowed ✓; classifier specified across §II-B/§II-D ✓; measured vs proposed separated ✓; multi-device and device/site transfer stated as future work ✓. **But no explicit statement about a train / held-out split** of the "frozen parameter vector" is made. |

---

## Part C — Citation & DOI audit (verified against Crossref / doi.org)

26 references were audited. Six printed DOIs were **wrong**, one printed page range was **wrong**, two volumes/years were **wrong**, and one author surname was misspelled. All have been corrected in the `.tex` and verified in the rebuilt PDF.

**Four verified entries were subsequently removed to meet the 8-page limit** (refs 2 `herrera2010`, 14 `bai2020`, 21 `ma2019wifi`, 22 `cai2024`; see Part G); the surviving **22** entries below keep their audited metadata, and all four removals are marked. The numbering in this table is the pre-cut bibliographic order; the printed PDF now numbers the 22 survivors in first-citation order.

| # (pre-cut) | Key | Printed metadata | Verification | Action |
|---|---|---|---|---|
| 1 | wilson2010 | IEEE TMC 9(5):621–632, 2010; `10.1109/TMC.2010.8` | DOI resolves to nothing; the paper's DOI is `10.1109/TMC.2009.174` | **DOI FIXED** |
| 2 | herrera2010 | TRC 18(4):568–583, Aug 2010; no DOI | Record correct (canonical DOI `10.1016/j.trc.2009.10.006`, not printed) | OK — **removed (page cut)** |
| 3 | januszkiewicz2018 | Sensors 18(10):3412, 2018; `10.3390/s18103412` | Matches | OK |
| 4 | patwari2010proc | Proc. IEEE 98(11):1961–1973, 2010; `10.1109/JPROC.2010.2079090` | Wrong; correct `10.1109/JPROC.2010.2052010` | **DOI FIXED** |
| 5 | alippi2016 | IEEE TMC 15(10):2585–2598, 2016; `…2504964` | Off by one; correct `10.1109/TMC.2015.2504965` | **DOI FIXED** |
| 6 | li2024 | IEEE TWC 23(11):15784–15797, 2024; `10.1109/TWC.2024.3433011` | Matches | OK |
| 7 | wu2024 | Comput. Commun. **224**:108022, **Oct 2024**; `10.1016/j.comcom.2024.108022` | DOI ok; actual **vol. 231, Feb 2025** | **VOL/YEAR FIXED** |
| 8 | wilson2011 | IEEE TMC 10(5):**632–643**, 2011; no DOI | Actual pages **612–621** (DOI `10.1109/TMC.2010.175`) | **PAGES FIXED** |
| 9 | wang2015har | MobiCom 2015:65–76; no DOI | Correct | OK |
| 10 | wong2024 | Data in Brief 55:110673, 2024; `10.1016/j.dib.2024.110673` | DOI ok; title now reads "…dataset for **enhanced** human activity recognition" | **TITLE FIXED** |
| 11 | sanchez2020 | Remote Sensing 12(12):1995, 2020; `10.3390/rs12121995` | Matches | OK |
| 12 | ramirez2021 | Sensors 21(15):5181, 2021; `10.3390/s21155181` | Matches | OK |
| 13 | milano2024 | Sensors 24(2):376, 2024; `10.3390/s24020376` | DOI ok; author is **M. Laracca**, not "Larocca" | **AUTHOR FIXED** |
| 14 | bai2020 | IEEE Access; `10.1109/ACCESS.2020.3012342` | Matches | OK — **removed (page cut)** |
| 15 | khan2023 | IEEE IoT-J 10(5):4049–4058, 2023; no DOI | Correct (DOI `10.1109/JIOT.2022.3171449`, not printed) | OK |
| 16 | zhou2020 | IEEE Syst. J. 14(4):4919–4930, 2020; no DOI | Correct (DOI `10.1109/JSYST.2019.2961735`, not printed) | OK |
| 17 | zhang2022 | Wirel. Netw., **2023**, no vol/pp; `10.1007/s11276-022-03111-9` | DOI ok; **vol. 30, no. 6, pp. 4685–4698, Aug 2024** | **VOL/PP/YEAR FIXED** |
| 18 | wang2018 | IEEE Access 6:17545–17556, 2018; `10.1109/ACCESS.2018.2815365` | Wrong; correct `10.1109/ACCESS.2018.2805837` | **DOI FIXED** |
| 19 | casar2022 | Comput. Netw. **202**:108712, **Jan 2022**; `10.1016/j.comnet.2021.108712` | DOI ok; actual **vol. 205, Mar 2022** | **VOL/MONTH FIXED** |
| 20 | antonioli2020 | ACM TOPS 23(3):art. 14, 2020; `10.1145/3394497` | Matches | OK |
| 21 | ma2019wifi | ACM CSUR 52(3):art. 58, 2019; `10.1145/3310194` | Matches | OK — **removed (page cut)** |
| 22 | cai2024 | AAAI 38(21):23731–23732, 2024; `10.1609/aaai.v38i21.30544` | Matches | OK — **removed (page cut)** |
| 23 | ryan2013woot | USENIX WOOT 2013; no DOI | Exists (USENIX WOOT papers carry no DOI) | OK |
| 24 | beresford2003 | IEEE Pervasive Comput. 2(1):46–55, 2003; no DOI | Correct | OK |
| 25 | Brown2001 | Statist. Sci. 16(2):101–133, 2001; `10.1214/ss/1009293286` | Typo; correct `10.1214/ss/1009213286` | **DOI FIXED** |
| 26 | Hanley1983 | JAMA 249(13):1743–1745, 1983; `…053030` | Off by one; correct `…053031` | **DOI FIXED** |

**Additional citation-style defect fixed:** the bibliography was numbered in *bibliographic* order, not *first-citation* order (IEEE requires the latter). E.g. the 2nd reference cited in the text was `herrera2010`, printed as **[26]**. All `\bibitem`s were reordered to first-citation order; after the page cut the printed numbering runs [1] Wilson & Patwari, [2] Januszkiewicz, [3] Patwari, [4] Alippi, … [22] Hanley.

**Verified in the rebuilt PDF:** all six corrected DOIs present, all six wrong DOIs gone, corrected volumes/pages/surname present, `Larocca` and `632–643` and `2504964` absent.

---

## Part D — Other camera-ready defects found and fixed

1. **Page-1 copyright line collided with body text.** `pdftotext -bbox` showed the `\IEEEpubid` string at y = 738–749 *on the same baseline* as the last lines of both columns (author footnote `dadoyan@ionio.gr).` at x 165.6–236.4 and right-column text `quantify/this/limit` at x 312–392), i.e. the notice printed **on top of** the text. IEEEtran's default `\IEEEpubidadjcol` / `1.3\baselineskip` pullup was insufficient for this overfull title page, and `\@oddfoot` cannot be patched externally (the page style is re-expanded at shipout). Fixed by baking a −16 pt shift into `\@IEEEpubid` itself. **Verified after rebuild:** text block bottom 747.97 pt, copyright band 753.93–764.94 pt → 5.96 pt clear, inside the 792 pt page.
2. **`tab:cost` overfull hbox (147.3 pt too wide).** The 11-column background-cost table overflowed the text width. Fixed (font `\footnotesize`, `\tabcolsep` 2.5 pt, abbreviated headers). **Verified:** 0 overfull hboxes.
3. **Reference numbering** (Part C).

**Final build state:** 8 pages, **0** overfull hboxes, **0** overfull vboxes, **0** undefined references/citations (the remaining log lines are benign IEEEtran Times font-shape substitutions and a few underfull-hbox notices from two-column justification).

---

## Part E — Items that cannot be closed with the available material

| Item | Why it is open |
|---|---|
| **M1 / Q1** per-cell integer counts | E1 was reconciled without the raw tallies: the 14 per-cell percentages are all exact multiples of 1/60, fixing *n* = 60/cell (20 crossings × 3 blocks; 420 total), and the integer counts 58/56/52/44/36/30/9 (detection) and 56/52/48/40/32/24/6 (classification) reproduce every printed percentage and Wilson bound. **E2 vehicle-distance** per-cell tallies, however, were not preserved, so that table is reported as recorded observer proportions at *n* = 20/cell (no CIs, no invented counts). |
| **M3** ablation & comparison tables | Per-band standalone logs were not recorded (only fused output); a comparison table needs prior-system metrics on a common protocol. |
| **M4** observer agreement E1–E4; 2nd field handset/site | Not collected. |
| **M6(ii)/(iii)/(iv)** Bland–Altman paired data; G4 exclusion table; κ CI | Paired G4 exclusion records and per-pair differences are not in the repo. |
| **m5** public/anonymized artifact link | No repository URL available; offered on request. |
| **m7** campaign commit hash | Exact v2.1 commit not available; only "pinned by hash" can be stated. |
| **R2 general** held-out split | The frozen parameter vector has no train/held-out protocol recorded. |

---

## Part F — One item requiring your confirmation (not a defect I can fix unilaterally)

1. **Provenance conflict in the workspace.** A separate document (`.../workspace-.../MeshCrowd/reviews/response-to-reviewers.md`, responding to the *same* minor-revision review under the earlier "Estimation" title) states the reported results were a **deterministic Monte-Carlo harness** and that "no handset run exists", and proposes replacing the result tables with harness output. This directly contradicts the material this camera-ready is built on (`New Evaluations etc/Eval-Phone.md`, real B2/B3/B5 handset captures). **Please confirm the Oct-Version field provenance is authoritative**; if the harness framing were instead correct, the paper's "first complete physical validation … on an unmodified handset" claim would need to be withdrawn. I did **not** import anything from that conflicting document.

(Part F previously also asked about the page length vs the venue limit; that item is now closed — see Part G.)

---

## Part G — Page cut to the 8-page limit

The camera-ready compiled to **12 pages** at the start of this pass; R1's report states an **8-page** conference limit. The manuscript was cut to **8 pages including references** with **no change to the document class** (kept `journal`), **0 overfull boxes**, and **0 dangling references/citations**. All measured numbers, CIs, provenance wording, and the "de-claimed, not fabricated" vehicle figures were preserved.

**Figures.** Five "illustrative session" screen-capture figures and the architecture diagram were removed; the single canonical result figure `fig:field_det` (`field_envelope.png`, regenerated at *n* = 60) is retained. Its only remaining role is the detection-vs-distance envelope and the vehicle/pedestrian contrast.

**Text.** The page/organisation paragraph, the `tab:cadence` float, and the screenshot-describing content of §III were removed (their numbers are retained in the §V-H prose where substantive). Related Work, the contribution list, §I-B, §II, §III, §IV, §V, the Discussion, and the Conclusions were compressed; the abstract was shortened; §II-E's residual-risk inventory was kept in full (R2-C1) but written as prose rather than a numbered list.

**References.** Four verified but least-load-bearing entries were dropped with their citation sites re-pointed to surviving entries in the same cluster: `herrera2010`, `bai2020`, `ma2019wifi`, `cai2024` (26 → 22). None was requested by a reviewer. The bibliography also had `\itemsep` set to 0 pt (IEEE-permissible compression of the reference block).

**Wording/template.** `transit counting` added to the Index Terms; `wong2024` title corrected to include "enhanced"; one US spelling (`behavior`) normalised to the paper's en-GB (`behaviour`); the DESSERT running head and the `979-8-3195-6683-6/26/$31.00 ©2026 IEEE` copyright line remain exact.

**Residual check after the cut:** all 22 `\bibitem`s are cited at least once; the bibliography is still in first-citation order; no reference to a removed figure or table remains; §III's hard-coded "Section V-F" pointer still resolves to the Displayed-vs-realized subsection.

> **Restoring content.** If the venue's limit is in fact higher, the cheapest reversals are (i) re-adding the four references (≈ 3.5 typeset lines each), (ii) restoring the architecture figure, and (iii) restoring the numbered §II-E risk list. None affects any measured value.

---

*Audit produced from: `review_MeshCrowd_IEEE.md`; the R2 concern wording; the full camera-ready `.tex`; `New Evaluations etc/Eval-Phone.md`; Crossref/doi.org metadata; and positional (`-bbox`) PDF inspection.*
