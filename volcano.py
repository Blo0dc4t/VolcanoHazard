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
        # Pressure parameters
        #

        recharge_min=0.005,

        recharge_max=0.01,

        pressure_loss_max=0.01,


        #
        # Earthquake parameters
        #

        earthquake_multiplier=40,

        earthquake_distance_scale=150,


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


        self.caldera_position = caldera_position


        #
        # Current state
        #

        self.pressure = initial_pressure

        self.fracture = initial_fracture


        self.erupted = False

        self.eruption_type = None

        self.eruption_location = None



        #
        # Parameters
        #

        self.recharge_min = recharge_min

        self.recharge_max = recharge_max

        self.pressure_loss_max = pressure_loss_max


        self.earthquake_multiplier = earthquake_multiplier

        self.earthquake_distance_scale = earthquake_distance_scale


        self.fracture_damage_min = fracture_damage_min

        self.fracture_damage_max = fracture_damage_max

        self.fracture_healing = fracture_healing


        self.eruption_pressure_threshold = eruption_pressure_threshold

        self.fracture_pressure_effect = fracture_pressure_effect

        self.minimum_pressure = minimum_pressure



        #
        # Output
        #

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


        self.pressure += recharge - loss


        self.pressure = max(

            0,

            min(

                self.pressure,

                1

            )

        )



    # =====================================================
    # EARTHQUAKES
    # =====================================================

    def generate_earthquakes(self):


        rate = (

            0.3

            +

            self.pressure ** 2

            +

            0.5*self.fracture

        ) * self.earthquake_multiplier



        number = int(

            random.gauss(

                rate,

                math.sqrt(max(rate,1))

            )

        )


        number = max(

            0,

            number

        )


        earthquakes=[]


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
    # MAGNITUDE
    # =====================================================

    def generate_magnitude(self):


        r=random.random()


        magnitude = (

            1.0

            -

            math.log10(r)

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


        x0,y0=self.caldera_position


        distance=random.expovariate(

            1/self.earthquake_distance_scale

        )


        angle=random.uniform(

            0,

            2*math.pi

        )


        return (

            round(x0 + math.cos(angle)*distance),

            round(y0 + math.sin(angle)*distance)

        )



    # =====================================================
    # FRACTURE UPDATE
    # =====================================================

    def update_fracture(self, earthquakes):


        for earthquake in earthquakes:


            magnitude = earthquake["magnitude"]


            damage = (

                magnitude ** 2

            ) * random.uniform(

                self.fracture_damage_min,

                self.fracture_damage_max

            ) / 100


            self.fracture += damage



        #
        # Background stress
        #

        self.fracture += random.uniform(

            0,

            0.001

        )



        #
        # Healing
        #

        self.fracture *= self.fracture_healing



        self.fracture=max(

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


        threshold = (

            self.eruption_pressure_threshold

            -

            self.fracture_pressure_effect*self.fracture

        )


        threshold=max(

            threshold,

            self.minimum_pressure

        )


        if self.pressure < threshold:

            return False



        probability=(

            self.pressure-threshold

        )/(1-threshold)


        probability=max(

            0,

            min(

                probability,

                1

            )

        )


        if random.random() < probability:


            self.erupted=True

            self.eruption_type=self.choose_eruption_type()

            self.set_eruption_location()

            self.set_eruption_properties()


            return True



        return False



    # =====================================================
    # NEW ERUPTION TYPE LOGIC
    # =====================================================

    def choose_eruption_type(self):


        #
        # High pressure + intact rock
        # favours explosive eruptions
        #

        explosive = (

            self.pressure ** 3

        ) * (

            1-self.fracture

        )



        #
        # Fractures create lava pathways
        #

        lava_flow = (

            self.fracture ** 2

        )



        #
        # Mixed is baseline
        #

        mixed = 1.0



        total=(

            explosive

            +

            lava_flow

            +

            mixed

        )


        value=random.random()*total



        if value < explosive:

            return "explosive"



        elif value < explosive + lava_flow:

            return "lava_flow"



        else:

            return "mixed"



    # =====================================================
    # LOCATION
    # =====================================================

    def set_eruption_location(self):


        x0,y0=self.caldera_position


        if random.random()<0.9:


            self.eruption_location=(

                x0,

                y0

            )


            return



        distance=random.uniform(

            20,

            100

        )


        angle=random.uniform(

            0,

            2*math.pi

        )


        self.eruption_location=(

            round(x0+math.cos(angle)*distance),

            round(y0+math.sin(angle)*distance)

        )



    # =====================================================
    # NEW ERUPTION OUTPUT
    # =====================================================

    def set_eruption_properties(self):


        variation=random.uniform(

            0.7,

            1.3

        )


        #
        # Base behaviour
        #

        self.lava_intensity=(

            20

            +

            self.pressure*80

            +

            self.fracture*100

        )


        self.ash_intensity=(

            20

            +

            self.pressure*200

            +

            (1-self.fracture)*50

        )



        #
        # Apply eruption style
        #

        if self.eruption_type=="explosive":


            self.lava_intensity *= 0.3

            self.ash_intensity *= 1.5



        elif self.eruption_type=="lava_flow":


            self.lava_intensity *= 1.5

            self.ash_intensity *= 0.5



        #
        # Natural variation
        #

        self.lava_intensity *= variation

        self.ash_intensity *= variation



        self.lava_intensity=int(

            self.lava_intensity

        )


        self.ash_intensity=int(

            self.ash_intensity

        )



    # =====================================================
    # RESET
    # =====================================================

    def release_pressure(self):


        self.pressure *= random.uniform(

            0.3,

            0.6

        )


        self.fracture *= random.uniform(

            0.2,

            0.5

        )


        self.erupted=False

        self.eruption_type=None

        self.eruption_location=None

        self.lava_intensity=0

        self.ash_intensity=0