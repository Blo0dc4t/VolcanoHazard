from constants import INFRASTRUCTURE


def create_infrastructure(kind):

    """
    Create a new piece of infrastructure.
    """

    definition = INFRASTRUCTURE[kind]

    return {

        "type": kind,

        "health": definition["max_health"]

    }


def apply_damage(item, hazards):

    """
    Apply all hazards to one infrastructure item.
    """

    definition = INFRASTRUCTURE[item["type"]]

    damage = 0


    for hazard, intensity in hazards.items():

        damage += (

            intensity *

            definition["vulnerability"][hazard]

        )


    item["health"] -= damage

    item["health"] = max(

        0,

        item["health"]

    )


def destroyed(item):

    return item["health"] <= 0