# Justfile for Qdrant Vector Database

# Default recipe
default:
    @just --list

# Start Qdrant
start:
    @mkdir -p qdrant_storage
    @podman run -d \
        --name qdrant \
        -p 6333:6333 \
        -v $(pwd)/qdrant_storage:/qdrant/storage \
        qdrant/qdrant:latest
    @echo "Qdrant started at http://localhost:6333"

# Stop Qdrant
stop:
    @podman stop qdrant 2>/dev/null || true
    @podman rm qdrant 2>/dev/null || true
    @echo "Qdrant stopped"

# Restart Qdrant
restart: stop start

# View Qdrant logs
logs:
    @podman logs -f qdrant

# Check Qdrant status
status:
    @podman ps --filter name=qdrant

# Clean Qdrant data (DANGER!)
clean:
    @rm -rf qdrant_storage
    @echo "Qdrant data cleaned"
