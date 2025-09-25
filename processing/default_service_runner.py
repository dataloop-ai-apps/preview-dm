import logging
import time
import subprocess
import os
import shlex
from typing import Sequence, Optional, Mapping

logger = logging.getLogger('service-runner')

def run_and_stream(
    command: Sequence[str] | str,
    timeout: int = 600,
    workdir: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    stream_logs: bool = True,
) -> int:
    """
    Execute a shell command (string) or argv (sequence) with streamed logs and timeout.
    Returns the process return code.
    """
    if isinstance(command, (list, tuple)):
        popen_args = {"args": list(command), "shell": False}
        display_cmd = " ".join(shlex.quote(str(p)) for p in command)
    else:
        popen_args = {"args": command, "shell": True}
        display_cmd = command

    logger.info(f"Executing command: {display_cmd}")

    start_time = time.time()
    output_lines: list[str] = []
    with subprocess.Popen(
        **popen_args,
        cwd=workdir,
        env={**os.environ, **(env or {})},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    ) as process:
        assert process.stdout is not None
        for line in process.stdout:
            stripped_line = line.rstrip()
            output_lines.append(stripped_line)
            if stream_logs:
                print(stripped_line)
            if time.time() - start_time > timeout:
                process.kill()
                logger.error(f"Command timed out after {timeout} seconds")
                raise RuntimeError("Command timed out")
        return_code = process.wait()

    if return_code != 0:
        if output_lines:
            logger.error("Process output (combined):\n%s", "\n".join(output_lines))
        logger.error(f"Command failed with return code {return_code}")
    else:
        logger.info("Command completed successfully")

    return return_code