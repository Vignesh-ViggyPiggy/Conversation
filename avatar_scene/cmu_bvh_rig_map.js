// Bone name mapping for the classic ASF/AMC-derived BVH skeleton used by
// the CMU Graphics Lab Motion Capture Database (and several other BVH
// re-exports that reuse the same naming) -- verified against a real
// sample (01_01.bvh) via inspect_skeleton.html, not guessed.
//
// LHipJoint/RHipJoint are zero-length socket artifacts of the ASF-to-BVH
// conversion with no VRM equivalent -- omitted. The neck is a two-segment
// chain (Neck, Neck1) collapsing onto VRM's single "neck" bone; only the
// first segment is mapped since VRM has nowhere to put a second one.
// Fingers are minimal (index + thumb only, one segment each) -- mapped
// where a clean single-segment target exists, skipped otherwise
// (LeftFingerBase/RightFingerBase stand in for all four other fingers
// combined, which VRM has no equivalent single bone for).
export const cmuBvhRigMap = {
  Hips: "hips",
  LeftUpLeg: "leftUpperLeg",
  LeftLeg: "leftLowerLeg",
  LeftFoot: "leftFoot",
  LeftToeBase: "leftToes",
  RightUpLeg: "rightUpperLeg",
  RightLeg: "rightLowerLeg",
  RightFoot: "rightFoot",
  RightToeBase: "rightToes",
  LowerBack: "spine",
  Spine: "chest",
  Spine1: "upperChest",
  Neck: "neck",
  Head: "head",
  LeftShoulder: "leftShoulder",
  LeftArm: "leftUpperArm",
  LeftForeArm: "leftLowerArm",
  LeftHand: "leftHand",
  LeftHandIndex1: "leftIndexProximal",
  LThumb: "leftThumbProximal",
  RightShoulder: "rightShoulder",
  RightArm: "rightUpperArm",
  RightForeArm: "rightLowerArm",
  RightHand: "rightHand",
  RightHandIndex1: "rightIndexProximal",
  RThumb: "rightThumbProximal",
};

export const CMU_BVH_HIPS_NAME = "Hips";
