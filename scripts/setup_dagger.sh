#!/bin/bash
set -e

echo "🚀 Setting up Dagger CI/CD for SaaS Market Intelligence Platform"
echo "================================================================"

# Install Dagger CLI
echo "📦 Installing Dagger CLI..."
curl -L https://dl.dagger.io/dagger/install.sh | DAGGER_VERSION=0.9.0 sh
sudo mv bin/dagger /usr/local/bin/dagger

# Verify installation
echo "✅ Verifying Dagger installation..."
dagger version

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install dagger-io

# Initialize Dagger module
echo "🔧 Initializing Dagger module..."
cd dagger/
dagger develop

echo ""
echo "🎉 Dagger setup complete!"
echo ""
echo "Available commands:"
echo "  dagger call quick-health-check     # Quick system health check"
echo "  dagger call test-suite             # Run full test suite"
echo "  dagger call test-stripe-integration # Test payment flows"
echo "  dagger call test-rag-engine        # Test AI components"
echo "  dagger call full-ci-pipeline       # Complete CI/CD pipeline"
echo ""
echo "🎯 Ready to automate your $300/day revenue pipeline!"
