import sys
import subprocess
from abc import ABC


class DryRunnable:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

# wrapper that do not execute func, but print what it will do
def maybe_dry(func):
    def wrap(*args, **kwargs):
        if args[0].dry_run:
            fname = func.__name__
            if func.__closure__:
                fname = func.__closure__[-1].cell_contents.__name__

            print(f'{fname}: {", ".join(map(str, args[1:]))}') 
            
            return

        func(*args, **kwargs)

    return wrap