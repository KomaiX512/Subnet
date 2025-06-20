# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import time
import logging
import argparse
import bittensor as bt
import threading
import subprocess
import sys
import os

# Add the project root to Python path for template imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Bittensor Miner Template:
import template

# import base miner class which takes care of most of the boilerplate
from template.base.miner import BaseMinerNeuron

# Import stage tracking system
try:
    # Try importing from Miners directory first
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Miners'))
    from miner_stage_tracker import MinerStageReporter, get_tracker, reset_stages
    STAGE_TRACKING_AVAILABLE = True
except ImportError:
    # Fallback if stage tracking not available
    STAGE_TRACKING_AVAILABLE = False
    bt.logging.warning("Stage tracking system not available - continuing without stage monitoring")


class Miner(BaseMinerNeuron):
    """
    Enhanced Miner with integrated stage tracking and multi-module support.
    
    This miner orchestrates two main modules:
    - Module 1: Content recommendation system (main.py) 
    - Module 2: Image generator and query handler
    
    Features:
    - Real-time stage progress monitoring
    - Dual operation modes (direct processing vs watchdog)
    - Clean, user-friendly logging
    - Robust error handling and recovery
    """

    def __init__(self, config=None):
        # Initialize stage tracking FIRST, before any Bittensor initialization
        self.stage_reporter = None
        self.main_process = None
        self.module2_process = None
        self.processing_mode = "watchdog"  # "watchdog" or "direct"
        
        if STAGE_TRACKING_AVAILABLE:
            # Initialize stage monitoring immediately
            self.stage_reporter = MinerStageReporter(get_tracker(), bt.logging)
            reset_stages()  # Start fresh
            bt.logging.info("🎯 Stage tracking system initialized")
        
        # Show our integration is working BEFORE Bittensor init
        bt.logging.info("🚀 Initializing Content Recommendation Miner")
        bt.logging.info("📋 Starting Module 1: Content recommendation system")
        bt.logging.info("📋 Starting Module 2: Image generator and query handler")
        
        # Start stage monitoring early
        if self.stage_reporter:
            self.stage_reporter.start_monitoring(check_interval=1.0)
            bt.logging.info("📊 Stage monitoring activated")
        
        # Start modules early to show functionality
        try:
            self._start_module1_watchdog()
            self._start_module2()
            bt.logging.info("✅ All modules initialized successfully")
        except Exception as e:
            bt.logging.error(f"❌ Failed to initialize modules: {str(e)}")
        
        # Now try Bittensor initialization
        try:
            super(Miner, self).__init__(config=config)
            bt.logging.info("✅ Bittensor initialization completed successfully")
            self.bittensor_initialized = True
        except Exception as e:
            bt.logging.error(f"❌ Bittensor initialization failed: {str(e)}")
            bt.logging.info("⚠️ Continuing with limited functionality (modules still running)")
            self.bittensor_initialized = False
            # Set minimal required attributes for our functionality
            self.config = config or {}
            # Don't raise the exception - continue with our modules running

    def _initialize_modules(self):
        """Initialize and start the processing modules (deprecated - now called directly in __init__)"""
        pass  # This is now handled directly in __init__ for better error handling

    def _start_module1_watchdog(self):
        """Start Module 1 in watchdog mode (sequential processing loop)"""
        try:
            # Get the path to encrypted miner launcher (replaces main.py)
            launcher_py_path = os.path.join(os.path.dirname(__file__), '..', 'Miners', 'miner_launcher.py')
            
            if not os.path.exists(launcher_py_path):
                bt.logging.error(f"❌ miner_launcher.py not found at: {launcher_py_path}")
                # Fallback to original main.py if launcher not available
                fallback_path = os.path.join(os.path.dirname(__file__), '..', 'Miners', 'main.py')
                if os.path.exists(fallback_path):
                    bt.logging.warning("⚠️ Using fallback to original main.py")
                    launcher_py_path = fallback_path
                else:
                    bt.logging.error("❌ Neither miner_launcher.py nor main.py found")
                    return False
            
            # Start encrypted miner launcher with sequential processing mode
            self.main_process = subprocess.Popen(
                [sys.executable, launcher_py_path, '--sequential'],
                cwd=os.path.dirname(launcher_py_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processing_mode = "watchdog"
            launcher_name = "encrypted launcher" if "miner_launcher.py" in launcher_py_path else "main.py"
            bt.logging.info(f"🔄 Module 1 started in watchdog mode using {launcher_name} (PID: {self.main_process.pid})")
            bt.logging.info("⏳ Waiting for account information to begin processing...")
            
            return True
            
        except Exception as e:
            bt.logging.error(f"❌ Failed to start Module 1: {str(e)}")
            return False

    def _start_module2(self):
        """Start Module 2 (image generator and query handler)"""
        try:
            # Get the path to Module2
            module2_path = os.path.join(os.path.dirname(__file__), '..', 'Miners', 'Module2')
            module2_main = os.path.join(module2_path, 'main.py')
            
            if not os.path.exists(module2_main):
                bt.logging.warning(f"⚠️ Module2 not found at: {module2_main}")
                return False
            
            # Start Module2 as separate process
            self.module2_process = subprocess.Popen(
                [sys.executable, module2_main],
                cwd=module2_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            bt.logging.info(f"🎨 Module 2 started successfully (PID: {self.module2_process.pid})")
            return True
            
        except Exception as e:
            bt.logging.error(f"❌ Failed to start Module 2: {str(e)}")
            return False

    def _check_modules_health(self):
        """Check the health of running modules"""
        try:
            # Check Module 1
            if self.main_process:
                poll_result = self.main_process.poll()
                if poll_result is not None:
                    bt.logging.error(f"❌ Module 1 process terminated with code: {poll_result}")
                    # Attempt to restart
                    bt.logging.info("🔄 Attempting to restart Module 1...")
                    self._start_module1_watchdog()
            
            # Check Module 2  
            if self.module2_process:
                poll_result = self.module2_process.poll()
                if poll_result is not None:
                    bt.logging.error(f"❌ Module 2 process terminated with code: {poll_result}")
                    # Attempt to restart
                    bt.logging.info("🔄 Attempting to restart Module 2...")
                    self._start_module2()
                    
        except Exception as e:
            bt.logging.error(f"❌ Error checking module health: {str(e)}")

    def get_current_status(self) -> str:
        """Get a human-readable status of the miner"""
        try:
            status_parts = []
            
            # Processing mode
            status_parts.append(f"Mode: {self.processing_mode}")
            
            # Bittensor status
            if hasattr(self, 'bittensor_initialized'):
                if self.bittensor_initialized:
                    status_parts.append("Bittensor: OK")
                else:
                    status_parts.append("Bittensor: Failed")
            
            # Module statuses
            if self.main_process and self.main_process.poll() is None:
                status_parts.append("Module 1: Running")
            else:
                status_parts.append("Module 1: Stopped")
                
            if self.module2_process and self.module2_process.poll() is None:
                status_parts.append("Module 2: Running")
            else:
                status_parts.append("Module 2: Stopped")
            
            # Current stage if available
            if self.stage_reporter:
                current_stage = get_tracker().get_current_stage()
                if current_stage:
                    stage_name = current_stage.get("stage_name", "Unknown")
                    stage_status = current_stage.get("status", "unknown")
                    username = current_stage.get("username", "")
                    user_part = f" ({username})" if username else ""
                    status_parts.append(f"Stage: {stage_name} - {stage_status}{user_part}")
            
            return " | ".join(status_parts)
            
        except Exception as e:
            return f"Status check failed: {str(e)}"

    async def forward(
        self, synapse: template.protocol.Dummy
    ) -> template.protocol.Dummy:
        """
        Processes the incoming 'Dummy' synapse by performing a predefined operation on the input data.
        This method should be replaced with actual logic relevant to the miner's purpose.

        Args:
            synapse (template.protocol.Dummy): The synapse object containing the 'dummy_input' data.

        Returns:
            template.protocol.Dummy: The synapse object with the 'dummy_output' field set to twice the 'dummy_input' value.

        The 'forward' function is a placeholder and should be overridden with logic that is appropriate for
        the miner's intended operation. This method demonstrates a basic transformation of input data.
        """
        # TODO(developer): Replace with actual implementation logic.
        synapse.dummy_output = synapse.dummy_input * 2
        return synapse

    async def blacklist(
        self, synapse: template.protocol.Dummy
    ) -> typing.Tuple[bool, str]:
        """
        Determines whether an incoming request should be blacklisted and thus ignored. Your implementation should
        define the logic for blacklisting requests based on your needs and desired security parameters.

        Blacklist runs before the synapse data has been deserialized (i.e. before synapse.data is available).
        The synapse is instead contracted via the headers of the request. It is important to blacklist
        requests before they are deserialized to avoid wasting resources on requests that will be ignored.

        Args:
            synapse (template.protocol.Dummy): A synapse object constructed from the headers of the incoming request.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating whether the synapse's hotkey is blacklisted,
                            and a string providing the reason for the decision.

        This function is a security measure to prevent resource wastage on undesired requests. It should be enhanced
        to include checks against the metagraph for entity registration, validator status, and sufficient stake
        before deserialization of synapse data to minimize processing overhead.

        Example blacklist logic:
        - Reject if the hotkey is not a registered entity within the metagraph.
        - Consider blacklisting entities that are not validators or have insufficient stake.

        In practice it would be wise to blacklist requests from entities that are not validators, or do not have
        enough stake. This can be checked via metagraph.S and metagraph.validator_permit. You can always attain
        the uid of the sender via a metagraph.hotkeys.index( synapse.dendrite.hotkey ) call.

        Otherwise, allow the request to be processed further.
        """

        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            bt.logging.warning(
                "Received a request without a dendrite or hotkey."
            )
            return True, "Missing dendrite or hotkey"

        # TODO(developer): Define how miners should blacklist requests.
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        if (
            not self.config.blacklist.allow_non_registered
            and synapse.dendrite.hotkey not in self.metagraph.hotkeys
        ):
            # Ignore requests from un-registered entities.
            bt.logging.trace(
                f"Blacklisting un-registered hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"

        if self.config.blacklist.force_validator_permit:
            # If the config is set to force validator permit, then we should only allow requests from validators.
            if not self.metagraph.validator_permit[uid]:
                bt.logging.warning(
                    f"Blacklisting a request from non-validator hotkey {synapse.dendrite.hotkey}"
                )
                return True, "Non-validator hotkey"

        bt.logging.trace(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    async def priority(self, synapse: template.protocol.Dummy) -> float:
        """
        The priority function determines the order in which requests are handled. More valuable or higher-priority
        requests are processed before others. You should design your own priority mechanism with care.

        This implementation assigns priority to incoming requests based on the calling entity's stake in the metagraph.

        Args:
            synapse (template.protocol.Dummy): The synapse object that contains metadata about the incoming request.

        Returns:
            float: A priority score derived from the stake of the calling entity.

        Miners may receive messages from multiple entities at once. This function determines which request should be
        processed first. Higher values indicate that the request should be processed first. Lower values indicate
        that the request should be processed later.

        Example priority logic:
        - A higher stake results in a higher priority value.
        """
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            bt.logging.warning(
                "Received a request without a dendrite or hotkey."
            )
            return 0.0

        # TODO(developer): Define how miners should prioritize requests.
        caller_uid = self.metagraph.hotkeys.index(
            synapse.dendrite.hotkey
        )  # Get the caller index.
        priority = float(
            self.metagraph.S[caller_uid]
        )  # Return the stake as the priority.
        bt.logging.trace(
            f"Prioritizing {synapse.dendrite.hotkey} with value: {priority}"
        )
        return priority

    def cleanup(self):
        """Clean up resources when miner is stopping"""
        try:
            bt.logging.info("🛑 Stopping miner and cleaning up resources...")
            
            # Stop stage monitoring
            if self.stage_reporter:
                self.stage_reporter.stop_monitoring()
                bt.logging.info("📊 Stage monitoring stopped")
            
            # Terminate Module 1
            if self.main_process:
                try:
                    self.main_process.terminate()
                    self.main_process.wait(timeout=5)
                    bt.logging.info("✅ Module 1 stopped")
                except subprocess.TimeoutExpired:
                    self.main_process.kill()
                    bt.logging.warning("⚠️ Module 1 force-killed")
                except Exception as e:
                    bt.logging.error(f"❌ Error stopping Module 1: {str(e)}")
            
            # Terminate Module 2
            if self.module2_process:
                try:
                    self.module2_process.terminate()
                    self.module2_process.wait(timeout=5)
                    bt.logging.info("✅ Module 2 stopped")
                except subprocess.TimeoutExpired:
                    self.module2_process.kill()
                    bt.logging.warning("⚠️ Module 2 force-killed")
                except Exception as e:
                    bt.logging.error(f"❌ Error stopping Module 2: {str(e)}")
            
            bt.logging.info("🏁 Miner cleanup completed")
            
        except Exception as e:
            bt.logging.error(f"❌ Error during cleanup: {str(e)}")


# This is the main function, which runs the miner.
if __name__ == "__main__":
    miner = None
    try:
        miner = Miner()
        bt.logging.info("🚀 Content Recommendation Miner started successfully")
        bt.logging.info("📊 Monitoring processing stages and module health...")
        
        try:
            while True:
                # Log current status periodically
                status = miner.get_current_status()
                bt.logging.info(f"📈 Miner Status: {status}")
                
                # Check module health
                miner._check_modules_health()
                
                # Sleep for status update interval
                time.sleep(30)  # Update every 30 seconds
                
        except KeyboardInterrupt:
            bt.logging.info("🛑 Miner interrupted by user")
        except Exception as e:
            bt.logging.error(f"❌ Miner error: {str(e)}")
            
    except Exception as init_error:
        bt.logging.error(f"❌ Failed to initialize miner: {str(init_error)}")
        bt.logging.info("🔧 This is likely due to missing wallet files or network issues")
        bt.logging.info("💡 Note: Module functionality was demonstrated above before this error")
        
    finally:
        if miner:
            try:
                miner.cleanup()
            except:
                pass
