# Eval-Phone.md — on-device energy, background-operation, storage and duty-cycle evidence

**Status: measured on real hardware. Three legs recorded (B2, B3, B5), n = 1
each. B5 carries a screen-state deviation — see §2 before quoting it.**
This file supersedes the "Not instrumented" paragraph in
`merged/response_to_reviewer.md` §3 for the items that now have numbers, and it
states plainly which items remain unmeasured.

Every figure below was produced by `instrumentation/analysis/parse_leg.py` from
CSVs written by the meter app while it ran on the handset. Nothing here is
estimated, interpolated, or carried over from the repository's simulation
harness. Where a quantity could not be resolved, it is written `n/m` (not
measured) rather than filled in.

---

## 1. What was measured, and what this is not

| | |
|---|---|
| Device | motorola edge 60 pro (`ZY22MCML4K`, `cybert_g_syse`) |
| OS | Android 16, build `856a5e-59f4b` |
| Battery | `charge_full` = 5 604 000 µAh → **5 604 mAh** |
| Instrument | `org.meshcrowd.meter`, debug-signed, minSdk 26 / targetSdk 36, uid 10492 |
| Service state | foreground service confirmed live (`isForeground=true`, `types=0x10` CONNECTED_DEVICE) |
| Environment | battery saver **off**, adaptive charging inactive, app on the Doze whitelist, Bluetooth on |

**Scope limit — read this before quoting any number.** The repository does not
contain the v2.1 campaign build. What ran on the handset is a purpose-built
harness that reproduces the sensing duty cycle of the deployment build: the same
15 s epoch, the same foreground-service type, the same BLE scan and Wi-Fi poll
per epoch. It is **not** the deployment application. Every figure here must be
worded as *"a purpose-built harness reproducing the sensing duty cycle of the
deployment build"* and never as "the app". This is the single most important
constraint on how this evidence is used in the manuscript.

**Second scope limit:** the paper's field campaign ran on Android 15 with a
WCN7850 radio. These legs are Android 16 on different silicon. Scan-throttling
behaviour is platform- and firmware-specific, so these numbers bound the
deployment case for *this* device and must not be presented as the field
device's behaviour.

---

## 2. Headline numbers

| Quantity | B2 — screen off, unattended | B3 — screen on, 40 % brightness | B5 — screen **on**, forced Doze |
|---|---|---|---|
| Duration of discharging samples | 22.39 min | 33.41 min | 20.4 min |
| Discharging samples | 32 | 390 | 245 |
| `device_idle=1` throughout | last 17 samples only | no | **yes, all 245** |
| **SOC drain** | **n/m** (below gauge resolution) | **3.693 %/h** | **n/m** (1 step, at the floor) |
| **Mean discharge current** | **82.7 mA** (IQR 19–82, n=29) | **196.0 mA** (IQR 178–195, n=389) | **179.8 mA** (IQR 160–175, n=244) |
| Energy over leg | 30.9 mAh | 109.1 mAh | 79.6 mAh |
| BLE scan bursts | 117/h | 579/h | 774/h |
| BLE result batches | 685/h | 2 285/h | 3 584/h |
| Results per burst | 5.84 | 3.95 | 4.63 |
| Distinct links observed per hour | 180 | 1 590 | 1 676 |
| Sensing epochs completed | 44/h, ratio 1.000 | 231/h, ratio 1.000 | 309/h, ratio 1.000 |
| Epoch gap median / p95 / max | 8.2 s / 360.2 s / 427.8 s | 15.0 s / 15.1 s / 15.1 s | 15.0 s / 15.1 s / 15.1 s |
| Epochs missed (>2× nominal 15 s) | **5 of 18 gaps** | **0 of 131 gaps** | **0 of 104 gaps** |
| Wi-Fi `startScan` honoured | 0.235 | **0.504** | **0.0095** |
| **Wi-Fi polls returning fresh results** | 6 of 17 | 67 of 131 | **2 of 105** |
| App log storage growth | 0.0 kB/h | 0.0 kB/h | 0.0 kB/h |
| Per-UID mobile traffic | 0 B | 0 B | 0 B |

