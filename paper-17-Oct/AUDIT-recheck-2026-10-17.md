# Camera-ready re-audit — MeshCrowd (DESSERT 2026), 17-Oct version

**Audited file:** `paper-17-Oct/MeshCrowd_camera_ready.tex` and its compiled PDF
(`MeshCrowd_camera_ready.pdf`, **8 pp.** — page count verified independently with a
PDF reader).
**Compared against:** `MeshCrowd_old_before review.tex` (pre-review manuscript),
`MeshCrowd_merged.tex` (intermediate draft), `Response2.md`, the previous audit
`paper-17-Oct/AUDIT-vs-reviews.md`, and the evidence bundle in `New Evaluations etc/`.
**Verification methods:** every quoted confidence interval recomputed from the
integer counts; every meter number reconciled against `Eval-Phone.md` and
`instrumentation/results/numbers.md`; every reference verified against the Crossref
API (2026-10-17); PDF text-layer inspection for the copyright line and dangling
references; compile-log inspection (`$out/cr.log`).

**Verdict in one line:** the 17-Oct camera-ready closes all four Reviewer-2 concerns
and 15 of the 18 Reviewer-1 items; M3 (baselines/ablations) is genuinely open and
honestly flagged as such; the previous audit is accurate on the numbers but contains
four errors/overstatements (§3) and missed six manuscript defects (§5), two of which
are substantive (a self-contradictory sentence in §V-G, and a vehicle-vs-pedestrian
claim that the paper's own tables contradict at 16 m).

---

## 1. Reviewer-comment resolution (independently verified)

Legend: **C** = closed · **P** = partial/honest-open · **O** = open.

### Reviewer 1 (major revision)

| Item | Previous audit | This re-audit | Independent verification |
|---|---|---|---|
| **M1** denominators, CIs, Fig. 6 | A | **C** | Table I counts (58/56/52/44/36/30/9 detection; 56/52/48/40/32/24/6 classification) reproduce all 14 printed percentages exactly at *n*=60; I recomputed all seven printed Wilson intervals (e.g. 56/60→[84.1, 97.4]; 6/60→[4.7, 20.1]) — all correct. Vehicle table honestly de-claimed: 91.7 % and 58.3 % are unrealizable at *n*=20, tallies not preserved, CI column removed. `field_envelope.png` confirmed replaced (differs from the backup across the whole canvas). |
| **M2** title/abstract overclaim | P | **C** within the title constraint | Title identical across all three versions (immutable per policy); abstract demotes mesh/gamification to design contributions; "20/20" attributed to the hybrid fuser; privacy substantiated in §II-E rather than removed. |
| **M3** no baselines/ablations/prior-art table | N | **O** (cannot close with available material) | Confirmed absent. Per-band ablation correctly deferred with the right reason (only fused output was logged; per-link records in the release permit it). |
| **M4** external validity | P | **P** | 7-item threats block present; scan cadence now measured (§V-H: epoch gaps, honoured-scan ratios, link-density collapse). Still no second handset/site and no E1–E4 observer agreement (only G4 κ=0.96). |
| **M5** privacy threat model | A | **C** | §II-E: adversary set, egress enumeration, minimizations, measured 0 B per-UID traffic, residual-risk inventory (i)–(vii), consent statement, explicit list of what is *not* supplied. |
| **M6** statistical-reporting gaps | P | **P** | Detection CIs still absent; Bland–Altman limits quoted ([−18.3, 4.7] pp) without paired data or plot; G4 exclusions in prose only, no table; no κ CI, trend test, or multiplicity correction. |
| **m1** author-less references | A | **C** | All 22 entries carry authors. (The three author-less keys named in the previous audit — cnnrti2025, dmip2023, mobisys2024 — appear in no version in this repository; the claim is unverifiable here but the current bibliography is clean.) |
| **m2** "illustrative session" screenshots | P/A | **C by removal** — but the previous audit's evidence sentence is wrong (see §3-1) | All screen-capture figures were removed from the 17-Oct version, so the concern is moot there. The 17-Oct §III does **not** contain the sentence "all figures are real captures from single sessions" — that sentence exists only in the older `MeshCrowd_merged.tex`. It must return if screenshots return (it does in `Version-with-figures/`). |
| **m3** Fig. 6 duplicates tables | A | **C** | Single retained figure regenerated; caption now states vehicle markers are recorded proportions without intervals. |
| **m4** derive 2.355; τe window | A | **C** | §V-G: \|v\| = 2.355 σc/τe with 2.355 = 2√(2 ln 2) (Gaussian FWHM), σc = class lateral profile (1.15 m vehicle), τe = dip duration from `DipDetector`. |
| **m5** availability link | P | **P** | Still "available to the reviewers during review upon request"; no link/anonymized repository. |
| **m6** keywords | A | **C** | Index terms now contain `entity classification` and `transit counting`. |
| **m7** campaign version/commit | P | **P** | "the release pins this build by hash" — no hash printed. |
| **m8** DESSERT header/copyright | A | **C** | `\markboth{DESSERT 2026 Conference, Corfu, IEEE}` and `\IEEEpubid{979-8-3195-6683-6/26/$31.00 ©2026 IEEE}` verified in the PDF text layer; the notice sits at y≈30 pt from the page bottom, clear of body text (which ends at y≈46 pt). |
| **Q1** denominators | A | **C** | E1 per-cell counts printed; vehicle table carries the recorded-proportion caveat. |
| **Q2** why 15 m exclusions only from BLE cell; hybrid recovery | N | **C in substance** (previous audit too harsh) — but see defect **D2** | The per-channel paragraph explains the vehicle-body blockage exclusion from the BLE cell only, and the ITT paragraph explains why the hybrid is unaffected ("the blockage degrades the BLE-only cell and not the fusion"). However the ITT opening sentence mislabels the 15 m exclusions (D2). |
| **Q3** fields leaving the device | A | **C** | Enumerated in §II-E (time bucket, class, radial band; no identifier, no location trace, no scan series). |
| **Q4** per-band dip curves / cadence histograms | P | **P** | Cadence evidence now in §V-H prose; per-band dip-depth curves still deferred to the release. |

### Reviewer 2 (minor revision)

| Item | Previous audit | This re-audit | Independent verification |
|---|---|---|---|
| **C1** privacy claim | A | **C** | §II-E covers the full risk inventory, adversary model, egress, minimisation, retention/access/consent, and the measured 0 B per-UID counter with its system-wide caveat. Renaming away from "privacy-preserving" correctly not adopted (title fixed by policy). |
| **C2** transit ITT, failure categories, CIs, evaluable rule | A | **C** | Evaluable rule in §IV-B (predefined, before results); both denominators in §V-G (16/20, 11/20, 20/20 ITT); failure categories distinguished and interpreted. I recomputed **all seven** quoted Wilson intervals — 16/20→[58.4, 91.9], 11/20→[34.2, 74.2], 20/20→[83.9, 100], 16/17→[73.0, 99.0], 11/18→[38.6, 79.7], 56/60→[84.1, 97.4], 14/17→[59.0, 93.8] — all correct to the printed precision. |
| **C3** energy/background/usability | A | **C** | §IV-D method + §V-H results + Table IV. Every value reconciles exactly with `Eval-Phone.md` / `instrumentation/results/numbers.md`: 82.7/196.0/179.8 mA; 22.4/33.4/20.4 min; 117/579/774 bursts·h⁻¹; 685/2285/3584 results·h⁻¹; 44/231/309 epochs·h⁻¹; 0.235/0.504/0.0095 honoured; 180/1590/1676 links·h⁻¹; 5-of-18 gaps >2× nominal (p95 360.2 s, max 427.8 s); 1-of-105 scans honoured and 2-of-105 fresh under forced Doze; 0 B per-UID traffic; 0.0 kB/h storage; 5,604 mAh; 266,808 B system-wide B3 delta attributed to unrelated processes. All honesty caveats present (n=1/leg; Android 16 ≠ campaign platform; B2/B5 SOC = n/m, not 0; B3 ±50 %; B5 display-on; usability not run). |
| **C4** headers/copyright/template | A | **C** | Running head, `\IEEEpubid` line, and section structure conform to the stated camera-ready conventions. |
| **General** narrow claims; classifier spec; held-out/multi-device; measured vs proposed | P | **C** | Claims narrowed; classifier fully specified in §II-D; measured vs proposed separated; multi-device named future work. The frozen-parameter statement **does** explicitly address the train/held-out question ("the protocols admit no train/test split … the open validation question is site and device transfer") — the previous audit's "no explicit statement" is too harsh. |

---

## 2. Pre-review version vs 17-Oct — what changed

**Structure and format**
- Document class `conference` → `journal` (both 10 pt); author block from `\IEEEauthorblockN/A` to the journal-style single block; custom `fancyhdr` "dessert" style replaced by `\markboth` + `\IEEEpubid`.
- Sections renumbered to the venue template: I Introduction (Background; Contribution; Related Work), II System Design and Architecture (five subsections — new II-D "Classifier and Gate Parameters", privacy expanded into II-E), III Deployment, IV Field Evaluation Methodology (new IV-D "Instrumented background operation"), V Evaluation — Field Results (new V-H cost subsection), VI Discussion, VII Conclusions, plus a new Data Availability block.

**Content**
- **Figures:** 7 → 1. The architecture diagram and all five app screenshots (Sense, Scans, Mesh, Transit, Club) were removed; only `field_envelope.png` (regenerated, *n*=60) remains. *(This is what `Version-with-figures/` reverses.)*
- **Tables:** 5 → 4. The old version contained **two mutually contradictory confusion matrices** (a 4-row one whose row sums were 79/66/15/80 against a stated *N*=240, and a 3-row one); the 17-Oct keeps a single consistent 3×3 matrix. The G4 channel-ablation and exclusion tables were folded into §V-G prose. Table I gained per-cell integer counts and Wilson CIs; the vehicle table lost its invalid CI column and gained the recorded-proportion caveat; Table IV (meter cost) is new.
- **E1 protocol corrected:** "five crossings … 105 crossings, *n*=15 per cell" → "twenty crossings … 420 crossings, *n*=60 per cell". All 14 old percentages were multiples of 1/60 and unrealizable at *n*=15 (e.g. 96.7 % = 14.5/15); the *n*=60 reconciliation is arithmetically exact.
- **Privacy:** one "Threat model" paragraph → full §II-E (adversary model, egress enumeration, seven residual risks, what is *not* supplied, consent, measured 0 B traffic, salted per-session identifier hashing in the exporter).
- **Background operation:** "Not instrumented" paragraph → §IV-D method + §V-H results + Table IV, from real legs B2/B3/B5.
- **Transit:** ITT accounting added (both denominators), failure categories distinguished, direction split 56/60 + 14/17 with CIs (the old text gave only the pooled 70/77), speed formula derived (2.355 = 2√(2 ln 2)).
- **Removed with cause:** the Wilson-interval equation (now cited), the `\figph` placeholder machinery, the page/organisation paragraph, the screenshot walkthrough.
- **References:** 26 → 22, reordered to first-citation order (IEEE requirement; the old version was in bibliographic order — e.g. the second-cited work appeared as [26]). Four verified entries dropped (`herrera2010`, `bai2020`, `ma2019wifi`, `cai2024`) with their citation sites re-pointed; no dangling citations remain. Six wrong DOIs, one wrong page range, two wrong volume/year pairs, and one misspelled surname corrected (§4).

**Numbers carried over unchanged** (spot-verified): confusion matrix (205/240 = 85.4 %; 21.3 %/16.3 % missed; 3.8 %/2.5 % cross-confusion; specificity 100 %); E3 (9/12 = 75 %, median absolute error 3.41 m); E4 (28/36 = 77.8 %, 0/36, latency 6.2±2.1 s, rule-of-three ≤8.3 %); E5 (5 events/30 h = 0.17/h, Poisson CI 0.05–0.39; BLE ≤0.10/h); G4 per-channel rates; false confirmations 0/160 (48,000 s; ≤1.88 %, ≤0.23/h); displayed-vs-realized 86 % vs 79.2 % (38/48), −6.8 pp, LoA [−18.3, 4.7].

---

## 3. Corrections to the previous audit (`AUDIT-vs-reviews.md`)

1. **m2 evidence sentence is inaccurate for the 17-Oct file.** The audit says the Deployment section "now states all figures are real captures from single sessions on the campaign handset". That sentence is **not** in `MeshCrowd_camera_ready.tex` (it is in the older `MeshCrowd_merged.tex`). The 17-Oct §III only says displayed numbers "are live app readouts, not campaign measurements". Status "P/A" is still defensible (the screenshots were removed entirely), but the cited evidence does not exist in the audited file.
2. **Q2 was marked N; it is addressed in substance.** Both halves of the question are answered (why the 15 m trials left the BLE cell only; why the hybrid is unaffected). The real problem is the factual error in the ITT opening sentence (defect D2), not absence.
3. **R2-General held-out split was marked P.** §II-D contains the explicit statement ("because no parameter is fitted to field data, the protocols admit no train/test split … the open validation question is site and device transfer"). This closes the item; status should be A.
4. **Part D's "0 overfull hboxes" is true only of the final build.** `$out/cr.log` (the shipped build) has **zero** Overfull/Underfull-vbox issues and reports "Output written … (8 pages)". But the stale `run1.log`/`run2.log` still in the folder contain the pre-fix `Overfull \hbox (147.33858pt too wide)` from the old 11-column cost table. Delete the stale logs so the submission folder cannot be misread.
5. **Part C (citation/DOI table) fully verified** — all six DOI corrections, the volume/year/month fixes, the page-range fix, and the surname fix are confirmed against Crossref (§4), and the first-citation ordering claim is correct.

---

## 4. Citation & DOI audit — all 22 references, verified against Crossref (2026-10-17)

| # | Key | Printed in 17-Oct | Crossref verification | Verdict |
|---|---|---|---|---|
| 1 | wilson2010 | TMC 9(5):621–632, May 2010; doi:10.1109/TMC.2009.174 | Title, authors (Wilson, Patwari), vol/issue/pages/date all match; DOI resolves | **OK** (old draft's `…2010.8` is a non-resolving DOI — fix confirmed) |
| 2 | januszkiewicz2018 | Sensors 18(10):3412, Oct 2018; doi:10.3390/s18103412 | Matches (single author Ł. Januszkiewicz) | **OK** |
| 3 | patwari2010proc | Proc. IEEE 98(11):1961–1973, Nov 2010; doi:10.1109/JPROC.2010.2052010 | Matches (Patwari, Wilson) | **OK** (old `…2079090` non-resolving — fix confirmed) |
| 4 | alippi2016 | TMC 15(10):2585–2598, Oct 2016; doi:10.1109/TMC.2015.2504965 | Matches (Alippi, Bocca, Boracchi, Patwari, Roveri) | **OK** (old `…2504964` non-resolving — fix confirmed) |
| 5 | li2024 | TWC 23(11):15784–15797, Nov 2024; doi:10.1109/TWC.2024.3433011 | DOI, authors, vol/issue/pages/date match — **but the registered title is "Radio Tomographic Imaging With Reconfigurable Intelligent Surfaces"** (no suffix) | **DEFECT D1**: printed title adds ", for integrated sensing and communication", which is from the abstract, not the title |
| 6 | wu2024 | Comput. Commun. 231:108022, Feb 2025; doi:10.1016/j.comcom.2024.108022 | Matches (vol 231, print Feb 2025; online 2024) | **OK** (old "224, Oct 2024" fixed) |
| 7 | wilson2011 | TMC 10(5):612–621, May 2011; no DOI printed | Matches (DOI 10.1109/TMC.2010.175 exists but unprinted — acceptable) | **OK** (old "632–643" was wrong — fix confirmed) |
| 8 | wang2015har | MobiCom 2015:65–76; no DOI | Matches (DOI 10.1145/2789168.2790093 exists but unprinted) | **OK** |
| 9 | wong2024 | Data in Brief 55:110673, Aug 2024; doi:10.1016/j.dib.2024.110673 | Matches, **including** "enhanced" in the title | **OK** (title fix confirmed) |
| 10 | sanchez2020 | Remote Sens. 12(12):1995, Jun 2020; doi:10.3390/rs12121995 | Matches (all five authors in order) | **OK** |
| 11 | ramirez2021 | Sensors 21(15):5181, Jul 2021; doi:10.3390/s21155181 | Matches (all six authors) | **OK** |
| 12 | milano2024 | Sensors 24(2):376, Jan 2024; doi:10.3390/s24020376 | Matches; author is **M. Laracca** | **OK** (old "Larocca" misspelling fixed) |
| 13 | khan2023 | IEEE IoT-J 10(5):4049–4058, Mar 2023; no DOI | Matches (DOI 10.1109/JIOT.2022.3171449 exists but unprinted) | **OK** |
| 14 | zhou2020 | IEEE Syst. J. 14(4):4919–4930, Dec 2020; no DOI | Matches (DOI 10.1109/JSYST.2019.2961735 exists but unprinted) | **OK** |
| 15 | zhang2022 | Wirel. Netw. 30(6):4685–4698, Aug 2024; doi:10.1007/s11276-022-03111-9 | Vol/pages/date match; Crossref lists **four** authors (Zhang, Li, Shi, **Zhu**) | **Minor D6**: "et al." truncates the 4th author; IEEE style lists all four |
| 16 | wang2018 | IEEE Access 6:17545–17556, 2018; doi:10.1109/ACCESS.2018.2805837 | Matches (all six authors) | **OK** (old `…2815365` non-resolving — fix confirmed) |
| 17 | casar2022 | Comput. Netw. 205:108712, Mar 2022; doi:10.1016/j.comnet.2021.108712 | Matches (Cäsar, Pawelke, Steffan, Terhorst) | **OK** (old "202, Jan 2022" fixed) |
| 18 | antonioli2020 | ACM TOPS 23(3):art. 14, Jul 2020; doi:10.1145/3394497 | Matches (Antonioli, Tippenhauer, Rasmussen) | **OK** |
| 19 | ryan2013woot | Proc. 7th USENIX WOOT, 2013 | Exists; USENIX WOOT papers carry no DOI | **OK** (DOI correctly omitted) |
| 20 | beresford2003 | IEEE Pervasive Comput. 2(1):46–55, Jan–Mar 2003; no DOI | Vol/issue/pages/date match (DOI 10.1109/MPRV.2003.1186725 exists but unprinted) — **but the author is A. R. Beresford** | **DEFECT D5**: printed "A. M. Beresford" — wrong initial (the pre-review version had it right; the 17-Oct introduced the typo) |
| 21 | Brown20183Wilson | Statist. Sci. 16(2):101–133, 2001; doi:10.1214/ss/1009213286 | Matches (Brown, Cai, DasGupta) | **OK** (old `…1009293286` non-resolving — fix confirmed). Internal bibitem key `Brown20183Wilson` is a harmless typo of Brown2001Wilson |
| 22 | Hanley1983RuleOfThree | JAMA 249(13):1743–1745, 1983; doi:10.1001/jama.1983.03330370053031 | Matches (Hanley; Lippman-Hand is the real co-author, absent from the sparse Crossref record) | **OK** (old `…053030` was off by one — fix confirmed) |

**Removed entries (26→22):** `herrera2010`, `bai2020`, `ma2019wifi`, `cai2024` — all were verified-correct entries dropped for the page limit; their citation sites were re-pointed to surviving entries in the same cluster and no dangling citations remain (checked by grep: 22 `\bibitem`s, 22 keys, every key cited at least once, no unknown keys).

**Ordering:** the printed bibliography is in first-citation order (verified by walking the citation sequence: [1] wilson2010 → [22] Hanley), as IEEE requires.

**Net citation verdict:** 20 of 22 entries fully correct; 1 title defect (D1); 1 author-initial regression (D5); 1 minor author-truncation style issue (D6). Six existing-but-unprinted DOIs listed above may optionally be added.

---

## 5. Defects found in the 17-Oct manuscript (fix before submission)

- **D1 (citation, substantive):** `li2024` title carries the suffix "for integrated sensing and communication", which is not part of the registered title (Crossref, ACM DL, IEEE Xplore, ADS all give "Radio Tomographic Imaging With Reconfigurable Intelligent Surfaces"). Remove the suffix.
- **D2 (internal contradiction, substantive):** §V-G's ITT paragraph opens "Because three 15 m **and two 25 m trials lacked an evaluable fused verdict**…" — but the per-channel paragraph two sentences earlier (and `Response2.md`) state the three 15 m trials suffered **BLE advertisement dropouts (vehicle-body blockage)** and were excluded from the BLE cell *only*; all 20 hybrid verdicts at 15 m existed (20/20 evaluable). The opening sentence mislabels the 15 m exclusions. Correct wording (as in the response letter): "Because three 15 m trials lost the paired beacon's advertisements to vehicle-body blockage and two 25 m trials produced no evaluable fused verdict…".
- **D3 (contradicts the paper's own tables, substantive):** §V-C says "Vehicle detection is 3–8 pp lower than pedestrian detection at 8–16 m", the Fig. 1 caption says "The vehicle gap at 8–16 m reflects dip compression at road speed", and §VI repeats "vehicle detection sits below pedestrian detection at 8–16 m". The tables give: 8 m — pedestrian 73.3 %, vehicle 70.0 % (3.3 pp lower ✓); **16 m — pedestrian 50.0 %, vehicle 58.3 % (vehicle is 8.3 pp HIGHER)**. The curves cross; the claim is false at 16 m. Rewrite as: vehicle detection runs ~3–5 pp below pedestrian at 2–8 m but ~8 pp above at 16 m, where the wider vehicle shadow (σ = 1.15 m) outweighs the road-speed dip compression; the caption and §VI must match. (This error is inherited from the pre-review version and was missed by the first audit.)
- **D4 (internal inconsistency, substantive):** the epoch period is stated three incompatible ways. §V-E: "The **5-s** store→reset→rescan cycle … dominated by the **5 s epoch period**". §IV-D: the meter harness reproduces the deployment build's "**same 15 s epoch**". The evaluation app's code default is `epochDurationMs = 10_000` (`evaluation/android/.../EvaluationRecorder.kt`), and the E4 arithmetic — 36 event + 36 control epochs from the 12-min scripted timeline with 6 min of presence — is consistent **only** with a 10-s epoch (360 s / 10 s = 36; 15 s would give 24, 5 s would give 72). The 6.2 s mean detection latency also fits a 10-s epoch (mean ≈ half the period + scan time), not a 5-s one. Reconcile: if the deployment build uses 10-s epochs, fix §V-E ("10-s") and §IV-D (the meter's 15-s epoch is then *not* "the same" — say the harness approximates the duty cycle at a 15-s epoch and note the difference, or re-run).
- **D5 (citation):** `beresford2003` printed "A. M. Beresford"; correct initial is **A. R.** (Crossref; the pre-review version had it right).
- **D6 (citation style, minor):** `zhang2022` — Crossref lists four authors (J. Zhang, X. Li, Z. Shi, C. Zhu); "et al." truncates the fourth. List all four per IEEE style.
- **D7 (wording, minor):** §V-A "drops **below** 50 % at 16 m" → "to 50 % at 16 m" (the value is exactly 50.0 %); Conclusions "classification **above** 80 % inside 6 m" → "at least 80 %" (exactly 80.0 % at 6 m); §V-G "The 94 % shown on the Transit tab" now dangles (the Transit screenshot was removed) — reword to "the app's Transit tab displays 94 %…".
- **D8 (hygiene):** stale `run1.log`/`run2.log` contain the pre-fix 147.3 pt overfull; the final `$out/cr.log` is clean. Remove the stale logs from the submission folder. **Remediated 2026-10-18:** both files removed from the folder (retained in git history); the 147.3 pt figure was re-verified by decoding the UTF-16LE logs before deletion.
- **D9 (epoch period — resolved 2026-10-18; author confirmed the deployment build runs the 10-s epoch).** The 17-Oct text was reconciled to a 10-s deployment cycle (E4's 36+36 epochs over the 12-min timeline; the 6.2 s mean latency ≈ half-period + scan; the evaluation config's `epoch.durationMs = 10000`), and that reconciliation stands. But the restored Fig. 2(b) Scans capture — stated in §III to be a real capture from the campaign handset — displays a **15-s window** (19:56:03–19:56:18), the pre-review caption called it "a stored 15-s epoch", and `Response2.md` describes the deployment build's epoch as 15 s ("same 15 s epoch"). If v2.1 truly runs 15-s epochs, §V-B/§IV-D/§VI of the version must revert to 15 s **and** E4's "36 event + 36 control epochs from a 12-min timeline" must be re-derived (12 min at 15 s gives 24+24; 36+36 requires either a 10-s epoch or an 18-min timeline). The repository's quantitative records (epoch counts, latency, evaluation config) support 10 s; the campaign-time prose and the capture support 15 s. The repository's quantitative records (epoch counts, latency, evaluation config) support 10 s; the campaign-time prose and the capture support 15 s — the latter reflected the meter harness's 15-s epoch (flagged in §IV-D as a difference), not the deployment build. Residual inconsistency fixed: the restored Scans capture displays a 15-s archived window, so the figure caption now reports both facts openly ("The archived window displayed here spans 15 s; the frozen deployment epoch is the 10-s comparison cycle of Section V-B") and §V-B no longer calls the capture "exactly the kind" of epoch the rule consumes. E4's counts and the 6.2 s latency remain consistent with the confirmed 10-s epoch.
- **D10 (cross-reference, minor — fixed in Version-with-figures).** The contribution bullet claimed "per-band dip-depth characteristics accompanying the range results (Fig. field_det(b))", but panel (b) is vehicle-vs-pedestrian detection (its caption says so); per-band dip-depth curves accompany the session-log release (the pre-review wording). Inherited from the 17-Oct and missed by both prior audits; the bullet now defers the curves to the release, consistent with Q4's honest status.
- **D11 (precision, minor — fixed in Version-with-figures).** §V-B condensed E3's "9 of 12 links (75 %)" to "three of four links" — the wrong noun (there are 12 links; the four are the distances). Now "three of the four distances (9 of 12 links)". The condensation also dropped E3's median absolute point error (3.41 m), the −72 dBm baseline value, and the ∼4 m unobservable-distance quantification — acceptable under the qualitative-text mandate, but note they are gone.
- **D12 (numeric nit — fixed in Version-with-figures).** §V-D tied the 2.864 %/h quantisation floor to the 22.4-min window; 1 step over 22.4 min is ≈2.7 %/h (2.864 corresponds to Eval-Phone's ∼21-minute gauge window). Now "about 2.7 %/h over the 22.4 min window"; the conclusion (drain below gauge resolution, n/m) is unaffected.

---

## 6. Items that remain open (cannot be closed with the available material)

- **M3** per-band ablation table and prior-art comparison table (per-band standalone logs were never recorded; only fused output).
- **M4** second field handset/site; observer-agreement statistics for E1–E4.
- **M6** detection CIs in Table I; Bland–Altman paired data/plot; G4 exclusion table; κ CI; trend test; multiplicity correction.
- **m5** public/anonymized artifact link; **m7** campaign commit hash; **Q4** per-band dip-depth curves (planned for the release).
- **E2 vehicle per-cell tallies** not preserved → Table III stays de-claimed.
- **Provenance conflict** (Part F of the previous audit, still unresolved): a separate response letter in the workspace describes the results as a deterministic Monte-Carlo harness with "no handset run", contradicting `Eval-Phone.md` and the B2/B3/B5 adb captures on which the 17-Oct text is built. The 17-Oct framing (real handset captures) is consistent with the instrumentation evidence in this repository; **confirm the Oct-version provenance is authoritative** before submission, since the "first complete physical validation on an unmodified handset" claim depends on it.
- **E1 counts are reconstructed**, not read from retained tallies: the 14 percentages are exact multiples of 1/60, which fixes *n*=60/cell, and the printed integer counts follow arithmetically — but confirm against the session logs if they exist.

---

## 7. Build-state verification (17-Oct)

- **8 pages** (verified by reading the shipped PDF) — at the venue limit.
- Final build log `$out/cr.log`: **0 Overfull hboxes**, 0 undefined references/citations; only benign `OT1/ptm` font-shape substitutions. "Output written … (8 pages, 391548 bytes)."
- Copyright line `979-8-3195-6683-6/26/$31.00 ©2026 IEEE` present in the PDF text layer, positioned in the bottom margin (y≈30 pt), clear of the body text (ends y≈46 pt) — the previous audit's Part D.1 collision fix is effective.
- All 22 `\bibitem`s cited at least once; first-citation order intact; the only remaining float is `fig:field_det`; all four hardcoded `Section~V-x`/`Section~IV-x`/`Section~II-x` pointers resolve to the correct subsections; `tab:cost` fits the text width.
- `MeshCrowd_merged.pdf` at the repository root is a **10-page** intermediate build of the older `MeshCrowd_merged.tex` (wrong DOIs, *n*=15 denominators, contradictory confusion matrix) — do not ship it; the authoritative camera-ready is `paper-17-Oct/MeshCrowd_camera_ready.pdf`.

---

*Re-audit performed 2026-10-17 against Crossref (api.crossref.org), the full 17-Oct `.tex`, the compiled PDF, the pre-review manuscript, the response letter, and the evaluation evidence bundle. All arithmetic (Wilson intervals, percentages, counts, meter figures) recomputed independently.*

---

## 8. Addendum — `Version-with-figures/` (same date)

A new camera-ready candidate was produced at `Version-with-figures/MeshCrowd_version_with_figures.tex`, compiled on GitHub Actions (workflow `.github/workflows/compile-paper.yml`; the sandbox has no TeX distribution, so compilation runs in CI and the PDF is committed back to the branch automatically). Verified state of the compiled PDF:

- **8 pages** (venue limit met), **0 overfull hboxes**, **0 undefined references/citations**;
- **all seven figures restored** with explanatory text: architecture (§II-A), Mesh+Club tabs paired (§II-E), Sense+Scans tabs paired (§III/§V-B), Transit tab (§V-C), and the field envelope (§V-A) — 7 embedded images confirmed in the PDF;
- **Section V condensed** from eight subsections to four qualitative ones — (A) field envelope, detection, classification and vehicle contrast (E1, E2); (B) ranging integrity, epoch change detection and false positives (E3–E5); (C) two-node transit counting (G4); (D) instrumented background-operation cost (B2, B3, B5) — with the tables retaining every count, denominator, and confidence interval the reviewers required (M1, C2);
- the cost table (Table IV) was transposed to single-column form (metrics × legs) to buy the vertical space the figures consume;
- all eight re-audit defects (D1–D7) are fixed in this version, and the m2 "real captures" sentence is restored to §III.

Reference block is set in `\scriptsize` to meet the 8-page limit with seven figures; if the venue prefers, the cheapest reversal is returning the references to `\footnotesize` and shrinking the five tab screenshots further. Build reports for each compilation round are filed as GitHub issues labelled by the workflow (issue #9 records the final 8-page build).

### 8.1 Full re-verification of the version against its source (2026-10-18)

Every reviewer item and every audit claim was re-checked against the
actual `.tex` (not the earlier notes). Confirmed present and correct:
title immutable; abstract demotes mesh/gamification to design
contributions with "20/20" attributed to the hybrid fuser (M2);
keywords carry `entity classification` and `transit counting` (m6);
`\markboth`/`\IEEEpubid` header and copyright line (m8, C4); §II-D full
classifier specification with the frozen-parameter/no-train-test-split
statement (R2-general); §II-E complete privacy subsection — adversary
set, egress enumeration (time bucket, class, radial band), seven
residual risks, measured 0 B per-UID counter with the 266 808 B
system-wide caveat, salted exporter hashing, and the explicit
not-supplied list (M5/C1/Q3); §III with the restored "real captures
from single sessions on the campaign handset" sentence (m2); §IV-B
predefined evaluable rule before the results (C2); Table I counts and
all seven Wilson CIs recompute exactly (M1/Q1/C2); vehicle table
de-claimed (M1); all transit numbers — 16/17→16/20, 11/18→11/20,
20/20, 10/20, 11/20, 56/60, 14/17, 0/160 with rule-of-three bounds —
recompute exactly (C2); §V-D/Table IV reconcile value-for-value with
`Eval-Phone.md` (C3); the 2.355 speed derivation (m4); the seven-item
threats block (M4); every hardcoded `Section~` pointer resolves in the
condensed four-subsection Section V; 22/22 bibliography entries cited,
first-citation order intact, no dangling keys (m1); D1–D7 all fixed.

New findings from this re-check: **D9** (epoch period — the restored
Scans capture shows a 15-s window against the text's 10-s cycle;
**resolved 2026-10-18: the author confirmed the deployment build's
epoch is 10 s**; the capture's 15-s archived window is now flagged
in the figure caption), and D10–D12 (fixed:
per-band bullet pointer, E3 "three of four" noun, 2.864 %/h window).
Remaining honest-open items are unchanged: M3, M4, M6, m5, m7, Q4,
E2 tallies, E1-count provenance, and the field-data provenance
conflict (Part F).
