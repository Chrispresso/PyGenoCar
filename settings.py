from typing import Any, Tuple

# Settings that control everything.
settings = {}
settings['boxcar'] = {}
settings['ga'] = {}
__settings_cache = {} 
# The settings specific to the boxcar
settings['boxcar'] = {
    ### Floor ###
    'floor_tile_height': (.15, float),
    'floor_tile_width': (1.5, float),
    'max_floor_tiles': (150, int),
    'floor_creation_type': ('gaussian', str),
        ### Floor - Gaussian random. Used when 'floor_creation_type' == 'gaussian' ###
        # Only needed if using gaussian random floor creation
        'tile_angle_mu': (8, float),
        'tile_angle_std': (15, float),
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
    'num_cars_in_generation': (20, int),

    # Display
    'show': (True, bool), # Whether or not to display anything
    'fps': (60.0, float),
    'display_at_a_time': (20, int)
}

## Genetic algorithm specific settings
settings['ga'] = {
    # Selection
    'num_parents': (12, int),
    'num_offspring': (2, int),
    'selection_type': ('plus', str),

    # Mutation
    'probability_gaussian': (1.00, float),
    'gaussian_mutation_scale': (0.2, float),
    'probability_random_uniform': (0.00, float),
    'mutation_rate': (0.05, float),
    'mutation_rate_type': ('static', str),

    # Crossover
    'probability_SBX': (1.00, float),
    'SBX_eta': (5, float),

    # Misc.
    'should_clip': (bool, True),
    'clip_type': ('bounds', str)
}

def _verify_constants() -> None:
    failed = []

    for controller in settings:
        setting_map = settings[controller]
        for constant in setting_map:
            try:
                _get_constant(constant, controller)
            except:
                failed.append('{}: {}'.format(controller, constant))
        
    if failed:
        failed_constants = '\n'.join(fail for fail in failed)
        raise Exception('The following constants have invalid values for their types:\n{}'.format(failed_constants))

def _get_constant(constant: str, controller: str) -> Any:
    """
    Get the end value represented by the constant you are searching for
    """
    # Caches are good. Normally making a cache for a dictionary doesn't make sense.
    # Since I allow dependencies on other variables, a lookup could be O(N). By adding
    # a cache where (constant, controller) is the key, we get O(1) lookup time again.
    if (constant, controller) in __settings_cache:
        return __settings_cache[(constant, controller)]
    if controller not in settings:
        raise Exception('Unable to find a setting for {}'.format(controller))
    
    setting_map = settings[controller]
    value, requested_type = setting_map[constant]

    while value in setting_map:
        value, _ = setting_map[value]

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
    
    # Set cache if we made it this far
    __settings_cache[(constant, controller)] = value
    return value

def get_boxcar_constant(constant: str) -> Any:
    return _get_constant(constant, 'boxcar')

def get_ga_constant(constant: str) -> Any:
    return _get_constant(constant, 'ga')