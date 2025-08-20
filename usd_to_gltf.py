#!/usr/bin/env python3
"""
Convert .usd/.usda/.usdc/.usdb/.usdz to GLB or glTF (embedded) using Blender headless.

Usage (with Blender installed):
  python3 usd_to_gltf.py --input /path/model.usdz --output /path/model.glb --format GLB
  blender -b -P usd_to_gltf.py -- --input /path/model.usd --output /path/model.gltf --format GLTF_EMBEDDED

Notes:
  - Requires Blender 3.x with USD importer (standard builds include it)
  - If run outside Blender, this script spawns Blender automatically (use BLENDER_PATH env or keep blender on PATH)
  - USDZ is unzipped to a temp folder and the stage (.usda/.usd/.usdc/.usdb) inside is imported
  - If --input is a directory, we scan it for a main USD stage file (preferring .usda, then .usd, then .usdc/.usdb)
"""

import os
import sys
import argparse
import tempfile
import zipfile
import shutil
import glob
import subprocess
from typing import Optional, Tuple
import dtlpy as dl
from pathlib import Path
import logging



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_running_in_blender() -> bool:
    try:
        import bpy  # noqa: F401
        return True
    except Exception:
        return False


def _find_stage_in_dir(dir_path: str) -> str:
    # Prefer root files first, then recurse; prefer .usda over .usd over .usdc/.usdb
    candidates = []
    for pat in ("*.usda", "*.usd", "*.usdc", "*.usdb"):
        candidates.extend(glob.glob(os.path.join(dir_path, pat)))
    if not candidates:
        for pat in ("**/*.usda", "**/*.usd", "**/*.usdc", "**/*.usdb"):
            candidates.extend(glob.glob(os.path.join(dir_path, pat), recursive=True))
    if not candidates:
        raise RuntimeError("No USD stage (.usda/.usd/.usdc/.usdb) found in directory")

    def score(p: str) -> Tuple[int, int]:
        ext = os.path.splitext(p)[1].lower()
        ext_rank = {".usda": 0, ".usd": 1, ".usdc": 2, ".usdb": 2}.get(ext, 3)
        depth = p.count(os.sep)
        return (ext_rank, depth)

    candidates.sort(key=score)
    return candidates[0]


def _find_stage_in_usdz(usdz_path: str, extract_dir: str) -> str:
    with zipfile.ZipFile(usdz_path, "r") as zf:
        zf.extractall(extract_dir)
    return _find_stage_in_dir(extract_dir)


def _normalize_output_path(out_path: str, fmt: str) -> str:
    fmt = fmt.upper()
    if fmt == "GLB" and not out_path.lower().endswith(".glb"):
        out_path += ".glb"
    if fmt in ("GLTF_EMBEDDED", "GLTF") and not out_path.lower().endswith(".gltf"):
        out_path += ".gltf"
    return out_path


def _blender_exec_path() -> Optional[str]:
    return os.environ.get("BLENDER_PATH") or "blender"


def _run_under_blender(input_path: str, output_path: str, fmt: str) -> None:
    import bpy  # type: ignore

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(filepath=input_path)

    export_fmt = "GLB" if fmt.upper() == "GLB" else "GLTF_EMBEDDED"
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format=export_fmt,
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        use_selection=False,
    )


def _spawn_blender_this_script(input_path: str, output_path: str, fmt: str) -> None:
    blender = _blender_exec_path()
    cmd = [
        blender,
        "-b",
        "-P",
        os.path.abspath(__file__),
        "--",
        "--input",
        input_path,
        "--output",
        output_path,
        "--format",
        fmt,
        "--blender-mode",
        "1",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Blender failed (code {proc.returncode}):\n{proc.stdout}")


def convert_usd_like_to_gltf(input_path: str, output_path: str, fmt: str = "GLB") -> str:
    """
    Convert .usd/.usda/.usdc/.usdb/.usdz (or a directory containing them) to GLB or glTF embedded (.gltf).
    Returns the output file path.
    """
    fmt = fmt.upper()
    if fmt not in ("GLB", "GLTF_EMBEDDED", "GLTF"):
        raise ValueError("format must be GLB or GLTF_EMBEDDED")
    src = os.path.abspath(input_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"Input not found: {src}")

    output_path = '/tmp/app/' + Path(input_path).with_suffix('.glb').name
    print(output_path)

    out = _normalize_output_path(os.path.abspath(output_path), fmt)
    print('out', out)
    tmp_dir = None
    stage_path = src
    try:
        if os.path.isdir(src):
            stage_path = _find_stage_in_dir(src)
        elif src.lower().endswith(".usdz"):
            tmp_dir = tempfile.mkdtemp(prefix="usdz_")
            stage_path = _find_stage_in_usdz(src, tmp_dir)

        if _is_running_in_blender():
            _run_under_blender(stage_path, out, fmt)
        else:
            _spawn_blender_this_script(stage_path, out, fmt)
        return out
    finally:
        if tmp_dir and os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _parse_args(argv):
    p = argparse.ArgumentParser(
        description="Convert USD/USDA/USDC/USDB/USDZ (or folder) → GLB or GLTF(embedded) via Blender"
    )
    p.add_argument("--item_id", required=True, help="Item ID of file which is .usd/.usda/.usdc/.usdb/.usdz")
    p.add_argument(
        "--format",
        default="GLB",
        choices=["GLB", "GLTF_EMBEDDED", "GLTF"],
        help="Output format",
    )
    p.add_argument("--blender-mode", default="0", help=argparse.SUPPRESS)
    return p.parse_args(argv)


def main():
    args = _parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:])
    main_item = dl.items.get(item_id=args.item_id)
    input_path = main_item.download(save_locally=True)
    output_path = '/tmp/app/' + Path(input_path).with_suffix('.glb').name
    if not _is_running_in_blender() and args.blender_mode != "1":
        out = _normalize_output_path(os.path.abspath(output_path), args.format)
        _spawn_blender_this_script(os.path.abspath(input_path), out, args.format)
        print(out)
        return

    out = convert_usd_like_to_gltf(input_path, output_path, args.format)
    # modality_item = main_item.project.datasets._get_binaries_dataset().items.upload(local_path=out, remote_path='/dm_preview')
    # # Create a modality link for the main item
    # main_item.modalities.create(
    #     name='Preview',        # Name for the modality
    #     modality_type=dl.ModalityTypeEnum.PREVIEW,  # Type of modality
    #     ref=modality_item.id        # Reference the modality item
    # )

    # # Update the main item to apply changes
    # main_item.update()

if __name__ == "__main__":
    main()


