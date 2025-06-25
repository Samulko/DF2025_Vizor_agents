from dataclasses import dataclass
from enum import Enum
from typing import List


@dataclass
class AssemblyElement:
    """Represents a timber element in the assembly."""

    type: str  # redA, greenA, blueA, redB, greenB, blueB
    id: str  # 01, 02, 03 etc.
    width: float  # 5 cm
    height: float  # 5 cm
    length: float  # 20 - 80 cm
    position: list  # x, y, 0
    vector: list  # x, y, 0
    connections: List[str]  # IDs of connected elements


class TaskType(Enum):
    """Types of assembly tasks."""

    PLACEMENT = "placement"
    PLACEMENT_HOLD = "placement_hold"
    JOINING = "joining"
    VERIFICATION = "verification"


class ActorType(Enum):
    """Types of actors that can perform tasks."""

    HUMAN = "human"  # place and screw beam
    ROBOT = "robot"  # place and hold beam
    COLLABORATIVE = "collaborative"  # implemented as a parallel human/robot task


@dataclass
class AssemblyTask:
    """Represents a single assembly task."""

    id: str
    type: TaskType  # determines robot speech pattern
    assigned_to: ActorType
    element_id: str
    description: str  # description of the task
    status: str = "pending"
