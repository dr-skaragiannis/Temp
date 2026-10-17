# Response to Reviewer Comments — MeshCrowd

**Manuscript:** MeshCrowd: Privacy-Preserving Crowd and Vehicle Sensing using Gamified Mesh Networks
**Venue:** DESSERT 2026 Conference (IEEE)
**Review outcome:** Accept with minor revision
**Files referenced:** `MeshCrowd_merged.tex` (revised manuscript), `New Evaluations etc/` (new instrumentation and evaluation material)

We thank the reviewer for the careful reading and for the constructive assessment of the
field-measurement core. The review identifies four minor concerns; we address each below,
stating exactly what changed, where it changed in the revised manuscript, and — where a
concern could not yet be closed with data — what remains open and why. We do not upgrade any
claim by implication: every number quoted in this response is traceable to a capture in
`New Evaluations etc/instrumentation/runs/`, and quantities that were not measured are
labelled as such.

We also confirm at the outset: **the paper title is unchanged**, exactly as required during
the revision/final-acceptance phase.

---

## Coverage summary

| # | Reviewer concern | Status | Evidence |
|---|---|---|---|
| 1 | Privacy claim incomplete / potentially overstated | **Addressed** (adversary model + risk inventory in §II-D); further hardened with *measured* data-minimization evidence and a concrete identifier-protection mechanism | Revised §II-D; new measured mobile-traffic counters (0 B, all legs); salted per-session identifier hashing in the export path |
| 2 | Two-phone transit: exclusions, intent-to-treat, failure categories, CIs, evaluable rule | **Addressed in the revised manuscript** — all four requested items are now present (§IV-B rule; §V-G accounting) | Revised §IV-B, §V-G |
| 3 | No energy, background-operation, or usability measurements | **Largely addressed with new measurements** (battery, background limits, storage/traffic, screen-off scan availability); usability/permission-burden study is designed but **not yet executed** and is reported as an open item, with no numbers claimed | `New Evaluations etc/Eval-Phone.md`; legs B2/B3/B5 in `instrumentation/runs/`; paste-ready tables in `instrumentation/results/` |
| 4 | Correct headers per template; copyright line; title immutability | **Addressed** — camera-ready template conformance, copyright line, PDFeXpress verification listed in the camera-ready checklist below | Checklist section of this letter |

---

## Comment 1 — The privacy claim is incomplete and potentially overstated

**Reviewer's request:** distinguish "no camera/microphone ≠ privacy preservation"; analyse
identifiers in scan results, local RSSI/timing exposure, geo-tagged epochs, occupancy
patterns from repeated records, mesh-peer inference, linkability of time-bucketed records,
and non-consenting bystanders; define privacy model, adversary capability, retention,
cryptographic protection, access control, consent policy, data minimisation.

**Response:** We agree completely, and the revised manuscript now implements the reviewer's
distinction verbatim as the organising principle of a dedicated subsection,
**§II-D "Distributed Sensing and Privacy"**, which opens with the explicit statement
`no camera/microphone ≠ privacy preservation`. The reviewer's risk inventory is addressed
one-to-one:

| Reviewer's risk | Where addressed in revised §II-D |
|---|---|
| BLE/Wi-Fi scan results contain identifiers before ephemeral processing | Residual risk (i): the sensing phone observes third-party addresses transiently at the radio layer, before on-device reduction |
| Local raw RSSI and scan timing reveal nearby device presence | Residual risk (ii): the local log and its timing reveal which devices were in range |
| Geo-tagged epochs reveal operator location/movement | Residual risk (iii) |
| Repeated crossing records expose occupancy patterns | Residual risk (iv), with the spatio-temporal correlation citation |
| A mesh participant can infer activity at a fixed sensing location | Residual risk (v) |
| Time-bucketed class/range records are linkable across exports | Residual risk (vi) |
| Target-device-free sensing monitors non-consenting people | Residual risk (vii); consent is structurally unavailable from bystanders and is stated as such |

The subsection now also defines the **adversary capability** explicitly: a curious mesh
peer, a passive observer of mesh traffic, and a recipient of exported logs, each with
arbitrary compute but no access to an unlocked handset and no access to measurements before
on-device reduction; under this model a peer learns coarse flow at most, and identifying an
individual requires an auxiliary claim the system never makes.

**What leaves the device is enumerated** (answering the implicit question behind this
comment): a mesh confirmation carries only a time bucket, a class, and a radial band — no
identifier, no location trace, no scan series.

**New additions enabled by the revised evaluation material** (two concrete upgrades beyond
the prose):

