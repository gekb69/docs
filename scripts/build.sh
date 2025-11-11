#!/bin/bash
set -e

echo "🏗️ Building Super Agent Core..."

# Build Rust components
echo "📦 Building Warp Core..."
cd warp-core
cargo build --release
cd ..

echo "📦 Building Sharded Vault..."
cd sharded-vault
cargo build --release
cd ..

# Build Python components
echo "📦 Installing Python dependencies..."
cd master-agent
pip install -r requirements.txt
cd ..

echo "📦 Building Web UI..."
cd web-ui
npm install
npm run build
cd ..

echo "✅ Build completed successfully!"
echo "📂 Artifacts:"
echo " - warp-core/target/release/warp-core"
echo " - sharded-vault/target/release/sharded-vault"
echo " - master-agent/"
echo " - web-ui/dist/"
