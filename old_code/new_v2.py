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

        minimum_pressure=0.35


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



        # =================================================
        # ERUPTION OUTPUT
        # =================================================


        self.lava_radius = 0

        self.ash_radius = 0

        self.lava_intensity = 0

        self.ash_intensity = 0



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


        #
        # Same relationship as original:
        #
        # high pressure = many earthquakes
        #

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


            earthquakes.append(

                self.generate_magnitude()

            )


        return earthquakes



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


        for magnitude in earthquakes:


            #
            # Same damage as before,
            # divided by 100 because fracture is 0-1
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
        # Fracture lowers pressure needed
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



        if self.pressure < threshold:


            return False



        #
        # Probability increases above threshold
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
        # Open fractures = lava dominated
        #

        elif self.fracture > 0.7:


            return "lava_flow"



        else:


            return "mixed"



    # =====================================================
    # ERUPTION SIZE
    # =====================================================


    def set_eruption_properties(self):


        variation = random.uniform(

            0.7,

            1.3

        )


        #
        # Lava
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
        # Ash
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


        self.pressure *= random.uniform(

            0.1,

            0.4

        )


        self.fracture *= random.uniform(

            0.2,

            0.5

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



for day in range(1,366):


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
Pressure: {volcano.pressure*100:.1f}%
Earthquakes: {len(earthquakes)}
Largest magnitude: {max(earthquakes, default=0):.2f}
Fracture: {volcano.fracture*100:.1f}%
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
