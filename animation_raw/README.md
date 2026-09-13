# animation_raw/

Staging area for downloaded/recorded source animation files, before
retargeting them onto your VRM model. Organized by source, one directory
per origin:

- `mixamo/` — FBX files downloaded from [mixamo.com](https://mixamo.com)
  (download "without skin"). Retarget with
  `avatar_scene/convert_mixamo.html`, which reads any FBX file you point
  it at, including ones in here.

Other sources (Quaternius, CMU BVH mocap, VRMA) were tried and rolled
back -- see git history if picking one back up later. Next planned
source is recording reference footage yourself via webcam, which
sidesteps third-party rig-naming/licensing questions entirely; add a
`webcam/` directory here when that's built.

None of the actual downloaded files are committed to the repo (see
`.gitignore`) — this directory only exists to keep raw source material
organized on disk before conversion. The converted, checked-in output
lives in `lib/motion/clips/` once you've exported it.
