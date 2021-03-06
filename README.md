# PyGenoCar - V1.0
Welcome to PyGenoCar - The world in which cars are made using Genetic Algorithms!<br>
Feel free to mess around with the settings and see how the cars change over the generations!<br>
This contains information on the following:<br>
<ul>
<li>Installation</li>
<li>Command Line Arguments</li>
<li>Controls</li>
<li>Settings</li>
</ul>

# Installation
This requires Python3.6+<br><br>
The installation here might seem like a lot of work, but I promise it isn't. I cannot include everything into a `requirements.txt` since `Box2D` is a bit more work than that.  If you want the installation instructions from the `box2d` repo, head over to https://github.com/jonasschneider/box2d-py/blob/master/INSTALL.md. Otherwise just read below for what I did:<br>
## Windows:
1. `git clone https://github.com/pybox2d/pybox2d` (optional: ` -b 2.3.2`)
2. Download SWIG. Easiest way is to use prebuilt executables from: https://sourceforge.net/projects/swig/files/swigwin/swigwin-4.0.1/swigwin-4.0.1.zip/download?use_mirror=cfhcable.
3. Unzip and add `swigwin-4.0.1` to your `System Variables PATH` (environment variable).
4. `cd /path/to/pybox2d/clone/location`
5. `python setup.py build`
6. `python setup.py install`
## Linux
1. `sudo apt-get install swig`
2. `git clone https://github.com/pybox2d/pybox2d` (optional: ` -b 2.3.2`)
3. `cd /path/to/pybox2d/clone/location`
4. `python setup.py build`
5. `sudo python setup.py install`

To test open a new Python terminal:<br>
1. `import Box2D`
2. `Box2D.__version__`

If everything goes right, you should see a version printed.<br>
You can now run `pip3 install -r requirements.txt` to finish installing the below requirements:
1. numpy
2. pyqt5
3. dill

# Command Line Arguments
Most of the stuff you are going to want to change is done in settings. The reason for this is there are just so many parameters, and having everything be modifiable through the command line would be overwhelming. There are however some things you may want to use the command line for:<br>

`-h`: Basic help message.<br>
`--save-best <location>`: You can specify a `/path/to/save` the best car from each generation to. Make sure that folder is empty or at least does not contain previous generation cars, otherwise they are at risk of being overwritten and the program won't allow that.<br>
`--save-pop <location>`: If you want, you can specify a `/path/to/save` the entire population after each generation. Not really advised, but if you want to, it's here.<br>
`--save-pop-on-close <location>`: `/path/to/save` the population when the program exits.<br>
`--replay-from-folder <location>`: Can be used to replay individuals from a folder you saved to. Currently only supports playing one car at a time. Useful for seeing how best individuals are changing over the generations.

# Controls<br>
It might seem weird to have controls for a Genetic Algorithm, but the controls are for being able to move the camera around to get a better idea of the environment. Below are the current supported controls and their functions:<br>
<ul><i><b>Z</b></i>: Zoom camera out</ul>
<ul><i><b>C</b></i>: Zoom camera in</ul>
<ul><i><b>W, A, S, D</b></i>: Pan camera up, left, down and right, respectively</ul> 
<ul><i><b>R</b></i>: [R]eset to normal control, i.e. follow the leading car</ul>
<ul><i><b>E</b></i>: Goes back to default zoom (scal[e]). E is next to R....</ul> 

# Settings
This is broken up into two subsections: boxcar and ga. Boxcar consists of all settings that are used in the creation of cars, the world, and anything related to physics. Genetic Algorithm (ga) consists of all settings used in the overall control for the GA.

