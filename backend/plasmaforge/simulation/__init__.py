"""
Simulation package: turns raw physics primitives into a running, stateful
plasma-globe simulation. This is the orchestration layer — it decides
*when* to call physics functions and *what* to do with the results; it
does not implement field math or vector math itself (that's physics/).
"""
