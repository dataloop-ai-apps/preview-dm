import dtlpy as dl
import logging
import tempfile
from pathlib import Path
from typing import Callable, Any, Optional

import numpy as np
from PIL import Image
from pydicom import dcmread
import pydicom.pixel_data_handlers.util as dutil

from processing.utils import run_and_stream

logger = logging.getLogger('preview-processing')


# Supported extensions for office conversion
OFFICE_EXTS = {
    ".doc", ".docx", ".rtf", ".odt",
    ".xls", ".xlsx", ".xlsm", ".xlsb", ".ods",
    ".ppt", ".pptx", ".odp",
}


class ServiceRunner(dl.BaseServiceRunner):

    # -------------------------------------------------------------------------
    # USD Preview Generation
    # -------------------------------------------------------------------------
    def generate_usd_preview(self, item: dl.Item) -> dl.Item:
        """
        Generate a preview for USD files (converts to GLB and creates PNG thumbnail).

        :param item: Dataloop item
        :return: Dataloop item
        """
        item_id = item.id

        usd_mimetypes = [
            'model/usd',
            'application/usd',
            'application/x-usd',
            'application/octet-stream'
        ]
        usd_extensions = ['.usd', '.usda', '.usdc', '.usdb', '.usdz']

        is_usd_file = (
            item.mimetype in usd_mimetypes or
            any(item.name.lower().endswith(ext) for ext in usd_extensions)
        )

        if not is_usd_file:
            raise ValueError(f"Item id: {item.id} is not a USD file! This function expects USD files only")

        # Run Blender command to convert USD to GLB
        blender_script_path = "./processing/usd_to_gltf.py"
        cmd = f"blender -b -P {blender_script_path} -- --item_id {item_id} --format GLB"
        rc = run_and_stream(cmd, timeout=300)
        if rc != 0:
            raise RuntimeError(f"Blender conversion failed with code {rc}")

        updated_item = dl.items.get(item_id=item_id)

        for i in updated_item.modalities.list():
            if i.type == dl.ModalityTypeEnum.PREVIEW:
                preview = i
                break

        # Run Blender command to generate PNG thumbnail
        blender_script_path = "./processing/mesh_to_png.py"
        cmd = f"blender -b -P {blender_script_path} -- --item_id {preview.ref} --main_item_id {item_id} --resolution 400"
        rc = run_and_stream(cmd, timeout=300)
        if rc != 0:
            raise RuntimeError(f"Blender conversion failed with code {rc}")

        return item

    # -------------------------------------------------------------------------
    # DICOM Thumbnail Generation
    # -------------------------------------------------------------------------
    @staticmethod
    def _dicom_first_frame_to_png(dicom_path: Path, png_path: Path) -> None:
        ds = dcmread(str(dicom_path))

        if 'PixelData' not in ds:
            raise ValueError('No PixelData in DICOM')

        arr = ds.pixel_array

        samples_per_pixel = int(getattr(ds, 'SamplesPerPixel', 1))
        if arr.ndim == 3 and samples_per_pixel == 1:
            arr = arr[0]
        elif arr.ndim == 4:
            arr = arr[0]

        # modality LUT (rescale)
        modality_fn: Optional[Callable[[Any, Any], Any]] = getattr(dutil, 'apply_modality_lut', None)
        if modality_fn is not None:
            try:
                arr = modality_fn(arr, ds)
            except (ValueError, TypeError, AttributeError):
                pass

        if samples_per_pixel == 3:
            if arr.dtype != np.uint8:
                arr = arr.astype(np.float32)
                arr -= arr.min()
                maxv = arr.max()
                if maxv > 0:
                    arr /= maxv
                arr = (arr * 255.0).round().astype(np.uint8)
            Image.fromarray(arr, mode='RGB').save(str(png_path))
            return

        # VOI LUT / windowing
        voi_fn: Optional[Callable[[Any, Any], Any]] = getattr(dutil, 'apply_voi_lut', None)
        if voi_fn is not None:
            try:
                arr = voi_fn(arr, ds)
            except (ValueError, TypeError, AttributeError):
                pass

        if getattr(ds, 'PhotometricInterpretation', '') == 'MONOCHROME1':
            arr = np.max(arr) - arr

        arr = arr.astype(np.float32)
        arr -= arr.min()
        maxv = arr.max()
        if maxv > 0:
            arr /= maxv
        arr = (arr * 255.0).round().astype(np.uint8)

        Image.fromarray(arr).save(str(png_path))

    def generate_dicom_thumbnail(self, item: dl.Item) -> dl.Item:
        """
        Create a PNG thumbnail from the first frame of a DICOM file.

        :param item: Dataloop item
        :return: Dataloop item
        """
        dicom_mimetypes = {
            'application/dicom',
            'application/dicom+json',
            'application/dicom+xml',
            'application/octet-stream',
        }
        dicom_exts = {'.dcm', '.dicom'}
        is_dicom = (item.mimetype in dicom_mimetypes) or any(
            item.name.lower().endswith(ext) for ext in dicom_exts
        )
        if not is_dicom:
            raise ValueError(f'Item id: {item.id} is not a DICOM file')

        main_item = dl.items.get(item_id=item.id)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_p = Path(tmpdir)
            dicom_path = Path(main_item.download(save_locally=True, local_path=str(tmpdir_p / main_item.name)))
            out_png = tmpdir_p / (dicom_path.stem + '.png')

            self._dicom_first_frame_to_png(dicom_path, out_png)

            thumbnail_item = main_item.dataset.items.upload(
                local_path=str(out_png),
                remote_path='.dataloop/'
            )

        main_item.metadata['system']['thumbnailId'] = thumbnail_item.id
        main_item.update(system_metadata=True)

        return main_item

    # -------------------------------------------------------------------------
    # Mesh Thumbnail Generation
    # -------------------------------------------------------------------------
    def generate_mesh_thumbnail(self, item: dl.Item) -> dl.Item:
        """
        Generate a PNG thumbnail for supported mesh files using Blender.

        :param item: Dataloop item
        :return: Dataloop item
        """
        mesh_extensions = ['.glb', '.gltf', '.obj', '.stl', '.ply', '.fbx', '.3ds']
        is_mesh = any(item.name.lower().endswith(ext) for ext in mesh_extensions)
        if not is_mesh:
            raise ValueError(f"Item id: {item.id} is not a supported mesh file")

        # Run Blender command to render a PNG preview
        script_path = "./processing/mesh_to_png.py"
        cmd = f"blender -b -P {script_path} -- --item_id {item.id} --resolution 400"
        rc = run_and_stream(cmd, timeout=600)
        if rc != 0:
            raise RuntimeError(f"Mesh thumbnail generation failed with code {rc}")

        return item

    # -------------------------------------------------------------------------
    # Office to PDF Conversion
    # -------------------------------------------------------------------------
    def convert_office_to_pdf(self, item: dl.Item) -> dl.Item:
        """
        Convert an Office document to PDF and attach it as a Preview modality.

        :param item: Dataloop item
        :return: Dataloop item
        """
        is_supported = any(item.name.lower().endswith(ext) for ext in OFFICE_EXTS)
        if not is_supported:
            raise ValueError(f"Item id: {item.id} is not a supported Office document")

        # Download original item
        main_item = dl.items.get(item_id=item.id)
        input_path = Path(main_item.download(save_locally=True))

        # Convert with LibreOffice using run_and_stream into a temporary outdir and profile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_p = Path(tmpdir)
            lo_profile = tmpdir_p / 'lo_profile'
            lo_profile.mkdir(parents=True, exist_ok=True)

            cmd = [
                "soffice",
                "--headless",
                f"-env:UserInstallation=file://{lo_profile}",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmpdir_p),
                str(input_path),
            ]
            rc = run_and_stream(cmd, timeout=900)
            if rc != 0:
                raise RuntimeError(f"Office to PDF conversion failed with code {rc}")

            produced = tmpdir_p / (input_path.stem + ".pdf")
            if not produced.exists():
                candidates = list(tmpdir_p.glob("*.pdf"))
                if not candidates:
                    raise RuntimeError("LibreOffice did not produce a PDF output")
                produced = candidates[0]

            modality_item = (
                main_item.project.datasets._get_binaries_dataset()
                .items.upload(local_path=str(produced), remote_path='/dm_preview')
            )
        main_item.modalities.create(
            name='Preview',
            modality_type=dl.ModalityTypeEnum.PREVIEW,
            ref=modality_item.id,
        )
        main_item.update()

        return main_item

