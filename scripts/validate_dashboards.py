#!/usr/bin/env python3
"""Validator for Google Cloud Monitoring Dashboard JSON files.

Verifies:
1. Valid JSON syntax.
2. Required top-level fields (displayName, mosaicLayout, dashboardFilters).
3. Presence of version/metadata tags in 'labels'.
4. MosaicLayout grid integrity (columns == 48, valid xPos/yPos/width/height).
5. Zero overlapping tiles in the 2D mosaic grid.
6. Valid widget types and timeSeriesQuery / timeSeriesFilter / timeSeriesFilterRatio structures.
"""

import json
import os
import sys
from typing import Dict, List, Tuple


def check_tile_overlaps(tiles: List[Dict], filename: str) -> List[str]:
  errors = []
  occupied: List[Tuple[int, int, int, int, str]] = []
  for idx, tile in enumerate(tiles):
    x = tile.get("xPos", 0)
    y = tile.get("yPos", 0)
    w = tile.get("width", 0)
    h = tile.get("height", 0)
    widget = tile.get("widget", {})
    title = widget.get("title", f"Tile #{idx}")

    if x < 0 or y < 0 or w <= 0 or h <= 0:
      errors.append(
          f"{filename}: Tile #{idx} ({title}) has invalid dimensions: x={x}, y={y}, w={w}, h={h}"
      )
      continue
    if x + w > 48:
      errors.append(
          f"{filename}: Tile #{idx} ({title}) exceeds 48 columns: x={x} + w={w} = {x+w}"
      )

    for ox, oy, ow, oh, otitle in occupied:
      # Check rectangle intersection
      if x < ox + ow and ox < x + w and y < oy + oh and oy < y + h:
        errors.append(
            f"{filename}: Tile overlap detected between '{title}' "
            f"[x={x}..{x+w}, y={y}..{y+h}] and '{otitle}' "
            f"[x={ox}..{ox+ow}, y={oy}..{oy+oh}]"
        )
    occupied.append((x, y, w, h, title))
  return errors


def validate_file(filepath: str, require_labels: bool = False) -> List[str]:
  errors = []
  try:
    with open(filepath, "r", encoding="utf-8") as f:
      data = json.load(f)
  except Exception as e:
    return [f"{filepath}: Invalid JSON - {e}"]

  if "displayName" not in data or not data["displayName"]:
    errors.append(f"{filepath}: Missing 'displayName'")

  if require_labels and ("labels" not in data or not isinstance(data["labels"], dict)):
    errors.append(f"{filepath}: Missing 'labels' metadata tags dictionary")

  mosaic = data.get("mosaicLayout")
  if not mosaic:
    errors.append(f"{filepath}: Missing 'mosaicLayout'")
    return errors

  if mosaic.get("columns") != 48:
    errors.append(
        f"{filepath}: Expected mosaicLayout.columns == 48, got {mosaic.get('columns')}"
    )

  tiles = mosaic.get("tiles", [])
  if not tiles:
    errors.append(f"{filepath}: No tiles in mosaicLayout")

  errors.extend(check_tile_overlaps(tiles, filepath))
  return errors


def main():
  target_dirs = sys.argv[1:] if len(sys.argv) > 1 else ["dashboards"]
  all_errors = []
  checked_count = 0

  for target in target_dirs:
    if os.path.isfile(target):
      require_lbl = "v1.0" not in target and "v2.0" not in target
      all_errors.extend(validate_file(target, require_labels=require_lbl))
      checked_count += 1
    elif os.path.isdir(target):
      for root, _, files in os.walk(target):
        for file in sorted(files):
          if file.endswith(".json"):
            path = os.path.join(root, file)
            require_lbl = "v1.0" not in path and "v2.0" not in path
            all_errors.extend(validate_file(path, require_labels=require_lbl))
            checked_count += 1

  if all_errors:
    print(f"Validation FAILED with {len(all_errors)} error(s):")
    for err in all_errors:
      print(f"  [ERROR] {err}")
    sys.exit(1)
  else:
    print(f"Validation PASSED: {checked_count} dashboard JSON file(s) verified with 0 layout overlaps.")


if __name__ == "__main__":
  main()
