from typing import Any

# Constants
boxcar_constant = {
    ### Floor ###
    'floor_tile_height': (.15, float),
    'floor_tile_width': (1.5, float),
    'max_floor_tiles': (300, int),
    'floor_creation_type': ('gaussian', str),
        ### Floor - Gaussian random ###
        # Only needed if using gaussian random floor creation
        'tile_angle_mu': (8, (int, float)),
        'tile_angle_std': (15, (int, float)),
        'tile_gaussian_denominator': ('tile_gaussian_threshold', (int, float)),
        'tile_gaussian_threshold': ('max_floor_tiles', int),

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

def get_boxcar_constant(constant: str) -> Any:
    """
    Get the end value represented by the constant you are searching for
    """
    try:
        value, t = boxcar_constant[constant]
        requested_type = t
        cast_type = None
        if isinstance(requested_type, tuple):
            if float in requested_type:
                cast_type = float

        while not isinstance(value, requested_type):
            value, requested_type = boxcar_constant[value]
            if isinstance(requested_type, tuple):
                if float in requested_type:
                    cast_type = float

        # If we have a type to cast to because there were multiple options, choose that type
        if cast_type:
            value = cast_type(value)
        else:
            value = requested_type(value)

    except:
        value = None
    
    return value