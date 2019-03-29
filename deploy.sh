#!/bin/bash
set -ex

DISABLE_LIST="W0613,C0111,W1202,W1308"

for LAMBDA in $(ls -d */ | cut -f1 -d"/");
do
    if [[ $(ls $LAMBDA | grep index.py | wc -l) -eq 1 ]]; then
        echo "Linting Lambda $LAMBDA..."
        pylint --disable=$DISABLE_LIST $LAMBDA
        echo "Testing Lambda $LAMBDA..."
        pushd $LAMBDA
        pytest test.py -W ignore::DeprecationWarning
        echo "Building Lambda $LAMBDA..."
        mkdir build
        pip install -r requirements.txt --target build
        cp *.py build && rm build/test.py
        pushd build
        zip -r9 ../$LAMBDA.zip .
        popd
        rm -rf build
        if [ "$TRAVIS_PULL_REQUEST" = "false" ]; then
            echo "Publishing Lambda $LAMBDA..."
            aws s3 cp $LAMBDA.zip s3://$S3_BUCKET/$LAMBDA.zip --acl private
            aws lambda update-function-code --function-name $LAMBDA --s3-bucket $S3_BUCKET --s3-key $LAMBDA.zip --publish
        else
            echo "Just a PR, skipping Publish."
        fi
        rm -rf $LAMBDA.zip
        echo "Successfully deployed Lambda $LAMBDA."
        popd
    fi
done
