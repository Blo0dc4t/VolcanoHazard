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

        ),

        "income": 10,

        "repair_cost": 1,

        "destroyed_repair_multiplier": 1.5

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

        ),

        "income": 5,

        "repair_cost": 1,

        "destroyed_repair_multiplier": 1.5

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

        ),

        "income": -1,

        "repair_cost": 1,

        "destroyed_repair_multiplier": 1.5

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



        #
        # Basic information
        #

        self.name = name

        self.type = structure_type



        #
        # Health
        #

        self.health = health

        self.max_health = health



        #
        # Rendering
        #

        self.colour = colour


        self.size = size



        #
        # Position in world grid
        #

        self.position = None



        #
        # Multiplayer ownership
        #

        self.owner = None



        #
        # Destruction state
        #

        self.destroyed = False


    # =================================================
    # GET REPAIR COST
    # =================================================
    def get_repair_cost(self):

        if self.destroyed:

            multiplier = INFRASTRUCTURE_TYPES[
                self.type
            ].get(
                "destroyed_repair_multiplier",
                1.5
            )

        else:

            multiplier = 1


        return INFRASTRUCTURE_TYPES[
            self.type
        ]["repair_cost"] * multiplier




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

            if self.owner:
                self.owner.income -= INFRASTRUCTURE_TYPES[
                    self.type
                ]["income"]


    # =================================================
    # REPAIR
    # =================================================
    def repair(self, hp_amount=None):

        if self.owner is None:
            return 0


        if self.health >= self.max_health:
            return 0
        

        missing_health = (
            self.max_health -
            self.health
        )


        repair_cost = INFRASTRUCTURE_TYPES[
            self.type
        ]["repair_cost"]


        if self.destroyed:

            repair_cost *= INFRASTRUCTURE_TYPES[
                self.type
            ].get(
                "destroyed_repair_multiplier",
                1.5
            )


        #
        # Decide requested repair amount
        #

        if hp_amount is None:

            hp_to_restore = missing_health

        else:

            hp_to_restore = min(
                hp_amount,
                missing_health
            )


        #
        # Limit by money
        #

        affordable_hp = (

            self.owner.money /

            repair_cost

        )


        hp_to_restore = min(
            hp_to_restore,
            affordable_hp
        )


        hp_to_restore = int(
            hp_to_restore
        )


        if hp_to_restore <= 0:
            return 0



        #
        # Apply repair
        #

        self.health += hp_to_restore


        self.owner.money -= round(
            hp_to_restore * repair_cost,
            2
        )


        #
        # Restore destroyed building
        #

        if self.destroyed and self.health > 0:

            self.destroyed = False

            self.owner.income += INFRASTRUCTURE_TYPES[
                self.type
            ]["income"]


        return hp_to_restore




    # =================================================
    # ASSIGN PLAYER
    # =================================================

    def assign_owner(

        self,

        player

    ):


        self.owner = player



    # =================================================
    # STATUS
    # =================================================

    def get_status(self):


        owner_name = None


        if self.owner:

            owner_name = self.owner.name



        return {


            "name":

            self.name,


            "type":

            self.type,


            "health":

            self.health,


            "destroyed":

            self.destroyed,


            "owner":

            owner_name

        }