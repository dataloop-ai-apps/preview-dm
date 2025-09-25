import dtlpy as dl
import logging
from processing.default_service_runner import run_and_stream

logger = logging.getLogger('mesh-thumbnail')


class ServiceRunner(dl.BaseServiceRunner):

    def generate_thumbnail(self, item: dl.Item) -> dl.Item:
        """
        Generate a PNG thumbnail for supported mesh files using Blender.

        :param item: Dataloop item
        :return: Dataloop item
        """

        # Validate supported mesh types
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


