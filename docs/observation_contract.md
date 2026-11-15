# Observation contract — first experimental v2 code increment

This module is **implemented** as `src/cyclistics/observation_contract.py` and tested in `tests/test_observation_contract.py`. It validates *candidate image observations* without running object detection, confirming a lane blockage or starting any simulation.

## Input JSON

```json
{
  "schema": "cyclistics.observation.v1",
  "observation_id": "sample-frame-0001",
  "source": "synthetic_fixture",
  "observed_at_utc": "2026-11-14T16:30:00Z",
  "object_class": "truck",
  "confidence": 0.87,
  "bbox_norm_xyxy": [0.2, 0.1, 0.7, 0.8],
  "lane_overlap": null,
  "segment_id": null
}
```

**The above is a synthetic software example**, not a camera result or detected obstruction. Normalized box coordinates are fractions of the image width/height, **not** geographic coordinates. `lane_overlap: null` means "not assessed." If supplied later as true/false, it must come from a separate validated geometry/review step. A `confidence` of 0.87 is only a reported model value, not "87% certainty that the bike lane is blocked."

## Validation contract

- Exactly nine named fields; reject unknown fields to avoid carrying raw images or unexpected personal data.
- Schema must be version `cyclistics.observation.v1`.
- Source is one of `synthetic_fixture`, `roboflow` or `manual_review`; this only labels declared provenance and does **not** authenticate a provider.
- Timestamp must explicitly use UTC `Z`; this value must **not** be silently equated to NetLogo tick numbers or Java event time.
- `confidence` must be a finite numeric value in `[0, 1]`, not a string or boolean.
- `bbox_norm_xyxy` must be four finite normalized numbers ordered `[xmin, ymin, xmax, ymax]` with positive area.
- `lane_overlap` may be `true`, `false` or `null`. `segment_id` may be a known nonempty user-provided ID or `null`.
- The module copies the bounding box; callers may modify the normalized record without mutating the original input.
- **No simulated obstruction is emitted:** converting a candidate observation into a block/clear command requires a separate explicit decision and verified time/segment mapping.

## Reproduce

```powershell
git fetch origin
git switch --track -c feat/advanced-digital-twin-foundation origin/feat/advanced-digital-twin-foundation
docker compose run --build --rm tests
```

If the branch already exists locally, `git switch feat/advanced-digital-twin-foundation` instead. Review `git status` before changing branches; do not discard uncommitted work.

The rest of the advanced tracks (Roboflow inference, ArcGIS page, live event bridge, mixed motor traffic and trajectory-based conflict metrics) are **planned and not implemented**. See [advanced extensions plan](advanced_extensions_plan.md).
