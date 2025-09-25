import dtlpy as dl
import logging
import tempfile
from pathlib import Path
from processing.utils import run_and_stream

logger = logging.getLogger('office-convert')


SUPPORTED_EXTS = {
    ".doc", ".docx", ".rtf", ".odt",
    ".xls", ".xlsx", ".xlsm", ".xlsb", ".ods",
    ".ppt", ".pptx", ".odp",
}


class ServiceRunner(dl.BaseServiceRunner):

    def convert_to_pdf(self, item: dl.Item) -> dl.Item:
        """
        Convert an Office document to PDF and attach it as a Preview modality.

        :param item: Dataloop item
        :return: Dataloop item
        """

        is_supported = any(item.name.lower().endswith(ext) for ext in SUPPORTED_EXTS)
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


