import dtlpy as dl
import logging
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from pydicom import dcmread
import pydicom.pixel_data_handlers.util as dutil
from typing import Callable, Any, Optional

logger = logging.getLogger('dicom-preview')


class ServiceRunner(dl.BaseServiceRunner):

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
        modality_fn: Optional[Callable[[Any, Any], Any]] = getattr(dutil, 'apply_modality_lut', None)  # type: ignore[attr-defined]
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
        voi_fn: Optional[Callable[[Any, Any], Any]] = getattr(dutil, 'apply_voi_lut', None)  # type: ignore[attr-defined]
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

    def generate_thumbnail(self, item: dl.Item) -> dl.Item:
        """
        Create a PNG thumbnail from the first frame of a DICOM file
        """

        # Validate by mimetype or extension
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
        main_item.update(system_metadata = True)

        return main_item


