import random
import math

from constants import *

from earthquake import Earthquake



class EarthquakeGenerator:


    def __init__(self):

        self.events = []



    # =====================================================
    # Generate earthquakes
    # =====================================================


    def generate(
        self,
        pressure,
        caldera
    ):


        x0, y0 = caldera
        print("Caldera:", caldera)



        #
        # Earthquake rate increases
        # with pressure
        #

        probability = (

            pressure / PRESSURE_MAX

        ) * 0.8



        if random.random() < probability:


            #
            # Gutenberg-Richter style magnitude
            #
            # More small earthquakes,
            # fewer large ones.
            #

            magnitude = self.generate_magnitude()



            #
            # Distance from caldera decreases
            # exponentially.
            #

            distance = random.expovariate(

                1 / SWARM_RADIUS

            )


            angle = random.uniform(

                0,

                2*math.pi

            )


            x = int(

                x0 +

                math.cos(angle)

                *

                distance

            )


            y = int(

                y0 +

                math.sin(angle)

                *

                distance

            )



            #
            # Keep inside map
            #

            x = max(

                0,

                min(

                    COLS-1,

                    x

                )

            )


            y = max(

                0,

                min(

                    ROWS-1,

                    y

                )

            )



            self.events.append(

                Earthquake(

                    x,

                    y,

                    magnitude

                )

            )
            print(
                "New quake:",
                x,
                y,
                magnitude
            )



    # =====================================================
    # Magnitude distribution
    # =====================================================


    def generate_magnitude(self):


        """

        Gutenberg-Richter:

        log10(N) = a - bM


        Approximation:

        small events common,
        large events rare.

        """


        beta = 1.0


        r = random.random()


        magnitude = (

            -math.log10(r)

            /

            beta

        )


        magnitude += MIN_MAGNITUDE



        return min(

            magnitude,

            MAX_MAGNITUDE

        )



    # =====================================================
    # Update earthquake catalogue
    # =====================================================


    def update(self):


        alive = []


        for quake in self.events:


            quake.update()


            if quake.alive:

                alive.append(quake)



        self.events = alive