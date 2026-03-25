# AquaChain Docker Setup

## Prerequisites
- Docker Desktop installed and running
- AWS credentials configured at `~/.aws/` (for CDK/Lambda work)
- Copy `.env.example` to `.env.local` inside `frontend/` and fill in values

## Quick Start

```bash
# Start the frontend dev server (hot reload enabled)
docker-compose up frontend

# Run all Lambda tests
docker-compose run lambda pytest lambda/ -v

# Run tests for a specific service
docker-compose run lambda pytest lambda/device_management/tests/ -v

# Open a shell in the Lambda environment
docker-compose run lambda bash

# Synthesize CDK stacks (dry run)
docker-compose run cdk cdk synth

# Open a shell in the CDK environment
docker-compose run cdk bash
```

## Build Images

```bash
# Build all images
docker-compose build

# Build a specific image
docker-compose build frontend
docker-compose build lambda
docker-compose build cdk
```

## Production Frontend Build

```bash
docker build -f Dockerfile.frontend --target production -t aquachain-frontend:prod .
docker run -p 80:80 aquachain-frontend:prod
```

## Notes
- AWS credentials are mounted read-only from `~/.aws` into the CDK container
- Never commit `.env.local` or real credentials
- Lambda functions run in the same Python environment as production layers
