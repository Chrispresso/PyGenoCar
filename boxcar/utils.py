from typing import Any, Tuple

# Constants
boxcar_constant = {
    ### Floor ###
    'floor_tile_height': (.03, float),
    'floor_tile_width': (.3, float),
    'max_floor_tiles': (300, int),
    'floor_creation_type': ('gaussian', str),
        ### Floor - Gaussian random. Used when 'floor_creation_type' == 'gaussian' ###
        # Only needed if using gaussian random floor creation
        'tile_angle_mu': (8, (int, float)),
        'tile_angle_std': (15, (int, float)),
        'tile_gaussian_denominator': ('tile_gaussian_threshold', (int, float)),
        'tile_gaussian_threshold': ('max_floor_tiles', int),

        ### Floor - ramp. Used when 'floor_creation_type' == 'ramp' ###
        # Only needed if using ramp floor creation
        # If 'ramp_constant_angle' is defined, it will use the constant ramp
        'ramp_constant_angle': (10, (float, type(None))),
        'ramp_constant_distance': (20, (float, type(None))),
        
        # If 'ramp_constant_angle' is not defined, it will use an increasing ramp
        'ramp_increasing_angle': (1.2, (float, type(None))),
        'ramp_start_angle': (1, (float, type(None))),
        'ramp_increasing_type': ('multiply', (str, type(None))),

        'ramp_max_angle': (10, float),
        'ramp_approach_distance': (10, float),
        'ramp_distance_needed_to_jump': (.2, float),

        ### Jagged - ramp. Used when 'floor_creation_type' == 'jagged' ###
        # Only needed if using jaged floor creation
        'jagged_increasing_angle': (45, float),
        'jagged_decreasing_angle': (45, float),

    # Car
    'car_max_tries': (120, int),

    # Chassis
    'min_chassis_axis': (0.1, float),
    'max_chassis_axis': (1.3, float),
    'min_chassis_density': (30.0, float),
    'max_chassis_density': (300.0, float),

    # Wheel
    'min_wheel_density': (40.0, float),
    'max_wheel_density': (200.0, float),
    'min_num_wheels': (0, int),
    'max_num_wheels': (8, int),
    'min_wheel_radius': (0.1, float),
    'max_wheel_radius': (0.5, float),

    # World
    'gravity': ((0, -9.8), tuple)  # X/Y direction

}

def _get_value_and_requested_type(value: Any, requested_type: Any) -> Tuple[Any, Any]:
    if isinstance(requested_type, tuple):
        if float in requested_type and not None in requested_type:
            value = float(value)
            requested_type = float
        elif str in requested_type and isinstance(value, str):
            value = value
            requested_type = str
        elif float in requested_type and isinstance(value, int):
            value = float(value)
            requested_type = float
    elif requested_type is float and isinstance(value, int):
        value = requested_type(value)
        requested_type = float

    return value, requested_type

def get_boxcar_constant(constant: str) -> Any:
    """
    Get the end value represented by the constant you are searching for
    """
    try:
        value, requested_type = boxcar_constant[constant]
        value, requested_type = _get_value_and_requested_type(value, requested_type)

        while not isinstance(value, requested_type):
            value, requested_type = boxcar_constant[value]
            value, requested_type = _get_value_and_requested_type(value, requested_type)

        value = requested_type(value)

    except:
        value = None
    
    return value