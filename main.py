from world import World

import matplotlib.pyplot as plt



world = World()



eruption_days=[]



for day in range(365):


    result = world.update()



#     print(

#         f"""
# Day:
# {world.day}

# Pressure:
# {world.volcano.pressure*100:.1f}%

# Fracture:
# {world.volcano.fracture*100:.1f}%

# Earthquakes:
# {len(result["earthquakes"])}

# """

#     )



    if result["eruption"]:


        eruption_days.append(

            world.day

        )


# =====================================================
# PRESSURE / FRACTURE PLOTS
# =====================================================


days=range(

    len(world.pressure_history)

)



fig,axes=plt.subplots(

    2,

    1,

    figsize=(10,8),

    sharex=True

)



axes[0].plot(

    days,

    world.pressure_history

)


for d in eruption_days:

    axes[0].axvline(

        d,

        linestyle="--"

    )



axes[0].set_title(

    "Magma Pressure"

)


axes[0].set_ylabel(

    "Pressure"

)


axes[0].grid()



axes[1].plot(

    days,

    world.fracture_history

)



for d in eruption_days:

    axes[1].axvline(

        d,

        linestyle="--"

    )



axes[1].set_title(

    "Crustal Fracture"

)


axes[1].set_xlabel(

    "Day"

)


axes[1].set_ylabel(

    "Fracture"

)


axes[1].grid()



plt.tight_layout()

plt.show()