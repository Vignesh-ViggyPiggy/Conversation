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

Add sibling directories for other sources as they come up (e.g. a future
`webcam/` for recorded takes, or another motion-capture dataset), each
with its own conversion tool if the source format needs one. FBX-based
sources whose skeleton doesn't use Mixamo's bone-naming convention (e.g.
Quaternius's animation packs) or BVH-based sources (e.g. the CMU Graphics
Lab Motion Capture Database) aren't supported by the current converters
yet -- their bone/joint names haven't been verified against real sample
files, so a hardcoded mapping table risked being silently wrong. Adding
them needs a bone-mapping step the user can verify (auto-guess + manual
correction) rather than another hardcoded name table -- see the project
discussion this came out of before building it.

None of the actual downloaded files are committed to the repo (see
`.gitignore`) — this directory only exists to keep raw source material
organized on disk before conversion. The converted, checked-in output
lives in `lib/motion/clips/` once you've exported it.
