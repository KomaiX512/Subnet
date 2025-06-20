#!/usr/bin/env python3

import subprocess
import time
import signal
import sys
import os

def run_miner():
    """Start the miner process"""
    print("🔨 Starting Miner...")
    miner_cmd = [
        "python", "neurons/miner.py",
        "--wallet.name", "miner",
        "--wallet.hotkey", "miner_hotkey", 
        "--logging.info",
        "--subtensor.chain_endpoint", "ws://127.0.0.1:9944",
        "--netuid", "2",
        "--subtensor.network", "local",
        "--axon.port", "8091",
        "--axon.ip", "127.0.0.1",
        "--axon.external_ip", "127.0.0.1",
        "--axon.external_port", "8091"
    ]
    
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/komail/bittensor-subnet-template"
    
    return subprocess.Popen(miner_cmd, env=env)

def run_validator():
    """Start the validator process"""
    print("🛡️ Starting Validator...")
    validator_cmd = [
        "python", "neurons/validator.py",
        "--wallet.name", "validator",
        "--wallet.hotkey", "validator_hotkey",
        "--logging.info", 
        "--subtensor.chain_endpoint", "ws://127.0.0.1:9944",
        "--netuid", "2",
        "--subtensor.network", "local"
    ]
    
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/komail/bittensor-subnet-template"
    
    return subprocess.Popen(validator_cmd, env=env)

def main():
    print("🚀 Starting Basic Bittensor Subnet Demonstration")
    print("=" * 60)
    print("This will run a basic miner and validator to show subnet functionality")
    print("Press Ctrl+C to stop both processes")
    print("=" * 60)
    
    miner_process = None
    validator_process = None
    
    try:
        # Start miner
        miner_process = run_miner()
        print("✅ Miner started")
        
        # Wait for miner to initialize
        print("⏳ Waiting for miner to initialize...")
        time.sleep(10)
        
        # Start validator
        validator_process = run_validator()
        print("✅ Validator started")
        
        print("\n🎉 BOTH PROCESSES ARE RUNNING!")
        print("📊 Watch the logs above to see the subnet in action:")
        print("   • Miner: Responds to validator requests")
        print("   • Validator: Sends queries and rewards miners")
        print("   • Weight setting: Validator sets weights based on performance")
        print("\nPress Ctrl+C to stop...")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopping processes...")
        
    finally:
        # Clean up processes
        if miner_process:
            miner_process.terminate()
            miner_process.wait()
            print("✅ Miner stopped")
            
        if validator_process:
            validator_process.terminate()
            validator_process.wait()
            print("✅ Validator stopped")
            
        print("🎯 Subnet demonstration complete!")

if __name__ == "__main__":
    main() 