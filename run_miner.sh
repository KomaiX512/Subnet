#!/bin/bash

# Bittensor Subnet Miner Startup Script
# This script runs the miner with the correct wallet configuration for netuid 2

echo "🚀 Starting Bittensor Subnet Miner"
echo "📋 Configuration:"
echo "   - Wallet: miner"
echo "   - Hotkey: default"
echo "   - Netuid: 2"
echo "   - Logging: info"
echo ""

# Run the miner with correct configuration
python neurons/miner.py \
    --wallet.name miner \
    --wallet.hotkey default \
    --netuid 2 \
    --logging.info

echo "Miner stopped." 