**B5 is not a valid screen-off leg and must not be reported as one.** The display
was woken at t=342.9 s — almost certainly by the act of unplugging the cable —
and stayed lit for all 245 discharging samples, because `screen_off_timeout` had
been raised to 60 min for the earlier legs. So B5 is *screen-on plus forced
Doze*, which makes it directly comparable to B3 and **not** to B2. Two further
deviations: forced Doze was engaged before unplugging rather than for the last
30 min of a 60 min leg, because there is no adb over an unplugged cable and a
mid-leg transition is impossible on this bench; and the phone sat on USB for the
first ~5 min of the recording while Doze was armed, so the discharging window is
20.4 min, not 30. The Doze condition itself is solid: `mState=IDLE`, and the app
was **removed from the Doze whitelist first**, because `force-idle` cannot idle a
whitelisted app and B5 would otherwise have been a silent no-op.

Raw per-leg artefacts: `instrumentation/runs/B2-idle-sensing-20261006-011458/`,
`instrumentation/runs/B3-operator-view-20261006-014431/` and
`instrumentation/runs/B5-forced-doze-20261006-025336/`. Paste-ready
tables regenerate with
`python3 analysis/meter_report.py <leg>/metrics.json --capacity-mah 5604`.

---

## 3. Reviewer item 1 — battery drain

**Answered, with one figure that must be quoted carefully.**

B3 gives **3.693 %/h** from 2 observed SOC steps (70 % → 68 %) over 32.5 min.
The parser flags this as resolution-limited: the quantisation floor on this
handset is 1.847 %/h per 1 % step, so **3.693 %/h carries roughly ±50 %
precision**. It should not be quoted to three significant figures, and it rests
on a small number of steps.

The stronger evidence is the current column, which is sampled every ~5 s rather
than inferred from a 1 %-granular gauge: **196.0 mA over 389 samples in B3**,
**82.7 mA over 29 samples in B2**. Lead with these.

B2's SOC drain is reported as **unresolved, not zero**. Level held at 68 % for
the whole leg with zero steps. At 1 % granularity, one step is worth 2.864 %/h
over that window, so the background duty cycle is below what the fuel gauge can
resolve in 21 minutes. The toolchain refuses to invent a number here and so
should the manuscript: this is `n/m`, not `0 %/h`.

Per-UID attribution from `dumpsys batterystats` is present but **not used** as
the energy figure, for a stated reason. Android's own estimator reports
156 mAh for uid 10492 over the B3 leg while the *global* computed drain for the
same dump is 53.9 mAh — a per-app figure that exceeds the whole-device figure is
internally inconsistent, which is a known failure mode of the estimator on some
builds. The sampler's current integration (109.1 mAh over B3) is the defensible
number, and it is also the one that does not depend on Android's model of what
the app was doing.

---

## 4. Reviewer item 2 — Android background limits

**Answered, and the finding is uncomfortable for the deployment case.**

Three pieces of evidence, and the third is decisive.

**Wi-Fi active-scan throttling.** Third-party `WifiManager.startScan()` is
documented as rate-limited from Android 9 onward. On this handset **23.5 %** of
scan requests were honoured with the screen off (B2) and **50.4 %** with the
screen on (B3).

**Forced Doze nearly eliminates Wi-Fi observation entirely.** This is the
sharpest result in the campaign. In B5, under forced deep idle, only
**1 of 105** scan requests was accepted — a ratio of **0.0095**, against 0.504
in the screen-on B3 baseline. More telling than the acceptance ratio is what the
requests returned: **2 fresh results out of 105 polls**, against 67 of 131 in B3.
BLE was unaffected by comparison — scan starts and result batches actually rose
(3 584/h against 2 285/h), and distinct links per hour rose from 1 590 to 1 676.
So the platform's response to deep idle is not a general slowdown: it is
specifically that **Wi-Fi-based observation stops working**, while BLE continues.

That asymmetry is the operationally important part of the reviewer's question. A
deployment that treats Wi-Fi scanning as a redundant second channel has not
measured what happens to it under Doze, because in the deep-idle case that
channel returns essentially nothing. Any claim of redundant sensing across
bands needs this caveat.

**Epoch starvation under idle, without forced Doze.** B2 missed **5 of 18**
epoch gaps at more than twice the nominal 15 s interval, with a p95 gap of
360 s and a maximum of 427.8 s. B3, with the screen on, missed **0 of 131**, and
so did B5 despite being under forced Doze. Note the apparent
contradiction with the epoch *completion* ratio of 1.000 in every leg: every
attempted epoch did eventually complete, but under B2 conditions they were
delayed by up to about seven minutes. The ratio alone would hide this; the gap
distribution is the honest measure.

