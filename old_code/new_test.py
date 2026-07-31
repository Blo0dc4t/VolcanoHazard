import random
import math


class Volcano:


    def __init__(

        self,

        #
        # Pressure parameters
        #

        initial_pressure=0,

        recharge_min=0.5,

        recharge_max=1.5,

        pressure_loss_max=1,


        #
        # Earthquake parameters
        #

        earthquake_background=3,

        earthquake_multiplier=100,

        earthquake_exponent=3,


        #
        # Fracture parameters
        #

        fracture_damage_min=0.01,

        fracture_damage_max=0.5,

        fracture_healing=0.9,


        #
        # Eruption threshold parameters
        #

        base_eruption_pressure=90,

        fracture_pressure_reduction=0.5,

        minimum_eruption_pressure=40

    ):


        #
        # Current volcano state
        #

        self.pressure = initial_pressure

        self.fracture = 0.0


        self.erupted = False

        self.eruption_type = None



        #
        # Store pressure parameters
        #

        self.recharge_min = recharge_min

        self.recharge_max = recharge_max

        self.pressure_loss_max = pressure_loss_max



        #
        # Store earthquake parameters
        #

        self.earthquake_background = earthquake_background

        self.earthquake_multiplier = earthquake_multiplier

        self.earthquake_exponent = earthquake_exponent



        #
        # Store fracture parameters
        #

        self.fracture_damage_min = fracture_damage_min

        self.fracture_damage_max = fracture_damage_max

        self.fracture_healing = fracture_healing



        #
        # Store eruption parameters
        #

        self.base_eruption_pressure = base_eruption_pressure

        self.fracture_pressure_reduction = fracture_pressure_reduction

        self.minimum_eruption_pressure = minimum_eruption_pressure



        #
        # Eruption properties
        #

        self.lava_radius = 0

        self.ash_radius = 0

        self.lava_intensity = 0

        self.ash_intensity = 0



    # =================================================
    # PRESSURE EVOLUTION
    # =================================================

    def update_pressure(self):


        recharge = random.uniform(

            self.recharge_min,

            self.recharge_max

        )


        loss = random.uniform(

            0,

            self.pressure_loss_max

        )


        self.pressure += recharge

        self.pressure -= loss



        #
        # Keep within physical limits
        #

        self.pressure = max(

            0,

            min(

                self.pressure,

                120

            )

        )



    # =================================================
    # EARTHQUAKE GENERATION
    # =================================================

    def generate_earthquakes(self):


        #
        # More pressure = more earthquakes
        #

        rate = (

            self.earthquake_background

            +

            self.earthquake_multiplier

            *

            (

                self.pressure / 120

            )

            **

            self.earthquake_exponent

        )


        number = int(

            random.gauss(

                rate,

                math.sqrt(

                    max(

                        rate,

                        1

                    )

                )

            )

        )


        number = max(

            0,

            number

        )


        earthquakes = []


        for i in range(number):

            earthquakes.append(

                self.generate_magnitude()

            )


        return earthquakes



    # =================================================
    # GUTENBERG-RICHTER MAGNITUDES
    # =================================================

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



    # =================================================
    # FRACTURE EVOLUTION
    # =================================================

    def update_fracture(

        self,

        earthquakes

    ):


        for magnitude in earthquakes:


            damage = magnitude * random.uniform(

                self.fracture_damage_min,

                self.fracture_damage_max

            )


            self.fracture += damage



        #
        # Natural healing
        #

        self.fracture *= self.fracture_healing



        #
        # Keep on 0-100 scale
        #

        self.fracture = max(

            0,

            min(

                self.fracture,

                100

            )

        )



    # =================================================
    # ERUPTION CHECK
    # =================================================

    def check_eruption(self):


        #
        # Fracture lowers required pressure
        #

        eruption_threshold = max(

            self.minimum_eruption_pressure,

            self.base_eruption_pressure

            -

            self.fracture_pressure_reduction

            *

            self.fracture

        )



        if self.pressure < eruption_threshold:

            return False



        #
        # Probability increases above threshold
        #

        probability = (

            self.pressure

            -

            eruption_threshold

        ) / (

            120

            -

            eruption_threshold

        )


        #
        # Random natural variation
        #

        probability *= random.uniform(

            0.8,

            1.2

        )


        probability = max(

            0,

            min(

                probability,

                0.95

            )

        )



        if random.random() < probability:


            self.erupted = True

            self.eruption_type = self.choose_eruption_type()

            self.set_eruption_properties()


            return True



        return False



    # =================================================
    # ERUPTION TYPE
    # =================================================

    def choose_eruption_type(self):


        if (

            self.pressure > 85

            and

            self.fracture < 30

        ):

            return "explosive"


        elif self.fracture > 70:

            return "lava_flow"


        else:

            return "mixed"



    # =================================================
    # ERUPTION SIZE
    # =================================================

    def set_eruption_properties(self):


        pressure_factor = (

            self.pressure / 120

        )


        fracture_factor = (

            self.fracture / 100

        )



        variation = random.uniform(

            0.7,

            1.3

        )



        self.lava_radius = int(

            (

                5

                +

                40 * fracture_factor

                +

                20 * pressure_factor

            )

            *

            variation

        )



        self.ash_radius = int(

            (

                10

                +

                80 * pressure_factor

                +

                20 * (

                    1 - fracture_factor

                )

            )

            *

            variation

        )



        self.lava_intensity = int(

            (

                20

                +

                100 * fracture_factor

                +

                40 * pressure_factor

            )

            *

            variation

        )



        self.ash_intensity = int(

            (

                20

                +

                150 * pressure_factor

            )

            *

            variation

        )



    # =================================================
    # RESET AFTER ERUPTION
    # =================================================

    def release_pressure(self):


        self.pressure *= random.uniform(

            0.05,

            0.40

        )


        self.fracture *= random.uniform(

            0.20,

            0.50

        )


        self.erupted = False

        self.eruption_type = None


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


