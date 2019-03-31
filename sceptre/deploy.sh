#!/bin/bash
set -ex

IGNORE_LIST="W3005"

cfn-lint -i $IGNORE_LIST -t templates/*.yaml

pushd config
STACKS=$(ls -d */ | cut -f1 -d"/")
popd

for STACK in $STACKS;
do
    echo "Launching Stack: $STACK..."
    sceptre validate $STACK
    sceptre launch $STACK -y
    echo "Successfully launched Stack: $STACK."
done
