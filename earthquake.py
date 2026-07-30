import math


class Earthquake:


    def __init__(
        self,
        x,
        y,
        magnitude
    ):


        self.x = x
        self.y = y

        self.magnitude = magnitude


        #
        # How long the event remains visible
        #

        self.life = int(

            15 +

            magnitude**2 * 3

        )



    # =====================================================
    # Lifetime
    # =====================================================


    def update(self):

        self.life -= 1



    @property
    def alive(self):

        return self.life > 0



    # =====================================================
    # Hazard properties
    # =====================================================


    def radius(self):

        """

        Approximate area affected
        in grid squares.

        Larger earthquakes affect
        more tiles.

        """

        return max(

            1,

            int(self.magnitude / 1.5)

        )



    def intensity(
        self,
        distance
    ):

        """

        Ground shaking intensity.

        Maximum at epicentre.

        Decreases linearly with distance.

        """


        radius = self.radius()


        if distance > radius:

            return 0



        shaking = (

            self.magnitude**2

            *

            (1 - distance/radius)

        )


        return shaking