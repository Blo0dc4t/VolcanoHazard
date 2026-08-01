import random
import math



class Volcano:


    def __init__(

        self,

        caldera_position=(500,500),


        #
        # Initial state
        #

        initial_pressure=0.25,

        initial_fracture=0.0,


        #
        # Simulation speed
        #

        time_scale=1,


        #
        # Pressure parameters
        #

        recharge_min=0.005,

        recharge_max=0.01,

        pressure_loss_max=0.01,


        #
        # Earthquake parameters
        #

        earthquake_multiplier=40,


        #
        # Fracture parameters
        #

        fracture_damage_min=0.01,

        fracture_damage_max=0.06,

        fracture_healing=0.96,


        #
        # Eruption parameters
        #

        eruption_pressure_threshold=0.8,

        fracture_pressure_effect=0.3,

        minimum_pressure=0.35


    ):


        # =================================================
        # LOCATION
        # =================================================


        self.caldera_position = caldera_position



        # =================================================
        # STATE
        # =================================================


        self.pressure = initial_pressure

        self.fracture = initial_fracture


        self.erupted = False

        self.eruption_type = None

        self.eruption_location = None



        # =================================================
        # PARAMETERS
        # =================================================


        self.time_scale = time_scale



        # Pressure

        self.recharge_min = recharge_min

        self.recharge_max = recharge_max

        self.pressure_loss_max = pressure_loss_max



        # Earthquakes

        self.earthquake_multiplier = earthquake_multiplier



        # Fracture

        self.fracture_damage_min = fracture_damage_min

        self.fracture_damage_max = fracture_damage_max

        self.fracture_healing = fracture_healing



        # Eruption

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
        # Pressure and fracture both contribute
        #

        rate = (

            0.3

            +

            self.pressure ** 2

            +

            0.5 * self.fracture

        ) * self.earthquake_multiplier * self.time_scale



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

                {

                    "magnitude":

                    self.generate_magnitude(),


                    "location":

                    self.generate_earthquake_location()

                }

            )


        return earthquakes



    # =====================================================
    # MAGNITUDE GENERATION
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


        return round(

            min(

                magnitude,

                6

            ),

            2

        )



    # =====================================================
    # EARTHQUAKE LOCATION
    # =====================================================


    def generate_earthquake_location(self):


        x0, y0 = self.caldera_position



        #
        # Most earthquakes close to caldera
        #

        distance = random.expovariate(

            1/100

        )


        angle = random.uniform(

            0,

            2*math.pi

        )


        x = x0 + math.cos(angle) * distance

        y = y0 + math.sin(angle) * distance



        return (

            round(x),

            round(y)

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
            # Reduced earthquake damage
            #
            # Magnitude squared gives a smoother
            # increase than 10^magnitude
            #

            damage = (

                magnitude ** 2

            ) * random.uniform(

                self.fracture_damage_min,

                self.fracture_damage_max

            ) / 100



            self.fracture += (

                damage

                *

                self.time_scale

            )



        #
        # Background crustal stress
        #
        # Allows fracture to develop independently
        #

        background_damage = random.uniform(

            0,

            0.001

        )


        self.fracture += (

            background_damage

            *

            self.time_scale

        )



        #
        # Slow healing
        #

        self.fracture *= (

            self.fracture_healing

            **

            self.time_scale

        )



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
        # Fracture reduces required pressure
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
        # Insufficient pressure
        #

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


            self.set_eruption_location()


            self.set_eruption_properties()



            return True



        return False



    # =====================================================
    # ERUPTION TYPE
    # =====================================================


    def choose_eruption_type(self):


        #
        # High pressure, low fracture:
        # sealed explosive system
        #

        if (

            self.pressure > 0.85

            and

            self.fracture < 0.5

        ):


            return "explosive"



        #
        # High fracture:
        # open lava pathways
        #

        elif self.fracture > 0.7:


            return "lava_flow"



        else:


            return "mixed"



    # =====================================================
    # ERUPTION LOCATION
    # =====================================================


    def set_eruption_location(self):


        x0, y0 = self.caldera_position



        #
        # Most eruptions occur at caldera
        #

        if random.random() < 0.9:


            self.eruption_location = (

                x0,

                y0

            )


            return



        #
        # Rare flank eruption
        #

        distance = random.uniform(

            20,

            100

        )


        angle = random.uniform(

            0,

            2*math.pi

        )


        x = x0 + math.cos(angle)*distance

        y = y0 + math.sin(angle)*distance



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
        # Lava intensity
        #

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


        #
        # Ash intensity
        #

        self.ash_intensity = int(

            (

                20

                +

                self.pressure * 150

            )

            *

            variation

        )


        #
        # Extent controlled by intensity
        #

        self.lava_radius = int(

            self.lava_intensity

            *

            0.5

        )


        self.ash_radius = int(

            self.ash_intensity

            *

            1.5

        )


    # =====================================================
    # RESET AFTER ERUPTION
    # =====================================================


    def release_pressure(self):


        #
        # Do not completely empty chamber
        #

        self.pressure *= random.uniform(

            0.3,

            0.6

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