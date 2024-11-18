"""
Minimal example of Cog usage
"""

from clock import Cog
from datetime import timedelta


class MyCog(Cog):
    """Examples of Cog usage"""

    @Cog.task(timedelta(seconds=5))
    async def task1(self):
        """
        Task after 1 minute, in timedelta
        """

        print("Executing task 1")
    
    @Cog.task("thu 10:00")
    async def task3(self):
        """
        Task at every Thursday at 10:00
        """
        print("Executing task 3")
