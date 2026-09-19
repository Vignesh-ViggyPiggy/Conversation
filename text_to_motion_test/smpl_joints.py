"""Shared HumanML3D/SMPL 22-joint skeleton metadata.

Verified against motion-diffusion-model's own
data_loaders/humanml/utils/paramUtil.py (t2m_kinematic_chain):

    [[0, 2, 5, 8, 11], [0, 1, 4, 7, 10], [0, 3, 6, 9, 12, 15],
     [9, 14, 17, 19, 21], [9, 13, 16, 18, 20]]

Joint indices 0-21 are the first 22 of SMPL's 24-joint skeleton (hands,
indices 22/23, are dropped -- HumanML3D/MDM never use them).
"""

JOINT_NAMES = [
    "Pelvis", "L_Hip", "R_Hip", "Spine1", "L_Knee", "R_Knee", "Spine2",
    "L_Ankle", "R_Ankle", "Spine3", "L_Foot", "R_Foot", "Neck", "L_Collar",
    "R_Collar", "Head", "L_Shoulder", "R_Shoulder", "L_Elbow", "R_Elbow",
    "L_Wrist", "R_Wrist",
]

# Parent index per joint (root's parent is -1), derived from the
# kinematic chain above.
PARENTS = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19]

# SMPL joint name -> VRM humanoid bone name. Not every VRM model rigs
# every one of these (toes and upperChest are often missing) -- the
# browser-side retargeter skips whatever the loaded model doesn't have,
# same as avatar_scene/convert_mixamo.html does for Mixamo bones.
VRM_BONE_MAP = {
    "Pelvis": "hips",
    "L_Hip": "leftUpperLeg",
    "R_Hip": "rightUpperLeg",
    "Spine1": "spine",
    "L_Knee": "leftLowerLeg",
    "R_Knee": "rightLowerLeg",
    "Spine2": "chest",
    "L_Ankle": "leftFoot",
    "R_Ankle": "rightFoot",
    "Spine3": "upperChest",
    "L_Foot": "leftToes",
    "R_Foot": "rightToes",
    "Neck": "neck",
    "L_Collar": "leftShoulder",
    "R_Collar": "rightShoulder",
    "Head": "head",
    "L_Shoulder": "leftUpperArm",
    "R_Shoulder": "rightUpperArm",
    "L_Elbow": "leftLowerArm",
    "R_Elbow": "rightLowerArm",
    "L_Wrist": "leftHand",
    "R_Wrist": "rightHand",
}


def as_skeleton_dict() -> dict:
    return {"joint_names": JOINT_NAMES, "parents": PARENTS, "vrm_bone_map": VRM_BONE_MAP}
