#!/bin/zsh

# Builds the dmg image file using node-appdmg from:
# https://github.com/LinusU/node-appdmg

# Change to current directory
cd "$(dirname "$0")"
appdmg build.json ~/Desktop/Fancy\ Folders.dmg