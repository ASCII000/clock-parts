import sys
from pathlib import Path

root_path = Path(__file__).parents[2]
sys.path.append(str(root_path))

from clock.shaft import Shaft

import asyncio


if __name__ == "__main__":
    # Create a new Shaft
    shaft = Shaft()
    # Add cogs folder
    shaft.add_cogs("examples/mininal/cogs")
    # Run the Shaft
    asyncio.run(shaft.run())
