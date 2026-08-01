import random
import math

from volcano import Volcano
from terrain import Terrain



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
        # Terrain
        #

        print("creating terrain...")

        self.terrain = Terrain(

            width,

            height,

            cell_size=4,

        )

        self.grid_width = self.terrain.grid_width
        self.grid_height = self.terrain.grid_height


        self.grid = [

            [

                {

                    "building":None,

                    "lava":False,

                    "ash":0

                }

                for x in range(self.grid_width)

            ]

            for y in range(self.grid_height)

        ]


        #
        # Volcano
        #

        print("creating volcano...")

        self.volcano = Volcano(

            caldera_position=self.terrain.caldera_position,

            time_scale=1,

        )


        #
        # Wind
        #

        self.wind_direction = random.uniform(

            0,

            2*math.pi

        )


        self.wind_speed = random.uniform(

            0.5,

            2.0

        )


        #
        # Active hazards
        #

        self.ash_plumes = []

        self.lava_flows = []



        #
        # Event storage
        #

        self.earthquakes = []

        self.recent_earthquakes = []

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

        self.recent_earthquakes = earthquakes


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

            self.generate_ash_plume(

            eruption_event

            )


            self.generate_lava_flow(

                eruption_event

            )


            #
            # Reset volcano after eruption
            #

            self.volcano.release_pressure()
            
            print(self.eruptions[-1]["type"])

        
        return {


            "earthquakes":
            earthquakes,


            "eruption":
            eruption


        }

    def generate_ash_plume(

        self,

        eruption

    ):


        x0,y0 = eruption["location"]


        distance = int(

            eruption["ash_intensity"]

            *

            self.wind_speed

            *

            0.5

        )


        plume=[]


        for i in range(distance):


            spread = i * 0.05


            x = (

                x0

                +

                math.cos(self.wind_direction)

                *

                i

                +

                random.uniform(
                    -spread,
                    spread
                )

            )


            y = (

                y0

                +

                math.sin(self.wind_direction)

                *

                i

                +

                random.uniform(
                    -spread,
                    spread
                )

            )


            plume.append(

                (

                    round(x),

                    round(y)

                )

            )


        self.ash_plumes.append(

            plume

        )

    def generate_lava_flow(self, eruption):


        x,y = eruption["location"]


        gx = int(
            x / self.terrain.cell_size
        )

        gy = int(
            y / self.terrain.cell_size
        )


        flow=[]


        length = int(

            eruption["lava_intensity"]

            *

            0.5

        )



        current=(gx,gy)



        for i in range(length):


            x,y=current


            flow.append(current)



            neighbours=[

                (x+1,y),
                (x-1,y),
                (x,y+1),
                (x,y-1)

            ]


            neighbours=[

                p for p in neighbours

                if

                0 <= p[0] < self.grid_width

                and

                0 <= p[1] < self.grid_height

            ]



            if not neighbours:

                break



            current=min(

                neighbours,

                key=lambda p:

                self.terrain.height_map[p[1],p[0]]

            )



        self.lava_flows.append(flow)
        

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