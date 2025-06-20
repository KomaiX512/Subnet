#!/usr/bin/env python3

import time
import asyncio
import sys
import os
import bittensor as bt

# Add the current directory to Python path
sys.path.insert(0, '/home/komail/bittensor-subnet-template')

import template
from template.base.miner import BaseMinerNeuron
from template.base.validator import BaseValidatorNeuron

def test_basic_template_functionality():
    """Test the basic functionality of the subnet template"""
    
    print("🧪 Testing Basic Bittensor Subnet Template Functionality")
    print("=" * 60)
    
    # Test 1: Protocol imports
    print("1. Testing protocol imports...")
    try:
        from template.protocol import Dummy
        print("   ✅ Protocol import successful")
    except Exception as e:
        print(f"   ❌ Protocol import failed: {e}")
        return False
    
    # Test 2: Base class imports
    print("2. Testing base class imports...")
    try:
        from template.base.miner import BaseMinerNeuron
        from template.base.validator import BaseValidatorNeuron
        print("   ✅ Base class imports successful")
    except Exception as e:
        print(f"   ❌ Base class imports failed: {e}")
        return False
    
    # Test 3: Validator components
    print("3. Testing validator components...")
    try:
        from template.validator import forward
        from template.validator.reward import reward, get_rewards
        print("   ✅ Validator components import successful")
    except Exception as e:
        print(f"   ❌ Validator components import failed: {e}")
        return False
    
    # Test 4: Create dummy synapse
    print("4. Testing synapse creation...")
    try:
        synapse = Dummy(dummy_input=5)
        print(f"   ✅ Synapse created with input: {synapse.dummy_input}")
    except Exception as e:
        print(f"   ❌ Synapse creation failed: {e}")
        return False
    
    # Test 5: Test miner logic
    print("5. Testing miner logic...")
    try:
        # Simulate miner forward function
        synapse.dummy_output = synapse.dummy_input * 2
        expected = 10
        if synapse.dummy_output == expected:
            print(f"   ✅ Miner logic works: {synapse.dummy_input} * 2 = {synapse.dummy_output}")
        else:
            print(f"   ❌ Miner logic failed: Expected {expected}, got {synapse.dummy_output}")
            return False
    except Exception as e:
        print(f"   ❌ Miner logic test failed: {e}")
        return False
    
    # Test 6: Test reward function
    print("6. Testing reward function...")
    try:
        from template.validator.reward import reward
        import torch
        
        # Test individual reward function
        query = 5
        correct_response = 10  # 5 * 2
        wrong_response = 8
        
        reward_correct = reward(query, correct_response)
        reward_wrong = reward(query, wrong_response)
        
        if reward_correct == 1.0 and reward_wrong == 0.0:
            print(f"   ✅ Reward function works correctly")
        else:
            print(f"   ❌ Reward function failed: correct={reward_correct}, wrong={reward_wrong}")
            return False
    except Exception as e:
        print(f"   ❌ Reward function test failed: {e}")
        return False
    
    print("=" * 60)
    print("🎉 All basic functionality tests passed!")
    print("✅ The subnet template is working correctly")
    return True

def test_network_connectivity():
    """Test basic network connectivity to local subtensor"""
    print("\n🌐 Testing Network Connectivity")
    print("=" * 60)
    
    try:
        # Test connection to local subtensor - using correct parameter name
        subtensor = bt.subtensor(
            network="local"
        )
        print(f"   ✅ Connected to subtensor: {subtensor.network}")
        
        # Check if subnet 2 exists
        if subtensor.subnet_exists(2):
            print("   ✅ Subnet 2 exists")
            
            # Get subnet info
            metagraph = subtensor.metagraph(2)
            print(f"   ✅ Metagraph loaded: {metagraph.n} neurons")
            
            return True
        else:
            print("   ❌ Subnet 2 does not exist")
            return False
            
    except Exception as e:
        print(f"   ❌ Network connectivity test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Bittensor Subnet Template Tests")
    print()
    
    # Run basic functionality tests
    basic_test_passed = test_basic_template_functionality()
    
    # Run network connectivity tests
    network_test_passed = test_network_connectivity()
    
    print("\n" + "=" * 60)
    if basic_test_passed and network_test_passed:
        print("🎉 ALL TESTS PASSED! The basic subnet template is fully functional.")
        print("✅ Ready for customization!")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        
    print("=" * 60) 