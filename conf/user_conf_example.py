"""User Configuration Example

This file demonstrates how to create custom user configurations that can override
default client configurations. The configuration supports both flat and nested
parameter overrides.

Usage:
    python run_client.py --user_conf conf/user_conf_example.py

Configuration Priority (highest to lowest):
    1. Command line arguments (--fps, --sleep_time, etc.)
    2. User configuration file (--user_conf)
    3. Default client configuration (client_conf.py)
"""

def get_user_config():
    """
    Return a dictionary of configuration parameters to override defaults.
    
    This function demonstrates various configuration options including:
    - Simple parameter overrides
    - Nested configuration overrides (multi-level)
    - Language instruction customization
    
    Returns:
        dict: Configuration dictionary with parameters to override
    """
    return {
        # Simple parameter overrides
        'inter_chunk_mode': 'min_jerk',
        'language': [
            '[PLACE_CUP_ON_TABLE_RIGHT] [RIGHT_ARM] With the right arm, place the cup onto the table.',
            '[PLACE_CUP_ON_TABLE_LEFT] [LEFT_ARM] Using the left arm, place the cup onto the table.',
            '[POUR_BLACK_TEA] [RIGHT_ARM] With the right arm, pick up the black-tea pot and pour into the cup.',
            '[POUR_GREEN_TEA] [LEFT_ARM] Using the left arm, lift the green-tea pot and pour into the cup.',
            '[PLACE_BLACK_TEA_CUP] [RIGHT_ARM] The right arm places the black-tea cup onto the tray.',
            '[PLACE_GREEN_TEA_CUP] [LEFT_ARM] The left arm transfers the green-tea cup onto the tray.',
        ],
        
        # Nested configuration overrides - robots configuration
        'robots': {
            'a2d': {
                # 'hand_type': 'gripper',  # NOTE: unsupported the param
                'gripper_freq': 40,   # Override gripper frequency
                'reset_robot_pos': [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
            }
        },
    }
