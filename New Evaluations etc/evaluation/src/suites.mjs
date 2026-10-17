import { createHash } from "node:crypto";
import { estimateRange, simulateEpochScene, simulateLinkScene, robustMeshConsensus } from "./model.mjs";
import { groupBy, mean, median, rate, round } from "./stats.mjs";

const entityKeys = ["pedestrian", "vehicle"];
const bandKeys = ["ble", "wifi24", "wifi5"];

function idFor(suite, index) {
  return `${suite}-${String(index + 1).padStart(4, "0")}`;
}

export function runFusionSuite(config, random, includeSamples) {
  const scenes = [];
  for (let index = 0; index < config.suites.fusion; index += 1) {
    const bandKey = bandKeys[index % bandKeys.length];
    const distanceM = config.radiiM[Math.floor(index / bandKeys.length) % config.radiiM.length];
    const entityKey = entityKeys[Math.floor(index / (bandKeys.length * config.radiiM.length)) % entityKeys.length];
    const scene = simulateLinkScene({ config, random, bandKey, entityKey, distanceM, includeSamples });
    scenes.push({ sceneId: idFor("fusion", index), suite: "fusion", ...scene });
  }

  const byBand = {};
  for (const [bandKey, values] of groupBy(scenes, (scene) => scene.truth.band)) {
    const detected = values.filter((scene) => scene.features.detected).length;
    const correct = values.filter((scene) => scene.output.classification === scene.truth.entity).length;
    byBand[bandKey] = {
      scenes: values.length,
      detected,
      detectionPct: round(rate(detected, values.length), 2),
      correctlyTyped: correct,
      perCrossingAccuracyPct: round(rate(correct, values.length), 2),
    };
  }

  const byRadius = {};
  for (const [radius, values] of groupBy(scenes, (scene) => scene.truth.distanceM)) {
    const detected = values.filter((scene) => scene.features.detected).length;
    const correct = values.filter((scene) => scene.output.classification === scene.truth.entity).length;
    byRadius[radius] = {
      scenes: values.length,
      detectionPct: round(rate(detected, values.length), 2),
      typingPct: round(rate(correct, values.length), 2),
    };
  }
  return { scenes, summary: { scenes: scenes.length, byBand, byRadius } };
}

export function runRangingSuite(config, random) {
  const scenes = [];
  for (let index = 0; index < config.suites.ranging; index += 1) {
    const bandKey = bandKeys[index % bandKeys.length];
    const layoutM = Math.floor(index / bandKeys.length) % 2 === 0 ? 10 : 55;
    const band = config.bands[bandKey];
    const observed = band.referenceRssiDbmAt1m - 10 * band.pathLossExponent * Math.log10(layoutM) + random.gaussian(0, layoutM === 10 ? 1.2 : 3.5);
    const range = estimateRange(observed, band, config.ranging);
    const naiveErrorM = Math.abs(range.naiveM - layoutM);
    scenes.push({
      sceneId: idFor("ranging", index),
      suite: "ranging",
      truth: { band: bandKey, distanceM: layoutM },
      observedRssiDbm: round(observed),
      output: range,
      naiveErrorM: round(naiveErrorM),
      gateSuppressedEstimate: range.status !== "estimated-band",
    });
  }
  const eligible = scenes.filter((scene) => scene.output.status === "estimated-band");
  const refused = scenes.filter((scene) => scene.output.status === "refused");
  const floor = scenes.filter((scene) => scene.output.status === "noise-floor");
  return {
    scenes,
    summary: {
      scenes: scenes.length,
      estimatedBands: eligible.length,
      refused: refused.length,
      noiseFloor: floor.length,
      medianNaiveErrorM: round(median(scenes.map((scene) => scene.naiveErrorM))),
      maximumNaiveErrorM: round(Math.max(...scenes.map((scene) => scene.naiveErrorM))),
    },
  };
}

