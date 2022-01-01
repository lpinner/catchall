"
Context manager for "stuff"
E.g

```
import arcpy
from env import env

with env(arcy.env, workspace='C:/Temp'):
   do_stuff()
```
License is Apache 2.0
"""

from contextlib import contextmanager

@contextmanager
def env(obj, **kwargs):
    """ Temporarily set env var """

    old_env = {}
    try:
        for key, val in kwargs.items():
            old_env[key] = getattr(obj, key)
            setattr(obj, key, val)

        yield

    except Exception:
        raise

    finally:
        for key, val in old_env.items():
            setattr(obj, key, val)
