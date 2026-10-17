export function createRandom(seed) {
  let state = seed >>> 0;
  let spare = null;

  function next() {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  }

  function gaussian(mean = 0, std = 1) {
    if (spare !== null) {
      const value = spare;
      spare = null;
      return mean + value * std;
    }
    const u = Math.max(next(), Number.EPSILON);
    const v = Math.max(next(), Number.EPSILON);
    const magnitude = Math.sqrt(-2 * Math.log(u));
    const z0 = magnitude * Math.cos(2 * Math.PI * v);
    spare = magnitude * Math.sin(2 * Math.PI * v);
    return mean + z0 * std;
  }

  return {
    next,
    gaussian,
    bool(probability = 0.5) {
      return next() < probability;
    },
    integer(min, maxInclusive) {
      return min + Math.floor(next() * (maxInclusive - min + 1));
    },
    pick(values) {
      return values[Math.floor(next() * values.length)];
    },
    state() {
      return state >>> 0;
    },
  };
}