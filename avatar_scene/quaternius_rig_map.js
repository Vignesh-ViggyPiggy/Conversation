// Bone name mapping for Quaternius's "Universal Animation Library" rig
// (verified against a real sample, Female_Alternative.fbx, via
// inspect_skeleton.html -- not guessed). The rig's IK-helper bones
// (FootL/FootR/PoleTargetL/PoleTargetR, under a separate "Bone" root
// from the actual deform chain under "Body") have no FK rotation data
// useful for retargeting and are intentionally omitted -- feet will
// stay at rest pose for clips retargeted through this map, which is
// safe (just not fully accurate) rather than wrong.
//
// The hand rig is simplified relative to VRM's per-finger chains: a
// single "FingersX" bone stands in for all four non-thumb fingers, and
// "MiddleHandX" is an intermediate palm bone with no VRM equivalent --
// both are omitted rather than force-mapped to something misleading.
// Only the two-segment thumb chain maps cleanly.
export const quaterniusVRMRigMap = {
  Hips: "hips",
  Abdomen: "spine",
  Torso: "chest",
  Neck: "neck",
  Head: "head",
  ShoulderL: "leftShoulder",
  ShoulderR: "rightShoulder",
  UpperArmL: "leftUpperArm",
  UpperArmR: "rightUpperArm",
  LowerArmL: "leftLowerArm",
  LowerArmR: "rightLowerArm",
  PalmL: "leftHand",
  PalmR: "rightHand",
  Thumb1L: "leftThumbProximal",
  Thumb2L: "leftThumbDistal",
  Thumb1R: "rightThumbProximal",
  Thumb2R: "rightThumbDistal",
  UpperLegL: "leftUpperLeg",
  UpperLegR: "rightUpperLeg",
  LowerLegL: "leftLowerLeg",
  LowerLegR: "rightLowerLeg",
};

// Hip bone name used for the hip-height scale reference (see
// convert_quaternius.html) -- Mixamo's equivalent is "mixamorigHips".
export const QUATERNIUS_HIPS_NAME = "Hips";
