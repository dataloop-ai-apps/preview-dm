import dtlpy as dl
import logging
import time
import subprocess

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

        try:
            # Run Blender command to convert USD to GLB
            blender_script_path = "./processing/create_preview/usd_to_gltf.py"
            
            cmd = f"blender -b -P {blender_script_path} -- --item_id {item_id} --format GLB"
            
            logger.info(f"Running Blender conversion command: {cmd}")
            
            # Live-stream process output with timeout
            start_time = time.time()
            output_lines = []
            with subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # merge stderr into stdout for ordered logs
                text=True,
                bufsize=1,
                universal_newlines=True
            ) as process:
                assert process.stdout is not None
                for line in process.stdout:
                    stripped_line = line.rstrip()
                    output_lines.append(stripped_line)
                    logger.info(stripped_line)
                    # Enforce 5-minute timeout
                    if time.time() - start_time > 300:
                        process.kill()
                        logger.error("Blender conversion timed out after 5 minutes")
                        raise RuntimeError("Blender conversion timed out")
                return_code = process.wait()

            if return_code != 0:
                logger.error(f"Blender conversion failed with return code {return_code}")
                if output_lines:
                    logger.error("Process output (combined):\n%s", "\n".join(output_lines))
                raise RuntimeError(f"Blender conversion failed with code {return_code}")

            logger.info("Blender conversion completed successfully")

        except Exception as e:
            logger.error(f"Error running Blender conversion: {str(e)}")
            raise

        return item