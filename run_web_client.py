#!/usr/bin/env python3
"""
VLA Web Client entry point.

Usage:
    python run_web_client.py [--host 0.0.0.0] [--port 9000]

Then open http://localhost:9000 in your browser.

Port layout:
    9000  — This web server (REST API + WebSocket /ws)
    8080  — visual/ HTTP static server  (started by VLAClientAsync.run())
    8765  — visual/ WebSocket data push (started by VLAClientAsync.run())
"""

import argparse

import uvicorn


def parse_args():
    p = argparse.ArgumentParser(description="VLA Web Client")
    p.add_argument('--host', default='0.0.0.0', help='Bind host')
    p.add_argument('--port', type=int, default=9000, help='Bind port')
    p.add_argument('--reload', action='store_true', help='Enable hot reload (dev only)')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    uvicorn.run(
        "web_client.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )