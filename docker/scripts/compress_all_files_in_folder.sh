#!/bin/bash

find . -name '*.z64.*' -exec zip '{}.zip' '{}' \;