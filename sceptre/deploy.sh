#!/bin/bash
set -ex

cfn-lint templates/*.yaml

pushd config
STACKS=$(ls -d */ | cut -f1 -d"/")
popd

for STACK in $STACKS;
do
    echo "Launching Stack: $STACK..."
    sceptre launch $STACK -y
    echo "Successfully launched Stack: $STACK."
done
