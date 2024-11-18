# ClockParts
Hi There 👋!

I'm the developer of ClockParts. I encountered many challenges when working with scheduling tasks in Python, whether in multi-threading projects, APIs, or microservices. So, I created ClockParts to address these issues. It's simple, compatible with asynchronous operations and threads, and human-readable, making scheduling in Python easier and more efficient.

## Installation
It's very easy on PyPI:

```bash
pip install ClockParts
```

## Usage
This usage is very simple and based on Shaft and Cog. Shaft is the manager of Cog, and Cog represents your tasks.

### Project structure:
``` bash
├── cogs
│   └── my_cogs.py
├── main.py
```
### Shaft

Now, let's see how to create a Shaft:

```python
# main.py
from ClockParts import Shaft
import asyncio

shaft = Shaft()

if __name__ == "__main__":
    # Create a new Shaft
    shaft = Shaft()
    # Add the "cogs" folder (by default it's "cogs")
    shaft.add_cogs("cogs")
    # Run the Shaft
    asyncio.run(shaft.run())
```
It's simple! Basically, you need an asynchronous context in your project. If you need an internal explanation, in short, it checks every second if there is a new Cog Task to execute.

### Cogs
Let's move on to your Cogs!

```python
# cogs/my_cogs.py

from ClockParts import Cog
from datetime import timedelta


class MyCog(Cog):
    """Examples of Cog usage"""

    @Cog.task(timedelta(seconds=5))
    async def task1(self):
        """
        Task to run every after 5 seconds (using timedelta)
        """
        print("Executing task 1")
    
    @Cog.task("11:00")
    async def task2(self):
        """
        Task to be performed every day at 11:00
        """
        print("Executing task 2")

    @Cog.task("thu 10:00")
    async def task3(self):
        """
        Task to be executed every Thursday at 10:00
        """
        print("Executing task 3")

    @Cog.task("1m 10:00")
    async def task4(self):
        """
        Task to be executed every month at 10:00
        """
        print("Executing task 4")
    
    @Cog.task("mon 10:00")
    async def task5(self):
        """
        Task to be executed every Monday at 10:00
        """
        print("Executing task 5")
```
Does it look simple? Yes, indeed! In short, you don't need to import ClockParts, just import Cog and use its methods to schedule tasks. There are two ways to schedule your tasks:

- String format: Ideal for selecting specific days of the week and month.
- Timedelta format: Ideal for scheduling tasks at specific times. In most cases, you should use timedelta.
Your Cogs are ready! To run your Shaft, you just need to execute main.py, and you're good to go!

If you're contributing to the repository, feel free to open an issue, pull request, or fork. You're welcome!