B2's starvation coincides with the phone entering Doze on its own
(`device_idle=1` for the final 17 samples). That is **incidental, not forced**,
and it must not be described as a forced-Doze result. B5 is the forced leg, and
B5 missed **no** epochs at all — so the two must be reported as distinct
phenomena rather than merged. What B2 supports is the weaker and still useful
claim that when an unattended Android 16 phone is left to itself, the sensing
schedule degrades sharply while the app remains nominally "running".

Two structural asymmetries between the legs matter when reading any of this:

- B2 and B3 ran with the app **on the Doze whitelist** and a live foreground
  service of type CONNECTED_DEVICE. Their observed gaps therefore bound the
  *best case* for an app that has already obtained everything the platform
  offers. B5 ran with the whitelist entry **removed**, which is what forced idle
  required, and is the more representative case for a deployment whose exemption
  is denied or revoked.
- B5's screen was on (see §2), so B5 and B3 form the like-for-like pair and B2
  stands alone as the only screen-off measurement. A forced-Doze *screen-off* leg
  has still not been run.

---

## 5. Reviewer item 3 — data and storage use

**Answered, and the result is unambiguous.**

Per-UID mobile traffic was **exactly 0 bytes** in all three legs, measured across
independent `netstats` samples per leg whose system-wide byte counters were
byte-identical across the whole window. That is a direct measurement that
observation does not leave the handset, and it is a stronger statement than an
assertion about the architecture. B5 matters here specifically: forced deep idle
is the regime where a platform might defer or batch network traffic, and even
there the per-UID counters stayed at zero.

Storage growth was **0.0 kB/h** in all three legs. The zero is real rather than a
probe artefact: the storage probe counts only the app-private directories
(`filesDir`, `cacheDir`, `noBackupDir`), and the meter's own CSVs are written to
external app-specific storage, which that probe deliberately does not count. So
the app-private footprint did not grow measurably over the three windows
(~21, ~33 and ~20 min).

One caveat that must be stated if this number is used: B3's system-wide mobile
transmit counter moved by 266 808 B during the leg while the per-UID counters
stayed at 0. That delta belongs to other processes on the handset, not to the
meter. The per-UID 0 B is the figure to quote, and the distinction should be
explicit so the number is not misread as "the phone sent nothing".

---

## 6. Reviewer item 5 — scan availability with the screen off

**Answered for B2 and B3, and the two together are more informative than
either alone.**

With the screen off and the phone unattended (B2) the harness still completed
**100 %** of attempted epochs and observed **69 distinct BLE links** across 45
scan bursts in 21 minutes. With the screen on (B3) it observed **901 distinct
links** across 328 bursts in 33 minutes.

The honest framing is that **coverage improves by roughly an order of magnitude
when someone is watching the phone, and collapses when they are not** — and the
collapse is a platform behaviour, not an app defect. This cuts against the
intuitive reading that keeping the dashboard visible is simply a costly way to
improve coverage: for an unattended deployment, the interesting question is not
whether observation survives but *how degraded* it gets, and these legs put a
number on the degradation. Distinct links per hour are 180 (B2) versus 1 590
(B3), roughly 8.9×.

**What B5 adds to this item, and it is a qualification rather than a
confirmation.** BLE discovery proved robust under forced deep idle: 1 676
distinct links per hour, the highest rate of any leg, with scan starts and
results *above* the screen-on B3 baseline. So the BLE half of the sensing duty
cycle is more resilient to Doze than the screen-off B2 numbers alone would
suggest. What did not survive was Wi-Fi: 2 fresh results in 105 polls.

The practical consequence is that an unattended deployment should not treat
Wi-Fi scanning as a spare channel behind BLE. On this handset, under the idle
regime an unattended phone actually reaches, the Wi-Fi channel was
operationally dead while BLE kept working. The two legs together give the
reviewer a defensible answer to "does observation survive in the background":
partly, and the surviving part is specific to the radio.

The reviewer's related concern that "no scan-cadence logs are reported to
substantiate the throttling attribution" is now directly addressed: per-epoch
start/complete timestamps are in `events-*.csv`, and per-burst and per-link
counts in `cadence-*.csv`.

---

## 7. Reviewer item 6 — impact on normal phone use

**Partially answered. The battery and throughput halves are measured; the
interaction half is not, and should not be claimed.**

Measured: with the operator view visible, mean discharge current rises from
82.7 mA to 196.0 mA (≈2.4×), SOC drain becomes resolvable at 3.693 %/h, and
scan throughput roughly quintuples (117 → 579 bursts/h). Forcing deep idle on
top of that reduces current only modestly, to 179.8 mA — **8 % below the
screen-on un-idled baseline** — so the platform's own idle machinery saves
surprisingly little energy once a display is already lit. In other words, the
battery cost in an attended deployment is dominated by the duty cycle, not by
what Doze would otherwise have done.

Not measured: B3 holds the screen on and untouched. It does not model a person
using the phone. Any claim about interference with normal use — notification
intrusiveness, battery lost to the operator's own scrolling, interaction latency
— is outside what these legs can support. The defensible statement is the
narrow one: *the duty cycle adds a measurable cost that the dashboard's
visibility amplifies*, not *the app does not get in the way*.

---

## 8. Reviewer item 4 — permission burden

**Not measured. This is a genuine non-result and no amount of further
instrumentation on this bench will change it.**

Permission burden is a human-facing property. The protocol's U1 study requires
6–10 non-author participants completing a ~35 min think-aloud session. That
cannot be automated, cannot be simulated, and was not run. The correct treatment
in the manuscript is to state it as an open item with the study design specified
and unexecuted — which is what §3 of `response_to_reviewer.md` currently does.
It should stay that way; the other five items gaining real numbers makes it more
important, not less, that this one is not quietly upgraded by implication.

---

## 9. Legs not run

| Leg | Condition | Status |
|---|---|---|
| B1 | app stopped, screen off — idle floor | **not run** |
| B4 | two phones, mesh/RFCOMM+L2CAP | not run (needs a second handset) |
| B5 | forced Doze | run, but **screen was on** — see §2 |
| B5a | forced Doze *with the screen off* | not run |
| B6 | battery saver on | not run |

Two omissions matter, in this order.

**B1 is the significant one.** `net_cost_pct_per_h` is defined in `protocol.md`
as *leg drain minus B1 drain* — the net-of-idle figure is the one a reviewer
actually wants, and every net number here is `n/m` without it. The current
column would let a B1 floor be subtracted in mA even where the %/h stays
unresolved, so B1 is worth running even though it will probably not move the
gauge either. Note that B1 cannot be recorded by the app, since the app is what
records: it needs shell-side `dumpsys battery` snapshots before and after, which
on this bench is all that survives an unplugged window.

**B5a is the one that would let B5 be reported as intended.** B5's screen-on
state makes it comparable to B3 rather than to the deployment case. Re-running
with the display genuinely off, and with the cable handled without touching the
phone, would give the forced-Doze screen-off measurement the protocol asks for.

The protocol also asks for 3 reps per leg with 10 min settling between them.
These are n = 1 per leg. There is no median-over-repetitions and no
across-repetition IQR for any figure above, and the three legs come from a
single session on one device in one environment.

---

## 9a. Settings restored on the handset

After the final leg the following were returned to their pre-campaign values:
`screen_off_timeout` 3 600 000 → **15 000 ms**, `screen_brightness` 104 → **52**,
forced idle released (`mState=ACTIVE`), battery saver left **off** throughout.
One deliberate non-restoration: the app remains **off the Doze whitelist**, which
is its pre-B2 state — B2 and B3 were run with it whitelisted, and B5 could not
be run at all without removing that entry. Any future leg must state which state
it used, since it materially changes the result.

---

## 10. Two analyser defects found and fixed during this campaign

Both were portability bugs that would have silently corrupted results on any
device with these characteristics. They are recorded because they affect how much
the numbers can be trusted, and because the first one produced a *plausible but
entirely false* zero.

