from typing import Union

# Constants
boxcar_constant = {
    ### Floor ###
    'floor_tile_height': (.15, float)
    'floor_tile_width': (1.5, float)
    'max_floor_tiles': 300,
    'floor_creation_type': 'gaussian',
        ### Floor - Gaussian random ###
        # Only needed if using gaussian random floor creation
        'tile_angle_mu': 8,
        'tile_angle_std': 15,
        'tile_gaussian_denominator': 'tile_gaussian_denominator',
        'tile_gaussian_threshold': 'max_floor_tiles',

    # Chassis
    'min_chassis_axis': 0.1,
    'max_chassis_axis': 1.3,
    'min_chassis_density': 30.0,
    'max_chassis_density': 300.0,

    # Wheel
    'min_wheel_density': 40.0,
    'max_wheel_density': 200.0,
    'min_num_wheels': 0,
    'max_num_wheels': 8,
    'min_wheel_radius': 0.1,
    'max_wheel_radius': 0.5,

    # World
    'gravity': (0, -9.8)  # X/Y direction

}

def get_boxcar_constant(constant: str) -> Union[int, float]:
    """
    Get the end value represented by the constant you are searching for
    """
    try:
        value = boxcar_constant[constant]
        while not isinstance(value, (float, int, type(None))):
            value = boxcar_constant[value]
    except:
        value = None
    
    return value