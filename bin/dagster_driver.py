#!/usr/local/bin/python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dagster.cli

if __name__ == '__main__':
    dagster.cli.dagster_cli(obj={})
