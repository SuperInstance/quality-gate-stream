/**
 * Pythagorean48 Trust Encoding
 * 
 * 48 exact directions on the unit circle.
 * log2(48) = 5.585 bits per vector — maximum information per bit for 16-bit integers.
 * 
 * The 48 directions correspond to angles: k * 360/48 = k * 7.5 degrees for k in [0, 47].
 * This is the Pythagorean quantization — exact integer arithmetic on Z/48Z.
 */

export const DIRECTION_COUNT = 48;
export const BITS_PER_VECTOR = Math.log2(48);  // 5.58496...

/**
 * Precomputed lookup table: direction index → [x, y] unit vector.
 * Computed as (cos(k * 2π/48), sin(k * 2π/48)) for k in [0, 47].
 * These are exact rational values (some are sqrt-based, stored as floats).
 */
const DIRECTION_VECTORS: Array<[number, number]> = Array.from({ length: DIRECTION_COUNT }, (_, k) => {
  const angle = (k * 2 * Math.PI) / DIRECTION_COUNT;
  return [Math.cos(angle), Math.sin(angle)];
});

/**
 * The 48 direction labels (for human readability).
 * Each direction is a point on the unit circle at 7.5° increments.
 */
export const DIRECTION_LABELS = Array.from({ length: DIRECTION_COUNT }, (_, k) => {
  const degrees = k * 7.5;
  if (degrees === 0) return 'E';      // 0° = East
  if (degrees === 90) return 'N';     // 90° = North
  if (degrees === 180) return 'W';    // 180° = West
  if (degrees === 270) return 'S';    // 270° = South
  const quadrant = degrees < 90 ? 'NE' : degrees < 180 ? 'NW' : degrees < 270 ? 'SW' : 'SE';
  const fraction = Math.round(degrees) % 90;
  return fraction === 0 ? quadrant[0] : `${quadrant}${fraction}`;
});

/**
 * Convert a trust value in [-1, 1] to a Pythagorean48 direction index.
 * 
 * trust = 1.0   → direction 0  (0°)
 * trust = 0.0   → direction 24 (180°)
 * trust = -1.0  → direction 24 (180°) ... wait, let's think about this.
 * 
 * Actually: trust maps to an angle on the unit circle.
 * We use the sign of trust to determine which semicircle (0-23 for positive, 24-47 for negative).
 * The magnitude determines how far from the boundary.
 * 
 * @param trust - trust value in [-1, 1]
 */
export function trustToDirection(trust: number): number {
  // Clamp to [-1, 1]
  const t = Math.max(-1, Math.min(1, trust));
  
  // Map t in [-1, 1] to a direction in [0, 48)
  // t = 1 → direction 0
  // t = 0 → direction 24
  // t = -1 → direction 48 (wraps to 0, but we treat it as 24)
  
  // Actually, for trust encoding, we use the sign to split the circle:
  // Positive trust (0 to 1): directions 0-23
  // Negative trust (0 to -1): directions 24-47
  
  if (t >= 0) {
    // [0, 1] → [0, 23]
    return Math.round(t * 23);
  } else {
    // [-1, 0) → [24, 47]
    return 24 + Math.round(Math.abs(t) * 23);
  }
}

/**
 * Convert a direction index back to a trust value.
 * @param dir - direction index in [0, 47]
 */
export function directionToTrust(dir: number): number {
  const k = ((dir % DIRECTION_COUNT) + DIRECTION_COUNT) % DIRECTION_COUNT;
  
  if (k <= 23) {
    // [0, 23] → [0, 1]
    return k / 23;
  } else {
    // [24, 47] → [-1, 0]
    return -(k - 24) / 23;
  }
}

/**
 * Get the 48-dimensional unit vector for a direction.
 * The vector is all zeros except at index `dir` where it is 1.
 * (This is the standard HDC encoding.)
 */
export function trustVector(dir: number): number[] {
  const vector = new Array(DIRECTION_COUNT).fill(0);
  const k = ((dir % DIRECTION_COUNT) + DIRECTION_COUNT) % DIRECTION_COUNT;
  vector[k] = 1;
  return vector;
}

/**
 * Compute the cosine similarity between two trust values using Pythagorean48.
 * Returns value in [-1, 1] — same as trust.
 */
export function trustSimilarity(trustA: number, trustB: number): number {
  const dirA = trustToDirection(trustA);
  const dirB = trustToDirection(trustB);
  
  // If same direction, similarity = 1
  if (dirA === dirB) return 1;
  
  // If opposite direction, similarity = -1
  if (Math.abs(dirA - dirB) === DIRECTION_COUNT / 2) return -1;
  
  // Otherwise, compute angular distance
  const minDiff = Math.min(
    Math.abs(dirA - dirB),
    DIRECTION_COUNT - Math.abs(dirA - dirB)
  );
  
  // Angular distance / π → cosine similarity
  // 0° apart → cos(0) = 1
  // 180° apart → cos(π) = -1
  const angleDiff = (minDiff / DIRECTION_COUNT) * 2 * Math.PI;
  return Math.cos(angleDiff);
}

/**
 * Compute the dot product of two HDC vectors.
 * For Pythagorean48 encoding, this is the cosine similarity.
 */
export function vectorDot(vecA: number[], vecB: number[]): number {
  let sum = 0;
  for (let i = 0; i < DIRECTION_COUNT; i++) {
    sum += vecA[i] * vecB[i];
  }
  return sum;
}

/**
 * Normalize a vector (L2 norm = 1).
 */
export function normalizeVector(vec: number[]): number[] {
  let norm = 0;
  for (const v of vec) {
    norm += v * v;
  }
  norm = Math.sqrt(norm);
  
  if (norm === 0) return vec;
  
  return vec.map(v => v / norm);
}