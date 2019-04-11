#!/bin/bash
set -e

DISABLE_LIST="W0613,C0111,W1202,W1308,C0103,R0801"

echo "Linting Lambdas..."
pylint --disable=$DISABLE_LIST src

echo "Testing Lambdas..."
python -m pytest --cov=src test -W ignore::DeprecationWarning

if [ "$TRAVIS_PULL_REQUEST" = "false" ]; then
    pushd src
    for LAMBDA in $(ls -d */ | cut -f1 -d"/");
    do
        if [[ $(ls $LAMBDA | grep index.py | wc -l) -eq 1 ]]; then
            pushd $LAMBDA
            echo "Building Lambda $LAMBDA..."
            mkdir build
            pip install -r requirements.txt --target build
            cp *.py build
            pushd build
            zip -r9 ../$LAMBDA.zip .
            popd
            rm -rf build
            echo "Publishing Lambda $LAMBDA..."
            aws s3 cp $LAMBDA.zip s3://$S3_BUCKET/$LAMBDA.zip --acl private
            aws lambda update-function-code --function-name $LAMBDA --s3-bucket $S3_BUCKET --s3-key $LAMBDA.zip --publish | grep Version
            rm -rf $LAMBDA.zip
            echo "Successfully deployed Lambda $LAMBDA."
            popd
        fi
    done
    popd
else
    echo "Just a PR, skipping Build & Deploy."
fi
