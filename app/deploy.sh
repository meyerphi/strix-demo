#!/usr/bin/env bash

set -e
set -o pipefail

docker build -t strix-lambda .

REPOSITORY_URI=$(aws ecr describe-repositories --query "repositories[?repositoryName=='strix'].repositoryUri" --output text)

docker tag strix-lambda ${REPOSITORY_URI}
docker push ${REPOSITORY_URI}

aws lambda update-function-code --function-name strix --image-uri ${REPOSITORY_URI}:latest

REST_API_ID=$(aws apigateway get-rest-apis --query "items[?name=='Strix API'].id" --output text)
AWS_REGION=$(aws configure get region)

echo "Strix API available at: https://${REST_API_ID}.execute-api.${AWS_REGION}.amazonaws.com/strix/synthesize"
