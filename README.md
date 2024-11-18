# ClockParts
Hi there!

I'm the developer of ClockParts. I encountered many problems in multi-threading projects, APIs, microservices, etc. So I created ClockParts to solve these issues. It's simple, compatible with asynchronous operations and threads, and human-readable.

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

from clock import Cog
from datetime import timedelta


class MyCog(Cog):
    """Examples of Cog usage"""

    @Cog.task(timedelta(seconds=5))
    async def task1(self):
        """
        Task to be executed after 5 seconds (using timedelta)
        """

        print("Executing task 1")
    
    @Cog.task("thu 10:00")
    async def task3(self):
        """
        Task to be executed every Thursday at 10:00
        """
        print("Executing task 3")
```
Does it look simple? Yes, indeed! In short, you don't need to import ClockParts, just import Cog and use its methods to schedule tasks. There are two ways to schedule your tasks:

- String format: Ideal for selecting specific days of the week and month.
- Timedelta format: Ideal for scheduling tasks at specific times. In most cases, you should use timedelta.
Your Cogs are ready! To run your Shaft, you just need to execute main.py, and you're good to go!

If you're contributing to the repository, feel free to open an issue, pull request, or fork. You're welcome!

