#!/bin/bash
export GITHUB_TOKEN=$(grep '^export GITHUB_TOKEN' ~/.bashrc | cut -d= -f2)
python3 /home/ubuntu/.openclaw/workspace/scripts/plato_scholar.py "$@"
