#!/usr/bin/env python3
"""
VLA Web Client entry point.

Usage:
    python run_web_client.py [--host 0.0.0.0] [--port 9000]

Then open http://localhost:9000 in your browser.

Port layout:
    9000  — This web server (REST API + WebSocket /ws)
    8080  — visual/ HTTP static server  (started by VLAClient.run())
    8765  — visual/ WebSocket data push (started by VLAClient.run())
"""

import argparse
import os
import signal
import subprocess
import sys
import cv2
import uvicorn
from conf.logging_conf import setup_logging
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
sys.setswitchinterval(0.001)
cv2.setNumThreads(1)
# os.environ.setdefault('MKL_NUM_THREADS', '1')
# os.environ.setdefault('OMP_NUM_THREADS', '1')


def parse_args():
    p = argparse.ArgumentParser(description="VLA Web Client")
    p.add_argument('--host', default='0.0.0.0', help='Bind host')
    p.add_argument('--port', type=int, default=9000, help='Bind port')
    p.add_argument('--conf', type=str, default='default_conf.yaml', help='Configuration file name used to load and save config parameters in /conf directory')
    p.add_argument('--reload', action='store_true', help='Enable hot reload (dev only)')
    return p.parse_args()

def kill_port(port):
    """Kill processes occupying the Web port, if any."""
    try:
        result = subprocess.run(
            ['lsof', '-t', f'-i:{port}'],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return
    for value in result.stdout.split():
        if value.isdigit() and int(value) != os.getpid():
            os.kill(int(value), signal.SIGKILL)

def main():
    args = parse_args()
    kill_port(port=args.port)

    exit_code = 0
    logger = None
    try:
        logger = setup_logging("client.log", "run_web_client")
        os.environ['conf_file'] = args.conf
        uvicorn.run(
            "web_client.server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
    except KeyboardInterrupt:
        exit_code = 0
    except Exception as e:
        if logger is not None:
            logger.exception(f"Exception: {e}")
        else:
            print(f"Exception: {e}")
        exit_code = 1
        raise
    finally:
        # Some native robot SDK resources may segfault during CPython finalization.
        # After uvicorn shutdown completes, force immediate process exit to avoid it.
        if not args.reload:
            try:
                sys.stdout.flush()
                sys.stderr.flush()
            except Exception:
                pass
            os._exit(exit_code)

        return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
