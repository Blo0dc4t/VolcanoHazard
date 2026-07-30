import random

from constants import *


class Volcano:


    def __init__(self):


        self.pressure = random.randint(

            PRESSURE_MIN,

            PRESSURE_MAX

        )


        self.explosivity = random.randint(

            0,

            100

        )


        self.erupted = False


        self.eruption_radius = 0

        self.ash_radius = 0


        self.damage = 0


        self.eruption_power = 0


        self.lava_intensity = 0

        self.ash_intensity = 0



    def update(self):


        self.erupted = False


        self.lava_intensity = 0

        self.ash_intensity = 0



        #
        # Recharge pressure
        #

        self.pressure += random.gauss(

            3,

            5

        )



        #
        # Small releases
        #

        if random.random() < 0.03:


            self.pressure -= random.randint(

                10,

                25

            )



        self.pressure = max(

            PRESSURE_MIN,

            min(

                PRESSURE_MAX,

                self.pressure

            )

        )



        if self.pressure >= ERUPTION_THRESHOLD:


            self.erupt()



    def erupt(self):


        self.erupted = True



        self.eruption_power = (

            self.pressure +

            self.explosivity

        )



        power = self.eruption_power



        #
        # Spatial effects
        #

        self.eruption_radius = max(

            2,

            int(power/30)

        )


        self.ash_radius = max(

            5,

            int(power/10)

        )



        #
        # Damage

        #

        self.damage = int(

            power*2

        )



        #
        # Hazard intensity

        #

        self.lava_intensity = (

            power * 0.8

        )


        self.ash_intensity = (

            power * 1.2

        )



        #
        # Pressure release
        #

        if power < 120:


            release = random.randint(

                40,

                60

            )


        elif power < 170:


            release = random.randint(

                60,

                80

            )


        else:


            release = random.randint(

                80,

                95

            )



        self.pressure -= release



        self.pressure = max(

            0,

            self.pressure

        )