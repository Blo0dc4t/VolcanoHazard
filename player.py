class Player:


    def __init__(

        self,

        name,

        colour

    ):


        self.name = name

        self.colour = colour


        #
        # Selected starting infrastructure
        #

        self.city = None


        #
        # Grid position of starting city
        #

        self.start_location = None

        #
        # Money
        # 
        self.money = 500

        #
        # Income
        #
        self.income = 0
        self.connected_structures = set()