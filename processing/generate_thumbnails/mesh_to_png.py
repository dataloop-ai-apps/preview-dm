#!/usr/bin/env python3
"""
Convert mesh files (.glb, .gltf, .obj, .stl, .ply, .fbx, .3ds) to PNG preview images using Blender headless.

Usage (with Blender installed):
  python3 mesh_to_png.py --item_id <dataloop_item_id> --resolution 1024
  blender -b -P mesh_to_png.py -- --item_id <dataloop_item_id> --resolution 1024

Notes:
  - Requires Blender 3.x+ with appropriate importers
  - If run outside Blender, this script spawns Blender automatically (use BLENDER_PATH env or keep blender on PATH)
  - Full support: .glb, .gltf, .obj, .stl, .ply, .fbx, .3ds formats
  - Creates optimized camera angle and lighting for preview
"""

import os
import sys
import argparse
import subprocess
from typing import Optional, TYPE_CHECKING
import dtlpy as dl
from pathlib import Path
import uuid
import logging
import math

if TYPE_CHECKING:
    from mathutils import Vector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_running_in_blender() -> bool:
    try:
        import bpy  # noqa: F401
        return True
    except ImportError:
        return False


def _blender_exec_path() -> Optional[str]:
    return os.environ.get("BLENDER_PATH") or "blender"


def _import_mesh_file(filepath: str) -> None:
    """Import mesh file based on extension"""
    import bpy
    
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == '.glb':
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext == '.gltf':
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext == '.obj':
            # Try newer API first, fall back to older
            try:
                bpy.ops.wm.obj_import(filepath=filepath)
            except AttributeError:
                bpy.ops.import_scene.obj(filepath=filepath)
        elif ext == '.stl':
            # Try different STL import operators depending on Blender version
            try:
                bpy.ops.wm.stl_import(filepath=filepath)
            except AttributeError:
                try:
                    bpy.ops.import_mesh.stl(filepath=filepath)
                except AttributeError:
                    # Try enabling STL addon if it exists
                    try:
                        bpy.ops.preferences.addon_enable(module="io_mesh_stl")
                        bpy.ops.import_mesh.stl(filepath=filepath)
                    except Exception:
                        raise RuntimeError(f"STL importer not available in this Blender version")

        elif ext == '.ply':
            # Try newer API first, fall back to older
            try:
                bpy.ops.wm.ply_import(filepath=filepath)
            except AttributeError:
                bpy.ops.import_mesh.ply(filepath=filepath)
            
            # PLY files often need rotation to match Three.js orientation
            _fix_orientation(rotation_axis='X', rotation_value=-90)
        elif ext == '.fbx':
            # Try FBX import with addon enabling fallback
            try:
                bpy.ops.import_scene.fbx(filepath=filepath)
            except AttributeError:
                try:
                    bpy.ops.preferences.addon_enable(module="io_scene_fbx")
                    bpy.ops.import_scene.fbx(filepath=filepath)
                except Exception:
                    raise RuntimeError(f"FBX importer not available in this Blender version")
        elif ext == '.3ds':
            # 3DS import - should work natively in Blender 4.1.1
            logger.info(f"Importing 3DS file: {filepath}")
            
            # Enable the 3DS addon and refresh operator registry
            try:
                # Try multiple addon names that might work
                addon_names = ['io_scene_3ds', 'io_import_3ds', 'import_export_3ds']
                addon_enabled = False
                
                for addon_name in addon_names:
                    try:
                        bpy.ops.preferences.addon_enable(module=addon_name)
                        logger.info(f"Successfully enabled addon: {addon_name}")
                        addon_enabled = True
                        break
                    except Exception as e:
                        logger.debug(f"Failed to enable addon {addon_name}: {e}")
                        continue
                
                if not addon_enabled:
                    # List all available addons for debugging
                    logger.info("Available addons containing '3ds':")
                    for addon in bpy.context.preferences.addons.keys():
                        if '3ds' in addon.lower():
                            logger.info(f"  - {addon}")
                
                # Addon enabled successfully, proceed with import
                
                # Try different operator names that might work in 4.1.1
                operators_to_try = [
                    'import_scene.max3ds',      # This is the correct one for Blender 4.1.1
                    'import_scene.autodesk_3ds',
                    'import_scene.max_3ds', 
                    'import_scene.threeds',
                    'wm.3ds_import',
                    'import_mesh.threeds'
                ]
                
                import_success = False
                for op_name in operators_to_try:
                    try:
                        logger.info(f"Trying operator: {op_name}")
                        op_parts = op_name.split('.')
                        op_module = getattr(bpy.ops, op_parts[0])
                        op_func = getattr(op_module, op_parts[1])
                        op_func(filepath=filepath)
                        logger.info(f"Successfully imported 3DS file using: {op_name}")
                        import_success = True
                        break
                    except (AttributeError, RuntimeError) as e:
                        logger.debug(f"Operator {op_name} failed: {e}")
                        continue
                
                if not import_success:
                    # Debug: List all available import operators
                    logger.info("Available import operators:")
                    for attr_name in dir(bpy.ops.import_scene):
                        if not attr_name.startswith('_'):
                            logger.info(f"  - import_scene.{attr_name}")
                    
                    raise RuntimeError(f"No working 3DS import operator found in Blender {bpy.app.version_string}")
                    
            except Exception as e:
                logger.error(f"3DS import failed: {e}")
                raise RuntimeError(f"Failed to import 3DS file. Blender 4.1.1 should support 3DS natively. Error: {str(e)}")
            
            # 3DS files: Handle lights and rotation to match Three.js orientation
            _handle_3ds_post_import()
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        raise RuntimeError(f"Failed to import {ext} file '{filepath}': {str(e)}") from e


