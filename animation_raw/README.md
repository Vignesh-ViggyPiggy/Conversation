# animation_raw/

Staging area for downloaded/recorded source animation files, before
retargeting them onto your VRM model. Organized by source, one directory
per origin:

- `mixamo/` — FBX files downloaded from [mixamo.com](https://mixamo.com)
  (download "without skin"). Retarget with
  `avatar_scene/convert_mixamo.html`, which reads any FBX file you point
  it at, including ones in here.
- `vrma/` — `.vrma` (VRM Animation) files, e.g. the free samples from
  [VRoid Hub/BOOTH](https://vroid.com/en/news/6HozzBIV0KkcKf9dc1fZGW).
  These already target VRM's own humanoid bones and expressions, so
  there's no bone-name mapping step -- convert with
  `avatar_scene/convert_vrma.html`.
- `quaternius/` — FBX files from
  [Quaternius's Universal Animation Library](https://quaternius.itch.io/universal-animation-library)
  (CC0). One file bundles several named clips -- convert with
  `avatar_scene/convert_quaternius.html`, which lists them in a dropdown.
  Bone map verified against a real sample in `quaternius_rig_map.js`;
  feet stay at rest pose (the rig's foot bones are IK helpers, not part
  of the rotation chain this retargets) and only the thumb is mapped
  among the fingers.
- `cmu_mocap/` — BVH files using the classic ASF/AMC-derived skeleton
  naming, e.g. from the
  [CMU Graphics Lab Motion Capture Database](https://mocap.cs.cmu.edu/)
  or its [cmu-mocap BVH re-export](https://github.com/una-dinosauria/cmu-mocap).
  Convert with `avatar_scene/convert_cmu_bvh.html`. Bone map verified
  against a real sample in `cmu_bvh_rig_map.js` -- other BVH sources will
  only retarget well if they reuse the same bone names.

Before adding support for a new source, check its actual bone/joint
names with `avatar_scene/inspect_skeleton.html` (loads any .fbx or .bvh
and lists its skeleton hierarchy, no VRM needed) rather than guessing a
mapping table from a source's documentation alone -- every rig map in
this project so far was built from a real inspected sample specifically
because a wrong guess is hard to debug visually after the fact.

None of the actual downloaded files are committed to the repo (see
`.gitignore`) — this directory only exists to keep raw source material
organized on disk before conversion. The converted, checked-in output
lives in `lib/motion/clips/` once you've exported it.
