#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const summaryPath = path.resolve(root, process.argv[2] ?? "outputs/latest/summary.json");
const summary = JSON.parse(fs.readFileSync(summaryPath, "utf8"));

console.log(`\nMeshCrowd evaluation: ${summary.experimentId}`);
console.log(`Seed ${summary.seed} · ${summary.totalScenes} scenes`);
console.log(`Reproducibility ${summary.reproducibilityHash}\n`);

console.log("Fusion by band");
console.table(summary.suites.fusion.byBand);
console.log("Epoch by distance");
console.table(summary.suites.epoch.byDistance);
console.log("Transit by separation");
console.table(summary.suites.transit.bySeparation);
console.log("Ranging");
console.table([summary.suites.ranging]);
console.log("Mesh");
console.table([summary.suites.mesh]);