It is important to note that units are in MKS (meters, kilograms, seconds). If you change parameters, keep that in mind. Also keep in mind that Box2D, the physics engine used here, is meant for smaller objects. If you create a wheel that has a 50m radius, it might work, but it might not model the best.
## Boxcar settings<br>
<u>Floor params</u>
<br>
<i><b>floor_tile_height</b></i> [float]: The height that each floor tile in the world will be created with.<br>
<i><b>floor_tile_width</b></i> [float]: The width that each floor tile in the world will be created with.<br>
<i><b>max_floor_tiles</b></i> [int]: Maximum number of floor tiles that will be created in the world.<br>
<i><b>gaussian_floor_seed</b></i> [int]: If you choose to create a gaussian floor, this seed will be used for the random number generator.<br>
<i><b>floor_creation_type</b></i> [str]: Determines what type of floor will be generated for cars to compete on. Options are: `gaussian`, `ramp` and `jagged`
<ul>
<u>gaussian</u><br>
Gaussian creation creates a very random track. There are modifiers to help the track be easier in the beginning and potentially harder at the end. Elevation gain and loss are both possible. Below are settings you can modify if <i><b>floor_creation_type</b></i> == `gaussian`:<br>
<i><b>tile_angle_mu</b></i> [float]: When a random gaussian floor tile is created, it is created with a gaussian random angle centered around this value.<br>
<i><b>tile_angle_std</b></i> [float]: When a random gaussian floor tile is created, it is created with a gaussian random angle with standard deviation of this value.<br>
<br>
Please see equation and explanation at the bottom of the page for what these two parameters control<br>
<i><b>tile_gaussian_denominator</b></i> [float]: Used for calculating a scale between [0,1] to multiply the angle by.<br>
<i><b>tile_gaussian_threshold</b></i> [float]: Used for calculating a scale between [0,1] to multiple the angle by.<br>

<br>
<u>ramp</u><br>
Ramp creation creates a specified ramp and a jump distance that the cars will need to clear. The approach and landing zone are flat in order to prioritize learning of the ramp. Below are settings you can modify if <i><b>floor_creation_type</b></i> == `ramp`:<br>
<i><b>ramp_constant_angle</b></i>: [float/None]: If this value is defined, the ramp will go up at a constant angle.<br>
<br>
<i><b>ramp_constant_distance</b></i>: [float]: Only used if <i><b>ramp_constant_angle</b></i> is defined. Determines the length of the ramp.<br>
<i><b>ramp_increasing_angle</b></i>: [float]: If <i><b>ramp_constant_angle</b></i> is None this will be used. Will create a ramp at an increasing angle of this value.<br>
<i><b>ramp_start_angle</b></i>: [float]: Angle to start the ramp at.<br>
<i><b>ramp_increasing_type</b></i>: [str]: Options consist of `multiply` and `add` for now. The equation for the increasing ramp angle is: ramp_start_angle OPERATOR ramp_increasing_angle. Example:<br>
`ramp_start_angle = 1.0` and `ramp_increasing_angle=2.0`. The angles for the first 5 tiles of the ramp would be: `1, 2, 4, 8, 16`.<br>
<i><b>ramp_max_angle</b></i>: [float] Maximum angle to make a tile before ending the ramp creation.<br>
<br>
<i><b>ramp_approach_distance</b></i> [float]: Flat distance used as a runway before starting the ramp.
<i><b>ramp_distance_needed_to_jump</b></i> [float]: Distance needed to jump before there is a landing zone. Distance is measured from the end ramp location to beginning of landing zone.<br>

<br>
<u>jagged</u><br>
Jagged creation creates a jagged road for the cars to travel over. There is no elevation gain and nothing to jump here. It is simply a jagged course and simulates rough terrain. Below are settings you can modify if <i><b>floor_creation_type</b></i> == `jagged`:<br>
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

