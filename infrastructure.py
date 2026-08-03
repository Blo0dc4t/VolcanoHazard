INFRASTRUCTURE_TYPES = {


    "city": {


        "health":1000,

        "colour":(

            255,

            255,

            0

        ),

        "size":(

            5,

            5

        )

    },


    "town": {


        "health":500,

        "colour":(

            0,

            255,

            255

        ),

        "size":(

            3,

            3

        )

    },


    "road": {


        "health":300,

        "colour":(

            100,

            100,

            100

        ),

        "size":(

            10,

            1

        )

    }

}



class Infrastructure:


    def __init__(

        self,

        name,

        structure_type,

        health,

        colour,

        size=(1,1)

    ):


        self.name = name

        self.type = structure_type

        self.health = health

        self.max_health = health

        self.colour = colour

        self.size = size

        self.position = None

        self.destroyed = False



    # =================================================
    # APPLY DAMAGE
    # =================================================

    def apply_damage(

        self,

        amount

    ):


        if self.destroyed:

            return



        self.health -= amount



        if self.health <= 0:


            self.health = 0


            self.destroyed = True



    # =================================================
    # STATUS
    # =================================================

    def get_status(self):


        return {


            "name":

            self.name,


            "type":

            self.type,


            "health":

            self.health,


            "destroyed":

            self.destroyed

        }