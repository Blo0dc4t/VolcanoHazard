from volcano import Volcano



class World:


    def __init__(

        self,

        width=1000,

        height=1000

    ):


        #
        # World dimensions
        #
        # These are continuous coordinates,
        # not tiles
        #

        self.width = width

        self.height = height



        #
        # Volcano
        #

        self.volcano = Volcano(

            caldera_position=(

                width//2,

                height//2

            ),

            time_scale=1,

        )



        #
        # Event storage
        #

        self.earthquakes = []

        self.eruptions = []



        #
        # History for plotting
        #

        self.pressure_history = []

        self.fracture_history = []



        #
        # Day counter
        #

        self.day = 0



    # =================================================
    # SIMULATION UPDATE
    # =================================================

    def update(self):


        self.day += 1



        #
        # Update volcano state
        #

        self.volcano.update_pressure()



        earthquakes = self.volcano.generate_earthquakes()



        self.volcano.update_fracture(

            earthquakes

        )



        #
        # Store earthquake events
        #

        self.earthquakes.extend(

            earthquakes

        )



        #
        # Store history for matplotlib
        #

        self.pressure_history.append(

            self.volcano.pressure

        )


        self.fracture_history.append(

            self.volcano.fracture

        )



        #
        # Check eruption
        #

        eruption = self.volcano.check_eruption()



        if eruption:

            eruption_event = {


                "day":
                self.day,


                "type":
                self.volcano.eruption_type,


                "location":
                self.volcano.eruption_location,


                "lava_radius":
                self.volcano.lava_radius,


                "ash_radius":
                self.volcano.ash_radius,


                "lava_intensity":
                self.volcano.lava_intensity,


                "ash_intensity":
                self.volcano.ash_intensity


            }



            self.eruptions.append(

                eruption_event

            )


            #
            # Reset volcano after eruption
            #
            
            print(self.eruptions[-1]["type"])
            self.volcano.release_pressure()
            print(self.eruptions[-1]["type"])


        return {


            "earthquakes":
            earthquakes,


            "eruption":
            eruption


        }


    # =================================================
    # DISTANCE FUNCTION
    # =================================================


    def distance(

        self,

        point1,

        point2

    ):


        x1,y1=point1

        x2,y2=point2



        return (

            (

                (x2-x1)**2

                +

                (y2-y1)**2

            )

            **0.5

        )



    # =================================================
    # HAZARD CHECKING
    # =================================================


    def get_lava_damage(

        self,

        position

    ):


        damage=0



        for eruption in self.eruptions:


            distance=self.distance(

                position,

                eruption["location"]

            )


            if distance < eruption["lava_radius"]:


                damage += (

                    eruption["lava_intensity"]

                    *

                    (

                        1 -

                        distance /

                        eruption["lava_radius"]

                    )

                )



        return damage



    def get_ash_damage(

        self,

        position

    ):


        damage=0



        for eruption in self.eruptions:


            distance=self.distance(

                position,

                eruption["location"]

            )


            if distance < eruption["ash_radius"]:


                damage += (

                    eruption["ash_intensity"]

                    *

                    (

                        1 -

                        distance /

                        eruption["ash_radius"]

                    )

                )



        return damage