1. **Measured data minimisation.** Per-UID mobile traffic was **0 bytes in all three
   measured operating conditions** (screen-off background sensing, operator view, and forced
   deep idle), captured with independent `netstats` per-UID samples; app-private storage
   growth was **0.0 kB/h** in every leg. This converts the architectural assertion
   "observation stays on the handset" into a measured counter, including in the deep-idle
   regime where a platform might otherwise defer traffic. The manuscript now states the
   measurement and the caveat together (the handset's *system-wide* mobile counter moved by
   266 808 B during one leg due to unrelated processes; the per-UID counter is the figure
   attributable to the sensing service).
2. **Concrete identifier protection in the export path.** The JSON session exporter
   (`New Evaluations etc/evaluation/android/`) hashes SSIDs, BSSIDs, and BLE addresses with a
   **per-session salt**, so exported records cannot be joined across sessions by identifier.
   This is the first implemented mitigation (identifier rotation class) in the
   aggregation/rotation family the review asks for, and §II-D now names it as such.

**What we deliberately did not claim:** the evaluated build still has **no formal privacy
definition, no retention timer, no remote wipe, no cryptographic protection of the local
store beyond the device lock, and no identity-based admission control for mesh peers**.
§II-D states each of these absences explicitly rather than leaving them implicit, and
rate-limited or noised shared aggregates are listed as design options, not features. Should
the reviewer consider any single one of these mandatory for the word "privacy-preserving" in
the title, we note that the title is fixed by conference policy and that §II-D is written to
scope its meaning precisely to the measured data-minimisation properties above.

---

## Comment 2 — Two-phone transit results: exclusions and intent-to-treat reporting

**Reviewer's request:** intent-to-treat success rate over all initiated trials;
failure-category breakdown; confidence intervals per configuration; a predefined rule for
what counts as "evaluable".

**Response:** All four items are present in the revised manuscript. No new experiments were
required; the G4 campaign recorded enough to report all four, and the revision restructures
§V-G accordingly.

1. **Predefined evaluable rule — revised §IV-B.** A trial is *evaluable* for a configuration
   when the ground-truth crossing timestamp falls inside that trial's barrier window **and**
   the configuration under test returns a terminal verdict; other trials are logged with
   their cause and reported on **both** denominators (initiated and evaluable), never dropped
   silently. This rule is stated in the methodology, before the results.
2. **Intent-to-treat rates — revised §V-G, "Intent-to-treat accounting".** Every rate is now
   reported over all 20 initiated trials per separation as well as per-evaluable:
   - BLE-only at 15 m: 16/17 (94.1 %, CI [73.0, 99.0]) per-evaluable → **16/20 (80.0 %, CI
     [58.4, 91.9]) intent-to-treat**;
   - hybrid through 15 m: 20/20 (CI [83.9, 100]) on **both** denominators;
   - hybrid at 25 m: 11/18 (61.1 %, CI [38.6, 79.7]) per-evaluable → **11/20 (55.0 %, CI
     [34.2, 74.2]) intent-to-treat**.
   The text states explicitly that the hybrid's 20/20 is unchanged between denominators
   *because* the blockage degrades the BLE-only cell and not the fusion — i.e. the
   operational reading is given, exactly as the reviewer asks, so that 20/20 cannot be read
   as stronger than the operational result under real blocking conditions.
3. **Failure-category breakdown.** The two exclusion categories are now distinguished and
   interpreted: (a) *vehicle-body blockage of the paired beacon* — three 15 m BLE trials —
   is a condition a real deployment would also suffer; (b) *missing evaluable fused verdict*
   — two 25 m hybrid trials — is a measurement artifact of this configuration. The text notes
   that the 25 m figure is the one the stricter denominator moves, and why.
4. **Confidence intervals for each configuration.** All per-channel cells (BLE-only, RFCOMM
   only, hybrid), both denominators, and the direction estimates (56/60, CI [84.1, 97.4];
   14/17, CI [59.0, 93.8]) now carry 95 % Wilson intervals; the zero-false-confirmation
   result keeps its exact rule-of-three bound (1.88 %, ≤ 0.23/h).

---

## Comment 3 — Energy, background-operation, and usability measurements

**Reviewer's request:** measure battery drain; Android background limitations; data/storage
use; permission burden; scan availability with the screen off; impact on normal phone use.
The review states that scan throttling is mentioned but its operational consequences are not
measured, and that crowd-deployment claims are premature without such data.

