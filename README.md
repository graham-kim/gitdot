# gitdot
Git history to DOT language translation

# Installing Pre-requisites

Do this in this repository's root directory:
`python -m pip install -r requirements.txt`

You will also need to have installed graphviz

# Sample Usage

Run this from your repository's root directory:
`git log HEAD~8..HEAD --format="%p -> %h" | python path/to/gitdot.py | dot -Tpng > out.png`
