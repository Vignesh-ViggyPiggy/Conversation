# animation_raw/

Staging area for downloaded/recorded source animation files, before
retargeting them onto your VRM model. Organized by source, one directory
per origin:

- `mixamo/` — FBX files downloaded from [mixamo.com](https://mixamo.com)
  (download "without skin"). Retarget with
  `avatar_scene/convert_mixamo.html`, which reads any FBX file you point
  it at, including ones in here.

Add sibling directories for other sources as they come up (e.g. a future
`webcam/` for recorded takes, or a directory for another motion-capture
dataset), each with its own conversion tool if the source format needs
one.

None of the actual downloaded files are committed to the repo (see
`.gitignore`) — this directory only exists to keep raw source material
organized on disk before conversion. The converted, checked-in output
lives in `lib/motion/clips/` once you've exported it.
