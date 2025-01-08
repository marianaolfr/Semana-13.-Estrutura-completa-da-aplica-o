#!/bin/bash
echo $0
git remote remove origin
git remote add origin $1
git fetch --all
git reset --hard origin/main
git branch -u origin/master master
git pull
