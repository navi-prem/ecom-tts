APP_NAME=orchestrator
PROTO_DIR=api

PROTO_FILES=$(shell find $(PROTO_DIR) -name "*.proto")

.PHONY: proto run tidy build clean

proto:
	protoc \
	--go_out=. --go_opt=paths=source_relative \
	--go-grpc_out=. --go-grpc_opt=paths=source_relative \
	$(PROTO_FILES)

tidy:
	go mod tidy

build:
	go build -o bin/$(APP_NAME) ./cmd/server

run:
	go run ./cmd/server

clean:
	rm -rf bin
	rm -f $(PROTO_DIR)/*.pb.go
	rm -f $(PROTO_DIR)/*_grpc.pb.go