**Response:** We built a measurement kit (`New Evaluations etc/instrumentation/`: meter app
with battery, cadence, and storage probes; capture scripts; parsers with a 30-check
regression suite) and recorded three legs on a Motorola Edge 60 Pro. **Mandatory scoping
statement, also now in the manuscript:** the repository does not contain the v2.1 campaign
build, so what ran is *a purpose-built harness reproducing the sensing duty cycle of the
deployment build* (same 15 s epoch, same foreground-service type, same BLE scan and Wi-Fi
poll per epoch). It is not the deployment application, and it ran on Android 16 rather than
the campaign's Android 15/WCN7850 platform; the numbers therefore bound the deployment case
for this device and are not presented as the field device's behaviour. A new subsection,
**"Instrumented background operation"**, replaces the previous "Not instrumented" paragraph
in §IV, with three additions to §VI (threats to validity / platform effects).

Item-by-item:

| Reviewer item | New measurement (real legs only) | Manuscript treatment |
|---|---|---|
| **Battery drain** | Screen off, unattended: mean discharge current **82.7 mA** (30.9 mAh over 22.4 min); state-of-charge drain below the fuel-gauge resolution (**n/m**, quantisation floor 2.864 %/h per 1 % step — reported as unresolved, **not** as 0). Operator view: **196.0 mA**, SOC drain **3.693 %/h** from two 1 % steps (±50 % precision — stated). Forced Doze on top of a lit display: **179.8 mA**, only 8 % below the screen-on baseline. | New cost table (drain, mAh/h, current, IQR, n) with the resolution caveats in the caption. Current is led with because it is sampled every ~5 s rather than inferred from a 1 %-granular gauge. |
| **Android background limitations** | Third-party Wi-Fi `startScan()` honoured **23.5 %** (screen off) / **50.4 %** (screen on) / **0.95 %** under forced deep idle, where only **2 of 105** polls returned fresh results. BLE was unaffected or better under forced Doze (1 676 distinct links/h vs 1 590 screen-on). Under incidental idle, **5 of 18** epoch gaps exceeded twice the 15 s nominal interval (p95 360.2 s, max 427.8 s) although every attempted epoch eventually completed (ratio 1.000) — the gap distribution, not the completion ratio, is reported. | New cadence/throttling table; §VI now attributes the envelope narrowing partly to throttling with measured support, and states the operational asymmetry: under deep idle the Wi-Fi channel is effectively dead while BLE continues, so Wi-Fi cannot be treated as a redundant spare channel. |
| **Data/storage use** | Per-UID mobile traffic **0 B** in all three legs (including forced Doze); app-private storage growth **0.0 kB/h** in all legs; the 266 808 B system-wide delta during one leg is attributed to unrelated processes and explicitly separated. | New storage/traffic table; the "nothing leaves the handset" property is now a measured counter with its caveat, both in §II-D (privacy) and the new §IV subsection. |
| **Scan availability with the screen off** | Screen off and unattended: **100 %** of attempted epochs completed, 69 distinct BLE links in 21 min (**180/h**) vs **1 590/h** with the screen on — an ~9× degradation that is a platform behaviour, not an app defect. | Reported as the honest framing: observation survives in the background but degrades by roughly an order of magnitude when the handset is unattended, under a foreground service and a Doze exemption. |
| **Impact on normal phone use** | **Partially measured, deliberately not overclaimed.** Measured: the duty cycle's cost (82.7 → 196.0 mA) and throughput change (117 → 579 scan bursts/h); forced Doze saves only 8 % once the display is lit, i.e. in an attended deployment the duty cycle dominates the energy cost. **Not measured:** interaction effects — leg B3 holds the screen on and untouched and does not model a person using the phone. | The manuscript states only the narrow supported claim: the duty cycle adds a measurable cost that the dashboard's visibility amplifies. No claim of non-intrusiveness is made. |
| **Permission burden / usability** | **Not measured — reported as a genuine open item.** The usability protocol exists in full (8 tasks against the real tabs, 6–10 non-author participants, SUS / UMUX-Lite / NASA-TLX, consent form) but the study has not been executed. No usability numbers appear in the manuscript; the numbers that exist in the repository are outputs of a synthetic test fixture used to validate the analysers and are explicitly barred from citation. | §IV retains the honest statement: no usability study was run, the operator set is the author team, and the permission sequence remains unquantified. The protocol is specified so it can be executed before a journal extension. |

**Remaining instrumentation gaps, stated in the manuscript rather than hidden:** the idle
floor leg (app stopped) was not run, so every "net of idle" figure is `n/m`; the forced-Doze
leg had the display on (comparable to the operator-view leg, not to the deployment case); the
battery-saver regime and the two-handset transit leg were not run; each leg is n = 1 in a
single session on one device. These are listed in the new subsection and in §VI.

**Crowd-deployment claims.** Consistent with the review's concern, the deployment-facing
claims in §II are now explicitly labelled design arguments, and the measured envelope is
scoped to the measured handset and throttle regime.

---

## Comment 4 — Headers, copyright line, and camera-ready compliance

**Response:** Accepted without reservation. The camera-ready version will:

