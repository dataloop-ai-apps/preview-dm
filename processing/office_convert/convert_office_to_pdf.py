#!/usr/bin/env python3
"""
Securely convert Office files (Word, Excel, PowerPoint) to PDF using LibreOffice headless.

Usage:
  python convert_office_to_pdf.py --input /path/to/input.docx --output /path/to/output.pdf

Notes:
- Requires LibreOffice installed in the container (soffice available in PATH)
- Supported extensions: .doc, .docx, .rtf, .odt, .xls, .xlsx, .xlsm, .xlsb, .ods, .ppt, .pptx, .odp
- Runs entirely offline in your container/infra; no public URLs required
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import dtlpy as dl

SUPPORTED_EXTS = {
    ".doc", ".docx", ".rtf", ".odt",
    ".xls", ".xlsx", ".xlsm", ".xlsb", ".ods",
    ".ppt", ".pptx", ".odp",
}


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")


def convert_to_pdf(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")
    if input_path.suffix.lower() not in SUPPORTED_EXTS:
        raise ValueError(f"Unsupported extension: {input_path.suffix}. Supported: {sorted(SUPPORTED_EXTS)}")

    # LibreOffice writes output to a directory; we stage in a temp dir to avoid perms/path quirks
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        staged_input = tmpdir_p / input_path.name
        shutil.copy2(input_path, staged_input)

        # Use a separate user profile dir to avoid concurrent lock issues in containers
        lo_profile = tmpdir_p / "lo_profile"
        lo_profile.mkdir(parents=True, exist_ok=True)

        # Convert to PDF
        cmd = [
            "soffice",
            "--headless",
            f"-env:UserInstallation=file://{lo_profile}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmpdir_p),
            str(staged_input),
        ]
        run(cmd)

        # Figure out resulting filename (LibreOffice keeps base name and changes extension)
        produced = tmpdir_p / (staged_input.stem + ".pdf")
        if not produced.exists():
            # Some rare cases keep original extension uppercase/lowercase differences
            candidates = list(tmpdir_p.glob("*.pdf"))
            if not candidates:
                raise RuntimeError("LibreOffice did not produce a PDF output")
            produced = candidates[0]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(produced), str(output_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Office file to PDF using LibreOffice headless")
    parser.add_argument("--item_id", required=True, help="Item ID of Office file")
    args = parser.parse_args()

    main_item = dl.items.get(item_id=args.item_id)
    input_path = main_item.download(save_locally=True)
    output_path = '/tmp/app/' + Path(input_path).with_suffix('.pdf').name + '_'  + args.item_id

    try:
        convert_to_pdf(Path(input_path), Path(output_path))
        modality_item = main_item.project.datasets._get_binaries_dataset().items.upload(local_path=output_path, remote_path='/dm_preview')
        # Create a modality link for the main item
        main_item.modalities.create(
            name='Preview',        # Name for the modality
            modality_type=dl.ModalityTypeEnum.PREVIEW,  # Type of modality
            ref=modality_item.id        # Reference the modality item
        )
        main_item.update()
        return 0
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


