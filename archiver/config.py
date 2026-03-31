"""Configuration loading and merging.

Precedence: CLI args > config file > defaults.
Uses tomllib (stdlib since Python 3.11) - zero external dependencies.
"""