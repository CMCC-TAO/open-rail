#!/usr/bin/env python3
"""
Test script for adaptive layout functionality.
This script demonstrates how the VLA client layout adapts to different terminal sizes.
"""
import os
import sys
sys.path.append(f'{os.path.dirname(__file__)}/..')
print(sys.path)

import time
from rich.console import Console
from rich.live import Live
from client.utils.util import create_layout

def test_adaptive_layout():
    """Test the adaptive layout with sample data."""
    console = Console()
    
    # Sample data for testing
    test_info = {
        'infer_count': 1234,
        'avg_infer_time': 0.0456,
        'avg_traj_time': 0.0123,
        'debug_info': 'Testing adaptive layout functionality. This is a longer debug message to test text wrapping and display in different terminal sizes.',
        'robot_current_action': [0.123, -0.456, 0.789, -0.012, 0.345, -0.678, 0.901, 0.234, -0.567, 0.890, -0.123, 0.456, -0.789, 0.012, 0.5, 0.8],
        'robot_current_state': [0.987, -0.654, 0.321, -0.098, 0.765, -0.432, 0.109, 0.876, -0.543, 0.210, -0.987, 0.654, -0.321, 0.098, 0.3, 0.7],
        'config_info': {
            'record': True,
            'fps': 30,
            'sleep_time': 0.1,
            'model_name': 'test_model',
            'chunk_size': 64
        },
        'ctrl_info': {
            'language': 'pick up the bottle and place it in the box',
            'is_running_action': True,
        },
        'obs_act_info': {
            'preprocess': 'resize',
            'obs_shape': '(3, 224, 224)',
            'action_dim': 16,
            'chunk_size': 64
        },
        'cmd_key': 'Press Enter for commands'
    }
    
    print(f"Current terminal size: {console.size.width}x{console.size.height}")
    print("Testing adaptive layout...")
    print("Press Ctrl+C to exit")
    
    try:
        with Live(create_layout(test_info, console.size), refresh_per_second=2) as live:
            while True:
                # Update with current terminal size
                terminal_size = console.size
                live.update(create_layout(test_info, terminal_size))
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nTest completed.")

if __name__ == "__main__":
    test_adaptive_layout()