export function runEpochSuite(config, random, includeSamples) {
  const distances = config.radiiM.slice(0, 6);
  const scenes = [];
  for (let index = 0; index < config.suites.epoch; index += 1) {
    const distanceM = distances[index % distances.length];
    const moving = Math.floor(index / distances.length) % 2 === 0;
    const scene = simulateEpochScene({ config, random, distanceM, moving, includeSamples });
    scenes.push({ sceneId: idFor("epoch", index), suite: "epoch", ...scene });
  }
  const byDistance = {};
  for (const [distance, values] of groupBy(scenes, (scene) => scene.truth.distanceM)) {
    const moving = values.filter((scene) => scene.truth.moving);
    const empty = values.filter((scene) => !scene.truth.moving);
    byDistance[distance] = {
      movingScenes: moving.length,
      movementDetectionPct: round(rate(moving.filter((scene) => scene.output.stableChanged).length, moving.length), 2),
      emptyScenes: empty.length,
      stableRuleFalsePositivePct: round(rate(empty.filter((scene) => scene.output.stableChanged).length, empty.length), 2),
      naiveRuleFalsePositivePct: round(rate(empty.filter((scene) => scene.output.naiveChanged).length, empty.length), 2),
    };
  }
  return { scenes, summary: { scenes: scenes.length, byDistance } };
}

export function runTransitSuite(config, random) {
  const separations = config.transit.separationsM;
  const scenes = [];
  for (let index = 0; index < config.suites.transit; index += 1) {
    const separationM = separations[index % separations.length];
    const entity = entityKeys[Math.floor(index / separations.length) % entityKeys.length];
    const probability = config.transit.detectionProbability[String(separationM)];
    const detected = random.bool(probability);
    const typingProbability = separationM <= 10 ? 1 : Math.max(0.55, probability - 0.08);
    const typed = detected && random.bool(typingProbability);
    scenes.push({
      sceneId: idFor("transit", index),
      suite: "transit",
      truth: { separationM, entity },
      output: {
        rfcommPresent: detected || random.bool(0.08),
        l2capPresent: detected || random.bool(0.12),
        detected,
        classification: typed ? entity : detected ? (entity === "vehicle" ? "pedestrian" : "vehicle") : "unknown",
      },
    });
  }
  const bySeparation = {};
  for (const [separation, values] of groupBy(scenes, (scene) => scene.truth.separationM)) {
    bySeparation[separation] = {
      scenes: values.length,
      detectionPct: round(rate(values.filter((scene) => scene.output.detected).length, values.length), 2),
      typingPct: round(rate(values.filter((scene) => scene.output.classification === scene.truth.entity).length, values.length), 2),
    };
  }
  return { scenes, summary: { scenes: scenes.length, bySeparation } };
}

export function runMeshSuite(config, random) {
  const scenes = [];
  for (let index = 0; index < config.suites.mesh; index += 1) {
    const empty = index < 160;
    const truthCount = empty ? 0 : 1 + (index % 2);
    const nodeCount = 2 + (index % (config.mesh.maximumNodes - 1));
    const reports = [];
    for (let node = 0; node < nodeCount; node += 1) {
      const byzantine = !empty && random.bool(0.08);
      let count = truthCount;
      if (empty) count = random.bool(0.015) ? 1 : 0;
      else if (byzantine) count += random.pick([-3, 3, 4]);
      else if (random.bool(0.13)) count += random.pick([-1, 1]);
      reports.push({ nodeId: `node-${node + 1}`, count: Math.max(0, count), byzantine });
    }
    const consensus = robustMeshConsensus(reports, config);
    scenes.push({
      sceneId: idFor("mesh", index),
      suite: "mesh",
      truth: { empty, count: truthCount, nodeCount },
      output: consensus,
    });
  }
  const empty = scenes.filter((scene) => scene.truth.empty);
  const occupied = scenes.filter((scene) => !scene.truth.empty);
  const reliableReports = occupied.flatMap((scene) => scene.output.reports).filter((report) => report.reliabilityScore >= 0.9);
  return {
    scenes,
    summary: {
      scenes: scenes.length,
      emptyScenes: empty.length,
      falseConfirmations: empty.filter((scene) => scene.output.confirmed).length,
      occupiedScenes: occupied.length,
      confirmationPct: round(rate(occupied.filter((scene) => scene.output.confirmed).length, occupied.length), 2),
      meanReliableRewardMultiplier: round(mean(reliableReports.map((report) => report.rewardMultiplier))),
      singlePhoneRadiusM: config.mesh.singlePhoneRadiusM,
      meshRadiusM: config.mesh.meshRadiusM,
    },
  };
}

export function reproducibilityHash(records) {
  const hash = createHash("sha256");
  for (const record of records) hash.update(`${JSON.stringify(record)}\n`);
  return `sha256:${hash.digest("hex")}`;
}