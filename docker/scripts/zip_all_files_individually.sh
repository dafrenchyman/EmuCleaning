#!/bin/bash


for file in *; do zip -r "${file%/}.zip" "$file"; done