1. Follow the **DESSERT 2026 camera-ready IEEE template** exactly, including the page
   header/footer the template prescribes;
2. **Replace the existing copyright line** at the bottom of the first page with
   `979-8-3195-6683-6/26/$31.00 ©2026 IEEE`;
3. **Keep the title identical** to the original submission —
   *MeshCrowd: Privacy-Preserving Crowd and Vehicle Sensing using Gamified Mesh Networks* —
   in this revision, in the final acceptance phase, and at the conference;
4. Generate and verify the PDF through **IEEE PDFeXpress®**
   (https://ieee-pdf-express.org) and confirm Xplore-compatible output before submission.

The revised manuscript has already been restructured to the venue's section template
(Introduction; System Design and Architecture; Deployment; Field Evaluation Methodology;
Evaluation — Field Results; Discussion; Conclusions and Future Work), and all headers,
author block, and index terms conform to IEEEtran journal-mode conventions used by the
DESSERT camera-ready kit.

---

## Response to the general remarks in the review summary

The review's summary paragraph asks the revision to narrow claims, fully specify the
classifier, correct result tables, add held-out and multi-device testing where feasible,
evaluate battery and privacy/security constraints, and separate measured capabilities from
proposed extensions. Pointers:

- **Narrowing claims / measured vs proposed separation.** The abstract now states that the
  mesh and gamification layer are design contributions whose distributed validation is future
  work; §II-D ends with the same scoping sentence; §VI adds a "Scope of the validation"
  paragraph enumerating exactly what the campaign validated (single-device stack + two-node
  transit counter) and what it did not (mesh confirmation rates, gamification dynamics). The
  cooperative mesh is exercised in this campaign only as a deployed interface. App-projected
  quantities in screenshots (fused accuracy, radius panel) are caption-guarded as projections,
  not measurements.
- **Full classifier specification.** New §II-B states the complete decision path: baseline as
  the median of the first 20 window samples, dispersion as their standard deviation, trigger
  as the larger of 3 dB and 2.2× that dispersion, three-consecutive-sample admission, the six
  dip features with their definitions, the entity score
  (depth − 13 dB)/5 + (duration − 1.6 s)/1.4 s − texture with its sign rule, the confidence
  clamp, the band-fusion weights, the −75 dBm gate, the −90 dBm refusal, the ±41 % radial
  band, the admissible attenuation fraction interval, and the 45 s parked-vehicle sustain
  threshold. The parameter vector was frozen before the campaign; because no parameter is
  fitted to field data, we state that the open validation question is site and device
  transfer, not overfitting.
- **Result tables.** The transit results now carry integer counts, per-configuration
  confidence intervals, and both denominators (Comment 2 above). The distance-conditioned
  detection and vehicle tables now carry their 95 % Wilson intervals, and per-cell integer
  counts accompany the session-log release.
- **Held-out and multi-device testing.** Device and site transfer is named as the explicit
  open question in §II-B and §VI rather than being implied away. The new instrumentation
  legs provide a second platform point (same handset model, Android 16 build) for the
  background-operation question specifically, scoped as described in Comment 3. A
  distributed multi-device campaign (mesh confirmation and false-confirmation rates across
  node densities, gamification under sustained participation) remains future work and is
  described as such; the mesh numbers visible in the app screenshots remain caption-guarded
  as app projections and are not used as evidence.
- **Battery and privacy/security constraints.** See Comments 3 and 1 respectively.

## What we did not do, and why

In the interest of the same honesty the review praises in the reporting discipline:

1. We did not report any usability, SUS, or permission-burden number: the participant study
   has not been run, and the only such numbers in the repository belong to a synthetic parser
   test fixture that is barred from citation by its own generator's header.
2. We did not attribute the meter-harness measurements to the deployment application or to
   the campaign's Android 15/WCN7850 platform; the wording constraint is enforced in every
   sentence the new subsection uses.
3. We did not backfill unmeasured cells: state-of-charge drain below gauge resolution,
   net-of-idle cost without the idle-floor leg, and the battery-saver regime are reported as
   `n/m` or as not run, never estimated.
4. We did not promote the model-based evaluation harness (4 161 deterministic scenes of
   fusion/ranging/epoch/transit/mesh behaviour) into field evidence; it exists in the
   repository as a reproducibility artifact (fixed seed, SHA-256 reproducibility hash, JSON
   schema, scene-level outcomes retained) and supports the release, not the claims.

We believe the revision satisfies all four minor concerns to the extent the evidence allows,
and we are happy to run the usability study and the remaining instrumentation legs (idle
floor, forced-Doze screen-off, battery saver, two-handset transit) if the reviewer considers
any of them necessary for acceptance.