def _handle_3ds_post_import() -> None:
    """Handle 3DS-specific post-import tasks: adjust materials and apply correct rotation"""
    import bpy
    
    logger.info("Handling 3DS post-import tasks...")
    
    # Debug and potentially adjust 3DS materials to better match Three.js
    # _debug_and_adjust_3ds_materials()
    _fix_orientation(rotation_axis='X', rotation_value=90)


    
    logger.info("3DS post-import handling completed")


def _debug_and_adjust_3ds_materials() -> None:
    """Debug and adjust 3DS materials to better match Three.js behavior"""
    import bpy
    
    logger.info("Debugging 3DS materials...")
    
    # Check all materials in the scene
    materials_found = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.data.materials:
            for i, mat in enumerate(obj.data.materials):
                if mat is not None:
                    materials_found += 1
                    logger.info(f"Object '{obj.name}' Material {i}: '{mat.name}'")
                    
                    # Debug material properties
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.type == 'BSDF_PRINCIPLED':
                                base_color = node.inputs['Base Color'].default_value
                                metallic = node.inputs['Metallic'].default_value
                                roughness = node.inputs['Roughness'].default_value
                                logger.info(f"  - Base Color: {base_color[:3]} (RGB)")
                                logger.info(f"  - Metallic: {metallic}, Roughness: {roughness}")
                                
                                # Adjust materials to be more Three.js-like
                                # Three.js MeshStandardMaterial defaults: metalness=0.0, roughness=0.9
                                # Match the defaults used in MeshViewer.vue applyFallbackMaterials
                                if metallic != 0.0:
                                    logger.info(f"  - Adjusting metallic from {metallic} to 0.0 (Three.js MeshStandardMaterial default)")
                                    node.inputs['Metallic'].default_value = 0.0
                                    
                                if abs(roughness - 0.9) > 0.1:  # Only adjust if significantly different
                                    logger.info(f"  - Adjusting roughness from {roughness} to 0.9 (Three.js MeshStandardMaterial default)")
                                    node.inputs['Roughness'].default_value = 0.9
                                
                                # Ensure colors are in sRGB space (like Three.js)
                                # Convert if needed - this helps with color matching
                                if hasattr(node.inputs['Base Color'], 'default_value'):
                                    color = node.inputs['Base Color'].default_value
                                    logger.info(f"  - Preserving color: {color[:3]} (matching Three.js)")
                    else:
                        # Legacy material without nodes
                        logger.info(f"  - Legacy material (non-node): diffuse_color = {mat.diffuse_color[:3]}")
    
    if materials_found == 0:
        logger.info("No materials found in 3DS file")
    else:
        logger.info(f"Processed {materials_found} materials from 3DS file")


def _fix_orientation(rotation_axis: str, rotation_value: float) -> None:
    """Fix PLY and 3DS file orientation to match Three.js display"""
    import bpy
    import math
    
    # Get all mesh objects that were just imported
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    
    if mesh_objects:
        # Some mesh formats have different coordinate system conventions
        # Apply rotation to match Three.js orientation
        
        # First, deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        for obj in mesh_objects:
            # Select only this object
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # Rotate around specified axis by specified degrees to match Three.js display
            # This fixes files that appear with incorrect orientation
            bpy.ops.transform.rotate(value=math.radians(rotation_value), orient_axis=rotation_axis)
            
            # Try to apply the transformation, but handle multi-user case gracefully
            try:
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                logger.info(f"Applied transform to object: {obj.name}")
            except RuntimeError as e:
                if "multi user" in str(e).lower():
                    logger.warning(f"Skipping transform apply for {obj.name} (multi-user mesh data)")
                    # The rotation was already applied, just not baked into the mesh
                else:
                    logger.error(f"Failed to apply transform to {obj.name}: {e}")
                    raise
            
            # Deselect this object before moving to the next
            obj.select_set(False)