**1. `status=3` was misclassified as charging.** `normalise_battery()` keyed the
charging test on `status in (2, 3)`, where 3 is `BATTERY_STATUS_FULL` upstream.
This handset reports `status=3` with `plugged=0` while actively discharging, with
negative `current_now`. Every genuine discharging sample was therefore discarded
and the leg reported `n_points: 0` with a null current — indistinguishable from
"nothing drained". `plugged` is now authoritative where readable, with `status`
used only as a fallback. The defect would have reported a false zero on any
device whose OEM encoding collides with the upstream constants, which is a
plausible failure across a multi-device campaign.

**2. `dumpsys batterystats` output was unreadable, for two separate reasons.**
Shell-captured dumps on this bench are written as UTF-16LE (the `FF FE` BOM is
visible at offset 0 of `batterystats-after.txt`), while the parser read them as
UTF-8. Every section-header match then missed and the leg reported a
`batterystats` gap despite 674 KB of valid data being present. Decoding is now
BOM-sniffing. Separately, this Android 16 build prints UID rows in a shape the
parser did not anticipate — `UID u0a492: 156 fg: 2.65 ...`, with a *name-form*
uid and an *integer* total, where older builds print `Uid 10492: 0.5`. A
dedicated `RE_UIDROW` handles all three observed shapes, and the fg/bg split is
now captured rather than discarded.

All 30 synthetic-fixture checks in `tests/run_tests.sh` pass after both changes,
including the drain, current, and per-UID mAh assertions.

---

## 11. Sentence bank

Only sentences whose numbers appear above. Delete rather than hedge. The B5
sentences carry the screen-on caveat from §2 with them; do not quote them without
it.

- On an Android 16 handset, a purpose-built harness reproducing the sensing duty
  cycle of the deployment build drew a mean discharge current of
  $\mathrm{196.0\,mA}$ with the operator dashboard visible and
  $\mathrm{82.7\,mA}$ with the screen off and the device unattended.
- With the screen visible the harness resolved a state-of-charge drain of
  $\mathrm{3.693\,\%/h}$ (two 1 % steps; quantisation floor
  $\mathrm{1.847\,\%/h}$ per step), while the screen-off duty cycle fell below
  the resolution of the 1 %-granular fuel gauge over the same measurement.
- Sensing continued in every condition, completing 100 % of attempted epochs,
  but with the screen off and the device left to itself 5 of 18 epoch intervals
  exceeded twice the nominal 15 s period, with a maximum delay of 427.8 s.
- Third-party Wi-Fi active-scan requests were honoured in only 23.5 % of attempts
  with the screen off and 50.4 % with the screen on, consistent with the platform
  rate-limiting documented from Android 9 onward.
- Under forced deep idle, with the display on and the app removed from the Doze
  whitelist, third-party Wi-Fi active-scan requests were honoured in only
  0.95 % of attempts and returned fresh results in 2 polls out of 105, while BLE
  scanning was unaffected and yielded a higher rate of distinct links per hour
  than the idle-free baseline.
- Per-UID mobile traffic was 0 B in all three conditions, including under forced
  deep idle, and app-private storage did not grow measurably over any leg.
- Distinct BLE links observed per hour fell from 1 590 with the screen on to 180
  with the screen off, so observation degrades by roughly 9× when the handset is
  unattended, despite the harness holding a foreground service and exemption from
  Doze throughout.
- Forcing deep idle on top of an already-lit display reduced mean discharge
  current by only 8 % ($\mathrm{179.8\,mA}$ against $\mathrm{196.0\,mA}$),
  indicating that in an attended deployment the sensing duty cycle, rather than
  the platform's idle machinery, dominates the energy cost.

---

## 12. Provenance

- Parsers: `instrumentation/analysis/parse_leg.py`, `instrumentation/analysis/meter_report.py`
- Regression suite: `instrumentation/tests/run_tests.sh` — 30 checks, all passing on the synthetic fixture
- Protocol: `instrumentation/protocol.md` (legs B1–B6, usability part U)
- Legs: `instrumentation/runs/B2-idle-sensing-20261006-011458`, `instrumentation/runs/B3-operator-view-20261006-014431`, `instrumentation/runs/B5-forced-doze-20261006-025336`
- The `n/m` convention and Route A/B scope distinction are defined in `instrumentation/README.md`.

Every number in this file traces to a CSV in one of the two leg directories.
Nothing in this file may be replaced by a simulation-harness figure, and no
figure here may be attributed to the deployment application.
