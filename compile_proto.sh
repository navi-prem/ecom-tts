#!/bin/bash
# Compile protobuf files for all services

echo "Compiling protobuf files..."

# Create output directories
mkdir -p proto/python
mkdir -p semantic-engine/proto
mkdir -p orchestrator/app/clients

# Compile for Python
echo "Generating Python protobuf files..."
python3 -m grpc_tools.protoc \
    -I./proto \
    --python_out=./proto/python \
    --grpc_python_out=./proto/python \
    ./proto/product.proto

# Copy to semantic-engine
cp proto/python/product_pb2.py semantic-engine/proto/
cp proto/python/product_pb2_grpc.py semantic-engine/proto/

# Copy to orchestrator
cp proto/python/product_pb2.py orchestrator/app/clients/
cp proto/python/product_pb2_grpc.py orchestrator/app/clients/

# Copy to test root
cp proto/python/product_pb2.py .
cp proto/python/product_pb2_grpc.py .

echo "Done! Protobuf files generated and copied to all services."
