from enum import Enum

class State(Enum):
    """
    States of entities
    """
    UNDEFINED = 0
    DEFINED = 1
    CONFIGURED = 3
    RUNNING = 4
    PAUSED = 5
    SCALING = 6
    MIGRATING = 7
    ## Migration concurrent states
    TAKING_OFF = 8
    LANDING = 9
