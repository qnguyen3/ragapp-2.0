#!/bin/bash

# Exit on error
set -e

echo "🚀 Building RAG Application for macOS..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Clean up previous builds
echo "🧹 Cleaning up previous builds..."
rm -rf dist frontend/dist frontend/build
mkdir -p dist/scripts

# Create app icon if it doesn't exist
echo "🎨 Setting up app icon..."
if [ ! -f "frontend/public/icon.png" ]; then
  # Create a simple placeholder icon - you should replace this with your actual icon
  convert -size 512x512 xc:transparent \
          -font Helvetica -pointsize 140 -fill black -gravity center \
          -draw "text 0,0 'RAG'" \
          frontend/public/icon.png
fi

# Copy docker-compose file
cp dist/docker-compose.yml dist/scripts/

# Create data directories setup script
cat > dist/scripts/setup_directories.sh << 'EOL'
#!/bin/bash

# Create application data directories
mkdir -p ~/.ragapp/mongodb_data
mkdir -p ~/.ragapp/chroma_db

echo "✅ Application data directories created successfully"
EOL

chmod +x dist/scripts/setup_directories.sh

# Build and export the Docker images
echo "📦 Building Docker images..."
docker-compose build

# Save the Docker images
echo "💾 Saving Docker images..."
docker save ragapp-2.0_backend mongodb:latest | gzip > dist/docker_images.tar.gz

# Build the Electron app
echo "🔨 Building Electron application..."
cd frontend
echo "📦 Installing frontend dependencies..."
npm install

echo "🏗️ Building React application..."
npm run build

echo "📦 Packaging Electron application..."
npm run package

# Check if the build was successful
if [ ! -f "dist/mac-arm64/RAG App.app" ] && [ ! -f "dist/mac/RAG App.app" ]; then
    echo "❌ Build failed! No application package was created."
    exit 1
fi

# Copy the packaged app to dist
echo "📝 Copying packaged application..."
if [ -d "dist/mac-arm64" ]; then
    cp -r "dist/mac-arm64/RAG App.app" ../dist/
elif [ -d "dist/mac" ]; then
    cp -r "dist/mac/RAG App.app" ../dist/
fi

# Create the startup script with improved error handling
echo "📜 Creating startup script..."
cat > dist/scripts/start_ragapp.sh << 'EOL'
#!/bin/bash

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Load Docker images if not already loaded
if ! docker image inspect ragapp-2.0_backend &> /dev/null; then
    echo "🔄 Loading Docker images..."
    docker load < docker_images.tar.gz
fi

# Create necessary directories
./setup_directories.sh

# Start the services
echo "🚀 Starting RAG Application services..."
cd scripts && docker-compose up -d

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
attempt=1
max_attempts=30
until docker-compose exec -T mongodb mongosh --eval "db.serverStatus()" > /dev/null 2>&1; do
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ MongoDB failed to start properly"
        exit 1
    fi
    echo "Waiting for MongoDB... ($attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

# Wait for backend service to be ready
echo "⏳ Waiting for backend service to be ready..."
attempt=1
max_attempts=30
until curl -s http://localhost:3456/health > /dev/null; do
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Backend service failed to start properly"
        exit 1
    fi
    echo "Waiting for backend... ($attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

echo "✅ Services started! You can now launch the RAG Application from your Applications folder."
EOL

# Make the startup script executable
chmod +x ../dist/start_ragapp.sh

# Create README
echo "📖 Creating README..."
cat > ../dist/README.md << 'EOL'
# RAG Application Installation Guide

## Prerequisites
- macOS 10.15 or later
- Docker Desktop for Mac

## Installation Steps

1. Install Docker Desktop for Mac if you haven't already:
   - Download from https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. Copy the RAG Application to your Applications folder

3. Run the startup script:
   ```bash
   ./start_ragapp.sh
   ```

4. Launch the RAG Application from your Applications folder

## Troubleshooting

If you encounter any issues:
1. Make sure Docker Desktop is running
2. Check if the services are running with: `docker ps`
3. View logs with: `docker-compose logs`

## Stopping the Application

To stop the backend services:
```bash
docker-compose down
```

EOL

# Create a simple installer script
echo "📦 Creating installer script..."
cat > ../dist/install.sh << 'EOL'
#!/bin/bash

# Copy application to Applications folder
echo "📂 Copying RAG Application to Applications folder..."
cp -r "RAG App.app" /Applications/

# Make scripts executable
chmod +x start_ragapp.sh

echo "✅ Installation complete! You can now:"
echo "1. Run ./start_ragapp.sh to start the backend services"
echo "2. Launch RAG Application from your Applications folder"
EOL

chmod +x ../dist/install.sh

# Create zip archive
echo "🗜️ Creating distribution archive..."
cd dist
zip -r RAGApp-macOS.zip "RAG App.app" docker_images.tar.gz scripts/* README.md install.sh

echo "✅ Build complete! Distribution package is available in the dist directory."
echo "📦 File: dist/RAGApp-macOS.zip"
