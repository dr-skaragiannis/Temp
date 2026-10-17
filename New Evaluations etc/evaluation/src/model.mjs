import { clamp, longestRun, median, mean, round, standardDeviation, variance } from "./stats.mjs";

export function rssiAtDistance(distanceM, band) {
  return band.referenceRssiDbmAt1m - 10 * band.pathLossExponent * Math.log10(Math.max(distanceM, 0.1));
}

export function environmentalSigmaDb(distanceM) {
  return clamp(0.45 + 0.055 * distanceM, 0.45, 4.2);
}

export function effectiveAttenuationDb(distanceM, band, entity, lateralOffsetM = 0) {
  const distanceEfficiency = (1 + distanceM / 10) ** -0.6;
  const lateralEfficiency = Math.exp(-(lateralOffsetM ** 2) / (2 * entity.lateralSigmaM ** 2));
  const raw = band.referenceAttenuationDb * entity.attenuationScale * distanceEfficiency * lateralEfficiency;
  return Math.min(entity.attenuationCapDb ?? Number.POSITIVE_INFINITY, raw);
}

export function simulateLinkScene({ config, random, bandKey, entityKey, distanceM, includeSamples = false }) {
  const band = config.bands[bandKey];
  const entity = config.entities[entityKey];
  const count = config.samplesPerScene;
  const intervalMs = config.sampleIntervalMs;
  const center = random.integer(27, 34);
  const temporalSigma = entityKey === "vehicle" ? 8.2 : 3.8;
  const lateralOffset = random.gaussian(0, entity.lateralSigmaM * 0.58);
  const amplitude = effectiveAttenuationDb(distanceM, band, entity, lateralOffset);
  const sigma = environmentalSigmaDb(distanceM);
  const baseRssi = rssiAtDistance(distanceM, band) + random.gaussian(0, 0.7);
  const samples = [];

  for (let index = 0; index < count; index += 1) {
    const timeS = (index * intervalMs) / 1000;
    const profile = Math.exp(-((index - center) ** 2) / (2 * temporalSigma ** 2));
    const periodic =
      entityKey === "vehicle"
        ? entity.flutterAmplitudeDb * Math.sin(2 * Math.PI * entity.flutterHz * timeS)
        : entity.wobbleAmplitudeDb * Math.sin(2 * Math.PI * entity.wobbleHz * timeS);
    const noise = random.gaussian(0, sigma);
    samples.push(round(baseRssi - amplitude * profile + periodic * profile + noise, 3));
  }

  const features = extractFeatures(samples, config);
  const classification = classifyEvent(features, config);
  const range = estimateRange(median(samples.slice(0, config.detector.baselineSamples)), band, config.ranging);

  return {
    truth: { band: bandKey, entity: entityKey, distanceM, amplitudeDb: round(amplitude) },
    baselineRssiDbm: round(baseRssi),
    noiseSigmaDb: round(sigma),
    features,
    output: { ...classification, range },
    ...(includeSamples ? { samples } : {}),
  };
}

export function extractFeatures(samples, config) {
  const baselineCount = config.detector.baselineSamples;
  const baselineWindow = samples.slice(0, baselineCount);
  const baseline = median(baselineWindow);
  const dispersion = standardDeviation(baselineWindow);
  const dipSeries = samples.map((value) => baseline - value);
  const threshold = Math.max(config.detector.minimumDipDb, dispersion * config.detector.noiseFloorMultiplier);
  const sustained = longestRun(dipSeries, (value) => value >= threshold);
  const detected = sustained >= config.detector.sustainedSamples;
  const active = dipSeries.filter((value) => value >= threshold);
  const differences = [];
  for (let index = 1; index < samples.length; index += 1) differences.push(samples[index] - samples[index - 1]);
  const depthDb = Math.max(...dipSeries);
  const durationMs = sustained * config.sampleIntervalMs;
  const texture = active.length ? standardDeviation(differences) / Math.max(depthDb, 0.1) : 0;
  const sortedDepths = [...dipSeries].sort((a, b) => b - a);
  const prominenceDb = Math.max(0, sortedDepths[0] - (sortedDepths[4] ?? sortedDepths[sortedDepths.length - 1]));

  return {
    detected,
    baselineDbm: round(baseline),
    dispersionDb: round(dispersion),
    triggerThresholdDb: round(threshold),
    depthDb: round(depthDb),
    durationMs,
    texture: round(texture),
    varianceDb2: round(variance(samples)),
    prominenceDb: round(prominenceDb),
    sustainedSamples: sustained,
  };
}