def _enable_required_addons() -> None:
    """Enable all required addons for mesh importing"""
    import bpy
    
    # Only enable addons when actually needed during import
    # This avoids trying to enable non-existent addons upfront
    pass


def _setup_scene_for_preview() -> None:
    """Set up optimal lighting, camera, and materials for mesh preview"""
    import bpy
    
    # Enable required addons first
    _enable_required_addons()
    
    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Set render engine to Cycles for better quality
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128  # Good balance of quality/speed
    bpy.context.scene.cycles.use_denoising = True
    
    # Set transparent background
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    
    # Simple lighting setup to match MeshViewer.vue exactly
    # Create world for ambient lighting (like THREE.AmbientLight)
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new(name="World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    world_nodes = world.node_tree.nodes
    world_nodes.clear()
    
    # Create ambient lighting through world shader (equivalent to AmbientLight)
    background_node = world_nodes.new('ShaderNodeBackground')
    output_node = world_nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(background_node.outputs['Background'], output_node.inputs['Surface'])
    
    # Set ambient light strength (like THREE.AmbientLight(0xffffff, 1))
    background_node.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)  # White
    background_node.inputs['Strength'].default_value = 1.0  # Energy 1.0
    
    # Note: Lights will be added later only if needed (after mesh import)


def _add_fallback_lighting_if_needed() -> None:
    """Add default lighting only if the imported file has no lights"""
    import bpy
    
    # Check if the imported file brought any lights
    imported_lights = [obj for obj in bpy.context.scene.objects if obj.type == 'LIGHT']
    
    if imported_lights:
        logger.info(f"File has {len(imported_lights)} lights - using file's original lighting")
        # Keep whatever lights the file has, don't add any additional ones
    else:
        logger.info("File has no lights - adding default preview lighting")
        # Add our default directional light (like THREE.DirectionalLight in MeshViewer.vue)
        bpy.ops.object.light_add(type='SUN', location=(2, 2, 3))
        dir_light = bpy.context.object
        dir_light.data.energy = 0.8
        dir_light.name = "DefaultPreviewLight"


def _position_camera_for_object() -> None:
    """Position camera optimally to frame the imported object(s) - front-facing view like MeshViewer.vue"""
    import bpy
    from mathutils import Vector
    
    # Get all mesh objects
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    
    if not mesh_objects:
        raise RuntimeError("No mesh objects found to render")
    
    # Calculate bounding box of all objects
    min_coords = Vector((float('inf'), float('inf'), float('inf')))
    max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))
    
    for obj in mesh_objects:
        # Update object transforms
        bpy.context.view_layer.update()
        
        # Get world space bounding box
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        
        for corner in bbox_corners:
            for i in range(3):
                min_coords[i] = min(min_coords[i], corner[i])
                max_coords[i] = max(max_coords[i], corner[i])
    
    # Calculate center and size (similar to MeshViewer.vue fitCameraToObject)
    center = (min_coords + max_coords) / 2
    size = max_coords - min_coords
    max_size = max(size.x, size.y, size.z)
    
    # Add camera
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    
    # Set camera properties to match MeshViewer.vue (60° FOV)
    camera.data.lens_unit = 'FOV'
    camera.data.angle = math.radians(60)  # 60 degrees like in Vue component
    
    # Calculate distance needed to fit the object (similar to MeshViewer.vue logic)
    factor = 1.1  # Similar to the factor used in Vue component
    fov_radians = camera.data.angle
    fit_height_distance = max_size / (2 * math.tan(fov_radians / 2))
    # Assume square aspect ratio for PNG output
    distance = factor * fit_height_distance
    
    # Position camera in front of object (front-facing like MeshViewer.vue)
    # In Blender, front view is typically along negative Y axis (not Z like Three.js)
    # So position camera in front (negative Y direction from center)
    camera.location = Vector((center.x, center.y - 2 * distance, center.z))
    
    # Make camera look at the center (camera looks along positive Y axis toward center)
    direction = center - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Set near and far planes
    camera.data.clip_start = distance / 100
    camera.data.clip_end = distance * 100





def _enhance_materials() -> None:
    """Apply fallback materials only when none exist (matching MeshViewer.vue behavior)"""
    import bpy
    
    objects_with_materials = 0
    objects_needing_materials = 0
    
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            # Only add material if object has no materials (matching Three.js behavior)
            if not obj.data.materials or all(mat is None for mat in obj.data.materials):
                objects_needing_materials += 1
                logger.info(f"Object '{obj.name}' has no materials - adding default material")
                
                # Create a default material only when none exists
                mat = bpy.data.materials.new(name="PreviewMaterial")
                mat.use_nodes = True
                obj.data.materials.append(mat)
                
                # Set up the new material with basic properties
                nodes = mat.node_tree.nodes
                principled = None
                for node in nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        principled = node
                        break
                
                if principled:
                    # Only set properties for NEW materials (like Three.js fallback)
                    principled.inputs['Base Color'].default_value = (0.7, 0.7, 0.7, 1.0)
                    principled.inputs['Roughness'].default_value = 0.9
                    principled.inputs['Metallic'].default_value = 0.0
            else:
                objects_with_materials += 1
            
            # Do NOT modify existing materials - preserve original colors like Three.js does
    
    logger.info(f"Materials: {objects_with_materials} objects kept original materials, {objects_needing_materials} got default materials")


