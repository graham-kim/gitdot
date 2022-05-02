#--format="%p -> %h"

import sys

def printerr(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)