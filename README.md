# PyGenoCar - V1.0

# Setings
This is broken up into two subsections: boxcar and ga. Boxcar consists of all settings that are used in the creation of cars, the world, and anything related to physics. Genetic Algorithm (ga) consists of all settings used in the overall control for the GA.

It is important to note that units are in MKS (meters, kilograms, seconds). If you change parameters, keep that in mind. Also keep in mind that Box2D, the physics engine used here, is meant for smaller objects. If you create a wheel that has a 50m radius, it might work, but it might not model the best.
## Boxcar settings<br>
<u>Floor params</u>
<br>
<i><b>floor_tile_height</b></i> [float]: The height that each floor tile in the world will be created with.<br>
<i><b>floor_tile_width</b></i> [float]: The width that each floor tile in the world will be created with.<br>
<i><b>max_floor_tiles</b></i> [int]: Maximum number of floor tiles that will be created in the world.<br>
<i><b>floor_creation_type</b></i> [str]: Determines what type of floor will be generated for cars to compete on. Options are: "gaussian", "ramp" and "jaged"
<ul>
<li>Gaussian creation creates a very random track. There are modifiers to help the track be easier in the beginning and potentially harder at the end. Elevation gain and loss are both possible. Below are settings you can modify if <i><b>floor_creation_type</b></i> == "gaussian":<br>
<i><b>tile_angle_mu</b></i> [float]: When a random gaussian floor tile is created, it is created with a gaussian random angle centered around this value.<br>
<i><b>tile_angle_std</b></i> [float]: When a random gaussian floor tile is created, it is created with a gaussian random angle with standard deviation of this value.<br>
<i><b>tile_gaussian_denominator</b></i> [float]: Used for calculating a scale between [0,1] to multiply the angle by. See equation @TODO: Link an equation?<br>
<i><b>tile_gaussian_threshold</b></i> [float]: Used for calculating a scale between [0,1] to multiple the angle by. See quation @TODO: Link an equation<br>
</li>
<br>

<li>Ramp creation creates a specified ramp and a jump distance that the cars will need to clear. The approach and landing zone are flat in order to prioritize learning of the ramp. Below are settings you can modify if <i><b>floor_creation_type</b></i> == "ramp":<br>
<i><b>ramp_constant_angle</b></i>: [float/None]: If this value is defined, the ramp will go up at a constant angle.<br>
<br>
<i><b>ramp_constant_distance</b></i>: [float]: Only used if <i><b>ramp_constant_angle</b></i> is defined. Determines the length of the ramp.<br>
<i><b>ramp_increasing_angle</b></i>: [float]: If <i><b>ramp_constant_angle</b></i> is None this will be used. Will create a ramp at an increasing angle of this value.<br>
<i><b>ramp_start_angle</b></i>: [float]: Angle to start the ramp at.<br>
<i><b>ramp_increasing_type</b></i>: [str]: Options consist of "multiply" and "add" for now. The equation for the increasing ramp angle is: ramp_start_angle OPERATOR ramp_increasing_angle. Example:<br>
ramp_start_angle = 1.0 and ramp_increasing_angle=2.0. The angles for the first 5 tiles of the ramp would be: 1, 2, 4, 8, 16.<br>
<i><b>ramp_max_angle</b></i>: [float] Maximum angle to make a tile before ending the ramp creation.<br>
<br>
<i><b>ramp_approach_distance</b></i> [float]: Flat distance used as a runway before starting the ramp.
<i><b>ramp_distance_needed_to_jump</b></i> [float]: Distance needed to jump before there is a landing zone. Distance is measured from the end ramp location to beginning of landing zone.
</li>
<br>

<li>Jagged creation creates a jagged road for the cars to travel over. There is no elevation gain and nothing to jump here. It is simply a jagged course and simulates rough terrain. Below are settings you can modify if <i><b>floor_creation_type</b></i> == "jagged":<br>
</li>
<i><b>jagged_increasing_angle</b></i> [float]: The amount the jagged edge will increase by.<br>
<i><b>jagged_decreasing_angle</b></i> [float]: The amount the jagged edge will decrease by. <br>
</li>
</ul>
<br>
<u>Car params</u>
<br>
<i><b>car_max_tries</b></i> [int]: Maximum number of tries a car can do without improving before it dies. One try per frame. An improvement is measured by reaching a farther max distance while moving faster than ~ 0.9mph (.4m/s)<br>
<br>
<u>Chassis params</u>
<br>
<i><b>min_chassis_axis</b></i> [float]: Minimum length that a chassis part can have.<br>
<i><b>max_chassis_axis</b></i> [float]: Maximum length that a chassis part can have.<br>
<i><b>min_chassis_density</b></i> [float]: Minimum density a chassis part can have.<br>
<i><b>max_chassis_density</b></i> [float]: Maximum density a chassis part can have.<br>
<br>
<u>Wheel params</u>
<br>
<i><b>min_wheel_density</b></i> [float]: Minimum density a wheel can have.<br>
<i><b>max_wheel_density</b></i> [float]: Maximum density a wheel can have.<br>
<i><b>min_num_wheels</b></i> [float]: Minimum number of wheels a car can have.<br>
<i><b>max_num_wheels</b></i> [float]: Maximum number of wheels a car can have.<br>
<i><b>min_wheel_radius</b></i> [float]: Minimum radius a wheel can have.<br>
<i><b>max_wheel_radius</b></i> [float]: Maximum radius a wheel can have.<br>
<br>
<u>World params</u>
<br>
<i><b>gravity</b></i> [float, float]: (x, y) amount of gravity to have in the world.<br>
<br>
<u>Display params</u>
<br>
<i><b>show</b></i> [bool]: Whether or not to have the graphics display.<br>
<i><b>fps</b></i> [float]: The FPS to run the simulation at. If you are using <i><b>show</b></i>, you are basically limited to your monitor refresh rate. Otherwise you can set this to a value between [0, 1000].<br>
<i><b></b></i>


