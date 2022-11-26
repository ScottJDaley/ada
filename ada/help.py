from .query import Query
from .result import Result


class HelpQuery(Query):
    pass


class HelpResult(Result):
    def __str__(self) -> str:
        return """
ADA is a bot for the videogame Satisfactory.

ADA can be used to get information about items,
buildings, and recipes. ADA can also be used to
calculate an optimal production chain. Here are
some examples of queries that ADA supports:

```
ada iron rod
```
```
ada recipes for iron rod
```
```
ada recipes for refineries
```

```
ada produce 60 iron rods
```
```
ada produce 60 iron rod from ? iron ore
```
```
ada produce ? iron rods from 60 iron ore
```
```
ada produce ? power from 240 crude oil with only
    fuel generators
```
```
ada produce 60 modular frames without refineries
```

For more information and examples, see [the GitHub page](https://github.com/ScottJDaley/ada).

If you have any questions or concerns, please join the [ADA Bot Support Server](https://discord.gg/UnFkv4wDYJ).
"""