for day in range(1,366//2):


    #
    # Update volcano
    #

    volcano.update_pressure()


    earthquakes = volcano.generate_earthquakes()


    volcano.update_fracture(

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
    # Print daily summary
    #

    print(

        f"""
Day: {day}
Pressure: {volcano.pressure:.2f}
Earthquakes: {len(earthquakes)}
Largest magnitude: {max(earthquakes, default=0):.2f}
Fracture: {volcano.fracture:.2f}
"""

    )


    #
    # Eruption
    #

    if eruption:


        eruption_days.append(

            day

        )


        print(

            "ERUPTION!"

        )


        print(

            "Type:",

            volcano.eruption_type

        )


        print(

            "Lava radius:",

            volcano.lava_radius

        )


        print(

            "Ash radius:",

            volcano.ash_radius

        )


        volcano.release_pressure()


# =====================================================
# PLOTS
# =====================================================

import matplotlib.pyplot as plt


days = range(

    1,

    len(pressure_history) + 1

)


fig, axes = plt.subplots(

    2,

    1,

    figsize=(10,8),

    sharex=True

)


#
# Pressure
#

axes[0].plot(

    days,

    pressure_history,

    label="Pressure"

)


for eruption_day in eruption_days:

    axes[0].axvline(

        eruption_day,

        linestyle="--"

    )


axes[0].set_title(

    "Magma Pressure"

)

axes[0].set_ylabel(

    "Pressure"

)

axes[0].grid()


#
# Fracture
#

axes[1].plot(

    days,

    fracture_history,

    label="Fracture"

)


for eruption_day in eruption_days:

    axes[1].axvline(

        eruption_day,

        linestyle="--"

    )


axes[1].set_title(

    "Crustal Fracture"

)

axes[1].set_xlabel(

    "Day"

)

axes[1].set_ylabel(

    "Fracture"

)

axes[1].grid()


plt.tight_layout()

plt.show()