export function classifyEvent(features, config) {
  if (!features.detected) return { classification: "unknown", confidence: 0 };
  const vehicleScore =
    (features.depthDb - config.detector.vehicleDepthDb) / 5 +
    (features.durationMs - config.detector.vehicleDurationMs) / 1400 -
    features.texture;
  const classification = vehicleScore > 0 ? "vehicle" : "pedestrian";
  const confidence = clamp(0.5 + Math.abs(vehicleScore) * 0.18, 0.5, 0.97);
  return { classification, confidence: round(confidence) };
}

export function estimateRange(observedRssiDbm, band, ranging) {
  const naiveM = 10 ** ((band.referenceRssiDbmAt1m - observedRssiDbm) / (10 * band.pathLossExponent));
  if (observedRssiDbm <= ranging.noiseFloorDbm) {
    return { status: "noise-floor", observedRssiDbm: round(observedRssiDbm), naiveM: round(naiveM) };
  }
  if (observedRssiDbm <= ranging.rangeGateDbm) {
    return { status: "refused", observedRssiDbm: round(observedRssiDbm), naiveM: round(naiveM) };
  }
  return {
    status: "estimated-band",
    observedRssiDbm: round(observedRssiDbm),
    naiveM: round(naiveM),
    lowerM: round(naiveM * ranging.radialBand[0]),
    upperM: round(naiveM * ranging.radialBand[1]),
  };
}

export function simulateEpochScene({ config, random, distanceM, moving, includeSamples = false }) {
  const band = config.bands.ble;
  const sigma = environmentalSigmaDb(distanceM);
  const baseline = rssiAtDistance(distanceM, band) + random.gaussian(0, 0.5);
  const stableCount = config.epoch.stableSamples;
  const epochA = [];
  const epochB = [];

  for (let index = 0; index < stableCount; index += 1) {
    epochA.push(round(baseline + random.gaussian(0, sigma), 3));
    epochB.push(round(baseline + random.gaussian(0, sigma), 3));
  }

  if (moving) {
    const entity = config.entities.pedestrian;
    const amplitude = effectiveAttenuationDb(distanceM, band, entity, random.gaussian(0, entity.lateralSigmaM * 0.45));
    const center = random.integer(7, 13);
    for (let index = 0; index < epochB.length; index += 1) {
      const profile = Math.exp(-((index - center) ** 2) / (2 * 2.4 ** 2));
      epochB[index] = round(epochB[index] - amplitude * profile, 3);
    }
  }

  const medianA = median(epochA);
  const medianB = median(epochB);
  const stableDeltaDb = Math.abs(medianB - medianA);
  const transientDipDb = medianA - Math.min(...epochB);
  const stableChanged = stableDeltaDb >= config.epoch.changeDb || (moving && transientDipDb >= config.epoch.changeDb);
  const naiveChanged = Math.abs(epochB.at(-1) - epochA.at(-1)) >= config.epoch.changeDb;

  return {
    truth: { distanceM, moving },
    output: {
      stableChanged,
      naiveChanged,
      stableDeltaDb: round(stableDeltaDb),
      transientDipDb: round(transientDipDb),
      stableLevelA: round(medianA),
      stableLevelB: round(medianB),
    },
    ...(includeSamples ? { epochA, epochB } : {}),
  };
}

export function robustMeshConsensus(reports, config) {
  const center = median(reports.map((report) => report.count));
  const accepted = reports.filter((report) => Math.abs(report.count - center) <= config.mesh.agreementToleranceCount);
  const fusedCount = Math.round(mean(accepted.map((report) => report.count)));
  const scored = reports.map((report) => {
    const distance = Math.abs(report.count - center);
    const reliabilityScore = clamp(1 - distance / Math.max(config.mesh.agreementToleranceCount + 1, 1), 0, 1);
    return {
      ...report,
      accepted: accepted.includes(report),
      reliabilityScore: round(reliabilityScore),
      rewardMultiplier: reliabilityScore >= 0.9 ? config.mesh.reliabilityMultiplier : 1,
    };
  });
  const confirmations = scored.filter((report) => report.accepted && report.count > 0).length;
  return {
    center: round(center),
    fusedCount,
    confirmed: confirmations >= config.mesh.minimumConfirmingNodes,
    reports: scored,
  };
}