import dtlpy as dl
import logging
from processing.default_service_runner import run_and_stream

logger = logging.getLogger('quality-estimator')


class ServiceRunner(dl.BaseServiceRunner):

    def generate_preview(self, item: dl.Item) -> dl.Item:
        """
        The generating preview for the item.

        :param item: Dataloop item
        :return: Dataloop item
        """

        item_id = item.id

        # Check if item is a USD file type
        usd_mimetypes = [
            'model/usd',
            'application/usd',
            'application/x-usd',
            'application/octet-stream'  # Generic binary, might be USD
        ]
        
        usd_extensions = ['.usd', '.usda', '.usdc', '.usdb', '.usdz']
        
        # Check mimetype or file extension
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

        # Run Blender command to convert USD to GLB
        blender_script_path = "./processing/mesh_to_png.py"
        cmd = f"blender -b -P {blender_script_path} -- --item_id {preview.ref} --main_item_id {item_id} --resolution 400"
        rc = run_and_stream(cmd, timeout=300)
        if rc != 0:
            raise RuntimeError(f"Blender conversion failed with code {rc}")
        


        return item