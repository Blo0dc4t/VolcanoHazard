import random
import math


class Volcano:


    def __init__(

        self,

        initial_pressure=0.25,

        initial_fracture=0.0,


        #
        # Simulation speed
        #

        time_scale=1,


        #
        # Pressure
        #

        recharge_min=0.004,

        recharge_max=0.008,

        pressure_loss_max=0.008,


        #
        # Earthquakes
        #

        earthquake_multiplier=50,


        #
        # Fracture
        #

        fracture_damage_min=0.01,

        fracture_damage_max=0.04,

        fracture_healing=0.94,


        #
        # Eruption
        #

        eruption_pressure_threshold=0.8,

        fracture_pressure_effect=0.4,

        minimum_pressure=0.35,


        #
        # Location
        #

        caldera_position=(50,50),

        earthquake_radius=20,

        earthquake_clustering=3,

        eruption_vent_probability=0.05


    ):


        # =================================================
        # STATE
        # =================================================


        self.pressure = initial_pressure

        self.fracture = initial_fracture


        self.erupted = False

        self.eruption_type = None



        # =================================================
        # PARAMETERS
        # =================================================


        self.time_scale = time_scale


        #
        # Pressure
        #

        self.recharge_min = recharge_min

        self.recharge_max = recharge_max

        self.pressure_loss_max = pressure_loss_max



        #
        # Earthquakes
        #

        self.earthquake_multiplier = earthquake_multiplier



        #
        # Fracture
        #

        self.fracture_damage_min = fracture_damage_min

        self.fracture_damage_max = fracture_damage_max

        self.fracture_healing = fracture_healing



        #
        # Eruption
        #

        self.eruption_pressure_threshold = eruption_pressure_threshold

        self.fracture_pressure_effect = fracture_pressure_effect

        self.minimum_pressure = minimum_pressure



        #
        # Location
        #

        self.caldera_position = caldera_position

        self.earthquake_radius = earthquake_radius

        self.earthquake_clustering = earthquake_clustering

        self.eruption_vent_probability = eruption_vent_probability



        # =================================================
        # ERUPTION OUTPUT
        # =================================================


        self.lava_radius = 0

        self.ash_radius = 0

        self.lava_intensity = 0

        self.ash_intensity = 0


        self.eruption_location = None



    # =====================================================
    # PRESSURE UPDATE
    # =====================================================


    def update_pressure(self):


        recharge = random.uniform(

            self.recharge_min,

            self.recharge_max

        )


        loss = random.uniform(

            0,

            self.pressure_loss_max

        )


        self.pressure += (

            recharge - loss

        ) * self.time_scale



        self.pressure = max(

            0,

            min(

                self.pressure,

                1

            )

        )



    # =====================================================
    # EARTHQUAKE GENERATION
    # =====================================================


    def generate_earthquakes(self):


        rate = (

            self.pressure ** 3

        ) * self.earthquake_multiplier



        number = int(

            random.gauss(

                rate,

                math.sqrt(

                    max(rate,1)

                )

            )

        )


        number = max(

            0,

            number

        )


        earthquakes = []



        for i in range(number):


            magnitude = self.generate_magnitude()


            location = self.generate_earthquake_location()



            earthquakes.append(

                {

                    "magnitude": magnitude,

                    "x": location[0],

                    "y": location[1]

                }

            )


        return earthquakes



    # =====================================================
    # EARTHQUAKE LOCATION
    # =====================================================


    def generate_earthquake_location(self):


        x0, y0 = self.caldera_position



        #
        # Cluster earthquakes around caldera
        #
        # Higher exponent = tighter clustering
        #

        distance = (

            random.random()

            **

            self.earthquake_clustering

        ) * self.earthquake_radius



        angle = random.uniform(

            0,

            math.pi * 2

        )



        x = x0 + math.cos(angle) * distance

        y = y0 + math.sin(angle) * distance



        return (

            round(x),

            round(y)

        )



    # =====================================================
    # GUTENBERG-RICHTER MAGNITUDE
    # =====================================================


    def generate_magnitude(self):


        b = 1.0

        m_min = 1.0


        r = random.random()


        magnitude = (

            m_min

            -

            math.log10(r)

            /

            b

        )


        magnitude = min(

            magnitude,

            6

        )


        return round(

            magnitude,

            2

        )

        # =====================================================
    # FRACTURE UPDATE
    # =====================================================


    def update_fracture(

        self,

        earthquakes

    ):


        for earthquake in earthquakes:


            magnitude = earthquake["magnitude"]


            #
            # Earthquake damage
            #
            # Fracture is 0-1 so divide by 100
            #

            damage = (

                10 ** magnitude

            ) * random.uniform(

                self.fracture_damage_min,

                self.fracture_damage_max

            ) / 100



            self.fracture += damage



        #
        # Slow healing
        #

        self.fracture *= self.fracture_healing



        self.fracture = max(

            0,

            min(

                self.fracture,

                1

            )

        )



    # =====================================================
    # ERUPTION CHECK
    # =====================================================


    def check_eruption(self):


        #
        # Fractures lower required pressure
        #

        threshold = (

            self.eruption_pressure_threshold

            -

            self.fracture_pressure_effect

            *

            self.fracture

        )


        threshold = max(

            threshold,

            self.minimum_pressure

        )



        #
        # Cannot erupt below threshold
        #

        if self.pressure < threshold:


            return False



        #
        # Increasing probability above threshold
        #

        probability = (

            self.pressure - threshold

        ) / (

            1 - threshold

        )



        probability = max(

            0,

            min(

                probability,

                1

            )

        )



        if random.random() < probability:


            self.erupted = True


            self.eruption_type = self.choose_eruption_type()


            self.set_eruption_location()


            self.set_eruption_properties()


            return True



        return False



    # =====================================================
    # ERUPTION TYPE
    # =====================================================


    def choose_eruption_type(self):


        #
        # High pressure + closed system
        #

        if (

            self.pressure > 0.85

            and

            self.fracture < 0.3

        ):


            return "explosive"



        #
        # Open fracture system
        #

        elif self.fracture > 0.7:


            return "lava_flow"



        else:


            return "mixed"



    # =====================================================
    # ERUPTION LOCATION
    # =====================================================


    def set_eruption_location(self):


        #
        # Most eruptions occur at caldera
        #

        if random.random() > self.eruption_vent_probability:


            self.eruption_location = self.caldera_position

            return



        #
        # Rare flank vent
        #

        x0, y0 = self.caldera_position



        distance = random.uniform(

            1,

            5

        )


        angle = random.uniform(

            0,

            math.pi * 2

        )



        x = x0 + math.cos(angle) * distance

        y = y0 + math.sin(angle) * distance



        self.eruption_location = (

            round(x),

            round(y)

        )



    # =====================================================
    # ERUPTION SIZE
    # =====================================================


    def set_eruption_properties(self):


        variation = random.uniform(

            0.7,

            1.3

        )


        #
        # Lava spread
        #
        # More fracture = easier lava movement
        #

        self.lava_radius = int(

            (

                5

                +

                self.pressure * 30

                +

                self.fracture * 30

            )

            *

            variation

        )



        #
        # Ash spread
        #
        # More pressure = explosive ash
        #

        self.ash_radius = int(

            (

                10

                +

                self.pressure * 80

            )

            *

            variation

        )



        self.lava_intensity = int(

            (

                20

                +

                self.pressure * 100

                +

                self.fracture * 50

            )

            *

            variation

        )



        self.ash_intensity = int(

            (

                20

                +

                self.pressure * 150

            )

            *

            variation

        )



    # =====================================================
    # RESET AFTER ERUPTION
    # =====================================================


    def release_pressure(self):


        #
        # Magma chamber partially empties
        #

        self.pressure *= random.uniform(

            0.1,

            0.4

        )



        #
        # Some fractures remain
        #

        self.fracture *= random.uniform(

            0.2,

            0.5

        )



        self.erupted = False

        self.eruption_type = None


        self.eruption_location = None



        self.lava_radius = 0

        self.ash_radius = 0

        self.lava_intensity = 0

        self.ash_intensity = 0








