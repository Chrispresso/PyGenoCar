from typing import Any, Tuple

# Constants
boxcar_constant = {
    ### Floor ###
    'floor_tile_height': (.15, float),
    'floor_tile_width': (1.5, float),
    'max_floor_tiles': (15, int),
    'floor_creation_type': ('ramp', str),
        ### Floor - Gaussian random. Used when 'floor_creation_type' == 'gaussian' ###
        # Only needed if using gaussian random floor creation
        'tile_angle_mu': (8, (int, float)),
        'tile_angle_std': (15, (int, float)),
        'tile_gaussian_denominator': ('tile_gaussian_threshold', float),
        'tile_gaussian_threshold': ('max_floor_tiles', int),

        ### Floor - ramp. Used when 'floor_creation_type' == 'ramp' ###
        # Only needed if using ramp floor creation
        # If 'ramp_constant_angle' is defined, it will use the constant ramp
        'ramp_constant_angle': (None, (float, type(None))),
        'ramp_constant_distance': (None, (float, type(None))),
        
        # If 'ramp_constant_angle' is not defined, it will use an increasing ramp
        'ramp_increasing_angle': (1.2, (float, type(None))),
        'ramp_start_angle': (1, (float, type(None))),
        'ramp_increasing_type': ('multiply', (str, type(None))),

        'ramp_max_angle': (45, float),
        'ramp_approach_distance': (10, float),
        'ramp_distance_needed_to_jump': (5, float),

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
    'gravity': ((0, -9.8), tuple),  # X/Y direction

    # Genetic Algorithm
    'num_cars_in_generation': (1, int)

}

def _verify_constants() -> None:
    failed = []
    for constant in boxcar_constant:
        try:
            get_boxcar_constant(constant)
        except:
            failed.append(constant)
        
    if failed:
        failed_constants = '\n'.join(fail for fail in failed)
        raise Exception('The following constants have invalid values for their types:\n{}'.format(failed_constants))

def get_boxcar_constant(constant: str) -> Any:
    """
    Get the end value represented by the constant you are searching for
    """
    value, requested_type = boxcar_constant[constant]

    while value in boxcar_constant:
        value, _ = boxcar_constant[value]

    # Are there multiple options of what the value can be?
    if isinstance(requested_type, tuple):
        # If the value is None and we allow None as an option, that is okay
        if value is None and type(None) in requested_type:
            pass
        # If the value is None and we don't allow that as an option, raise an exception
        elif value is None and type(None) not in requested_type:
            raise Exception('constant "{}" contains value: None, which is of type NoneType. Expected type: {}'.format(
                constant, requested_type
            ))
        # If value is not None and float is an option, use that. Float will take priority over int as well then
        elif value and float in requested_type:
            value = float(value)
    elif value and requested_type is float:
        value = float(value)
    
    return value