## Genetic Algorithm Settings<br>
<u>Selection params</u>
<br>
<i><b>num_parents</b></i> [int]: Number of parents to select from the population for reproduction. This is also the default number of individuals spawned into the world. Will only reduce the size of the population if using <i><b>selection_type</b></i> `plus`.<br>
<i><b>num_offspring</b></i> [int]: Number of offspring to create from the parents. Only used if <i><b>selection_type</b></i> `plus` is selected. Otherwise there will always be <i><b>num_parents</b></i>.<br>
<i><b>selection_type</b></i> [str]: Options are `plus` and `comma`.<br>
If `plus` is used, then the number of offspring in the next generation will be <i><b>num_parents</b></i> + <i><b>num_offspring</b></i>.<br>
If `comma` is used, then the number of offspring in the next generation will be <i><b>num_parents</b></i>.<br>
<i><b>lifespan</b></i> [int/np.inf]: The lifespan of an individual when it is created. Each generation that an individual survies, the lifespan of that individual decreases. Once the lifespan hits 0 the individual will not be selected to go onto the next generation, even if it is a top performer. This can help with exploration of the search space.<br>
<br>
<u>Mutation params</u>
<br>
<i><b>probability_gaussian</b></i> [float]: When mutation occurs, this determines at what rate the mutation is gaussian.<br>
<i><b>gaussian_mutation_scale</b></i> [float]: If there is a gaussian mutation it is multiplied by this value. This can help reduce the mutation to smaller values.<br>
<i><b>probability_random_uniform</b></i> [float]: When mutation occurs, this determines at what rate the mutation is uniform.<br>
<i><b>mutation_rate</b></i> [float]: The probability that each given gene in the chromosome will mutate.<br>
<i><b>mutation_rate_type</b></i> [float]: Options are `static` and `decaying`. If `static`, then the <i><b>mutation_rate</b></i> is always the same, otherwise it decays as the generations increase.<br>
<br>
<u>Crossover params</u>
<br>
<i><b>probability_SBX</b></i> [float]: When crossover occurs, this determines at what rate the crossover is simulated binary crossover (SBX).<br>
<i><b>SBX_eta</b></i> [float]: eta is a control param for SBX. The smaller values create offspring further from the parents while larger values create offspring closer to the parents.<br>
<i><b>crossover_selection</b></i> [str]: Options are `tournament` and `roulette`. These options create either tournament or roulette wheel selection when deciding which parents to select for crossover.<br>
<br>
<u>Misc.</u>
<br>
<br>
<u>Fitness function</u>
<br>
The fitness function determines the overall fitness of an individual - calculated at the end of the generation. The great thing is you can change the fitness function directly from `settings.py` and choose what params to inclue and how to weight those params. Below are the params that will be passed to the fitness function:<br>
<ul>
<i><b>max_position</b></i> [float]: This is the maximum position in the x direction that an individual made it.<br>
<i><b>num_wheels</b></i> [int]: Number of wheels that the individual has.<br>
<i><b>total_chassis_volume</b></i> [float]: Total volume that makes up the chassis of the car.<br>
<i><b>total_wheels_volume</b></i> [float]: Total volume of all wheels on the car.<br>
<i><b>frames</b></i> [int]: Total frames the that individual stayed alive for.<br>
</ul>
<br>

## Random
<i><b>Gaussian threshold explained</i></b>:<br>
When creating gaussian random tiles, you may want the tiles to start off at an easier angle and progressively get more chaotic. Because of this I introduced two concepts that you can modify to tweak the rate at which tile angles become more chaotic.<br>
<br>
The equation is:<br>

    threshold = get_boxcar_constant('tile_gaussian_threshold')
    denominator = get_boxcar_constant('tile_gaussian_denominator')
    numerator = min(i, threshold)
    scale = min(numerator / denominator, 1.0)
    angle = random(mu, std) * scale
where `i` goes from `[0, num_tiles)`

So if `num_tiles = tile_gaussian_threshold = tile_gaussian_denominator` then `scale` won't be `1.0` until the very end. This just makes it so the potential of `random(mu, std)` is less until the end of the track. If you want just pure potential chaos, set both `tile_gaussian_threshold = tile_gaussian_denominator = 1`.
