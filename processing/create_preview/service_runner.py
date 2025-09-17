from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import dtlpy as dl
import numpy as np
import logging
import shutil
import time
import cv2
import os
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
            blender_script_path = "/tmp/app/processing/create_preview/usd_to_gltf.py"
            
            cmd = f"blender -b -P {blender_script_path} -- --item_id {item_id} --format GLB"
            
            logger.info(f"Running Blender conversion command: {cmd}")
            
            # Run the command and wait for completion
            result = subprocess.run(
                cmd,
                shell=True,  # Required when using string command
                capture_output=True,
                text=True,
                timeout=300,  # 5 minu te timeout
                check=False
            )

            print('success')
            print(result.stdout)
            print(result.stderr)
            print(result.returncode)
            print('koniec')

            
            if result.returncode != 0:
                logger.error(f"Blender conversion failed with return code {result.returncode}")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                raise RuntimeError(f"Blender conversion failed: {result.stderr}")
            
            logger.info("Blender conversion completed successfully")
            logger.info(f"STDOUT: {result.stdout}")
            
        except subprocess.TimeoutExpired:
            logger.error("Blender conversion timed out after 5 minutes")
            raise RuntimeError("Blender conversion timed out")
        except Exception as e:
            logger.error(f"Error running Blender conversion: {str(e)}")
            raise

        return item