def _run_under_blender(input_path: str, output_path: str, resolution: int) -> None:
    """Main Blender execution function"""
    import bpy
    
    # Start with clean scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Set up scene for preview rendering
    _setup_scene_for_preview()
    
    # Import the mesh file
    _import_mesh_file(input_path)
    
    # Check if any objects were imported
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not mesh_objects:
        raise RuntimeError("No mesh objects found after import. The file might be corrupted or empty.")
    
    # Smart lighting: only add our default lights if file has no lights
    _add_fallback_lighting_if_needed()
    
    # Enhance materials
    _enhance_materials()
    
    # Position camera optimally
    _position_camera_for_object()
    
    # Set render resolution
    bpy.context.scene.render.resolution_x = resolution
    bpy.context.scene.render.resolution_y = resolution
    bpy.context.scene.render.resolution_percentage = 100
    
    # Render and save
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def _spawn_blender_this_script(input_path: str, output_path: str, resolution: int) -> None:
    """Spawn Blender subprocess to run this script"""
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
        "--resolution",
        str(resolution),
        "--blender-mode",
        "1",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Blender failed (code {proc.returncode}):\n{proc.stdout}")


def convert_mesh_to_png(input_path: str, output_path: str, resolution: int = 1024) -> str:
    """
    Convert mesh file to PNG preview image.
    Returns the output file path.
    """
    src = os.path.abspath(input_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"Input not found: {src}")
    
    # Validate file extension
    supported_exts = ['.glb', '.gltf', '.obj', '.stl', '.ply', '.fbx', '.3ds']
    ext = os.path.splitext(src)[1].lower()
    if ext not in supported_exts:
        raise ValueError(f"Unsupported file format: {ext}. Supported: {', '.join(supported_exts)}")
    
    out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    
    if _is_running_in_blender():
        _run_under_blender(src, out, resolution)
    else:
        _spawn_blender_this_script(src, out, resolution)
    
    if not os.path.exists(out):
        raise RuntimeError(f"Failed to create output file: {out}")
    
    return out


def _parse_args(argv):
    p = argparse.ArgumentParser(
        description="Convert mesh files to PNG preview images via Blender"
    )
    p.add_argument("--item_id", required=True, help="Item ID of mesh file")
    p.add_argument("--input", help="Input file path (used internally by Blender subprocess)")
    p.add_argument("--output", help="Output file path (used internally by Blender subprocess)")
    p.add_argument(
        "--resolution",
        type=int,
        default=1024,
        help="Output image resolution (square, default: 1024)"
    )
    p.add_argument("--blender-mode", default="0", help=argparse.SUPPRESS)
    return p.parse_args(argv)


def main():
    args = _parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:])
    
    # If running in Blender subprocess mode, just do the conversion
    if args.blender_mode == "1" and args.input and args.output:
        _run_under_blender(args.input, args.output, args.resolution)
        return
    
    # Main mode: handle Dataloop item
    main_item = dl.items.get(item_id=args.item_id)
    input_path = main_item.download(save_locally=True)
    
    # Generate unique output path
    output_filename = Path(input_path).stem + '_preview.png'
    output_path = '/tmp/app/' + str(uuid.uuid4().hex) + '_' + output_filename
    
    if not _is_running_in_blender() and args.blender_mode != "1":
        # Spawn Blender subprocess
        _spawn_blender_this_script(os.path.abspath(input_path), output_path, args.resolution)
    else:
        # Direct conversion (shouldn't happen in normal usage)
        convert_mesh_to_png(input_path, output_path, args.resolution)
    
    # Upload preview to Dataloop
    # modality_item = main_item.project.datasets._get_binaries_dataset().items.upload(
    #     local_path=output_path, 
    #     remote_path='/dm_preview'
    # )
    
    # # Create a modality link for the main item
    # main_item.modalities.create(
    #     name='Preview',
    #     modality_type=dl.ModalityTypeEnum.PREVIEW,
    #     ref=modality_item.id
    # )
    
    # # Update the main item to apply changes
    # main_item.update()
    
    logger.info(f"Successfully created preview for mesh file: {main_item.name}")
    print(f"Preview created: {output_path}")


if __name__ == "__main__":
    main()
