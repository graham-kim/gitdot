#--format="%p -> %h"

import typing as tp
import json
from pathlib import Path

from pr_secretary import PrSecretary
from dot_translator import DotTranslator

if __name__ == '__main__':
    with open(Path(__file__).resolve().parent / 'config.json', 'r') as inF:
        cfg = json.load(inF)
    pr_secr = PrSecretary(cfg["access_token_env_var"], cfg["repo_name"])

    dot_tr = DotTranslator(pr_secr)
    dot_tr.parse_stdin()
    dot_tr.print_translation()

    pr_secr.save_cache()
