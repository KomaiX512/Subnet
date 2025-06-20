#!/bin/bash

# Bittensor Subnet Validator Startup Script
# This script runs the validator with the correct wallet configuration for netuid 2

echo "🚀 Starting Bittensor Subnet Validator"
echo "📋 Configuration:"
echo "   - Wallet: validator"
echo "   - Hotkey: default"
echo "   - Netuid: 2"
echo "   - Logging: info"
echo ""

# Run the validator with correct configuration
python neurons/validator.py \
    --wallet.name validator \
    --wallet.hotkey default \
    --netuid 2 \
    --logging.info

echo "Validator stopped." 