# =====================================================
# SIMULATION
# =====================================================


volcano = Volcano()



pressure_history = []

fracture_history = []

eruption_days = []


#
# Store spatial events
#

earthquake_history = []

eruption_locations = []



for day in range(1,366):


    #
    # Update volcano state
    #

    volcano.update_pressure()



    earthquakes = volcano.generate_earthquakes()



    volcano.update_fracture(

        earthquakes

    )



    #
    # Store earthquakes
    #

    earthquake_history.extend(

        earthquakes

    )



    eruption = volcano.check_eruption()



    #
    # Store histories
    #

    pressure_history.append(

        volcano.pressure

    )


    fracture_history.append(

        volcano.fracture

    )



    #
    # Daily summary
    #

    print(

        f"""
Day: {day}

Pressure:
{volcano.pressure*100:.1f}%

Earthquakes:
{len(earthquakes)}

Largest magnitude:
{max(
    [q["magnitude"] for q in earthquakes],
    default=0
):.2f}

Fracture:
{volcano.fracture*100:.1f}%

"""

    )



    #
    # Print earthquake locations
    #

    for quake in earthquakes:


        if quake["magnitude"] > 4:


            print(

                "Large earthquake:",
                
                quake["magnitude"],

                "Location:",

                (

                    quake["x"],

                    quake["y"]

                )

            )



    #
    # Eruption
    #

    if eruption:


        eruption_days.append(

            day

        )


        eruption_locations.append(

            volcano.eruption_location

        )



        print(

            "================="

        )


        print(

            "ERUPTION!"

        )


        print(

            "Type:",

            volcano.eruption_type

        )


        print(

            "Location:",

            volcano.eruption_location

        )


        print(

            "Lava radius:",

            volcano.lava_radius

        )


        print(

            "Ash radius:",

            volcano.ash_radius

        )


        print(

            "================="

        )



        volcano.release_pressure()


import matplotlib.pyplot as plt



plt.figure(

    figsize=(8,8)

)



#
# Earthquakes
#

x = [

    q["x"]

    for q in earthquake_history

]


y = [

    q["y"]

    for q in earthquake_history

]


m = [

    q["magnitude"]

    for q in earthquake_history

]



plt.scatter(

    x,

    y,

    s=[

        mag**3

        for mag in m

    ],

    alpha=0.5,

    label="Earthquakes"

)



#
# Caldera
#

cx,cy = volcano.caldera_position


plt.scatter(

    cx,

    cy,

    marker="*",

    s=300,

    label="Caldera"

)



#
# Eruptions
#

if len(eruption_locations)>0:


    ex = [

        p[0]

        for p in eruption_locations

    ]


    ey = [

        p[1]

        for p in eruption_locations

    ]


    plt.scatter(

        ex,

        ey,

        marker="X",

        s=200,

        label="Eruptions"

    )



plt.xlabel(

    "X position"

)


plt.ylabel(

    "Y position"

)


plt.title(

    "Volcano Seismicity"

)


plt.legend()


plt.axis(

    "equal"

)


plt.grid()


plt.show()