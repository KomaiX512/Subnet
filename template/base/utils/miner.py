# template/base/utils/miner.py
import time
import threading
import bittensor as bt

class BaseMinerNeuron:
    def __init__(self, config=None):
        self.config = config or bt.subtensor.config()
        if not hasattr(self.config, 'axon'):
            self.config.axon = bt.AxonConfig()
        self.config.axon.ip = self.config.axon.ip or '0.0.0.0'
        self.config.axon.port = self.config.axon.port or 8091
        self.wallet = bt.wallet(config=self.config)
        self.subtensor = bt.subtensor(config=self.config)
        try:
            self.metagraph = self.subtensor.metagraph(self.config.netuid)
            bt.logging.info(f"Metagraph synced for netuid: {self.config.netuid}")
        except Exception as e:
            bt.logging.error(f"Failed to sync metagraph for netuid {self.config.netuid}: {e}")
            self.metagraph = None
        self.block = self.subtensor.block
        self.axon = bt.axon(wallet=self.wallet, config=self.config)
        bt.logging.info(f"Axon created: {self.axon}")
        self.should_exit = False
        self.is_running = False
        self.thread = None
        self.step_count = 0

    def sync(self):
        self.block = self.subtensor.block
        if self.metagraph:
            self.metagraph.sync(subtensor=self.subtensor)
            uid = self.metagraph.uids[0].item() if self.metagraph.uids.size > 0 else 'N/A'  # Convert tensor to scalar
            bt.logging.debug(f"Synced: Block={self.block}, UID={uid}")

    def step(self):
        raise NotImplementedError("Subclass must implement step()")

    def run(self):
        self.sync()
        bt.logging.info(f"Serving miner axon {self.axon} on network: {self.config.subtensor.chain_endpoint} with netuid: {self.config.netuid}")
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)
        self.axon.start()
        bt.logging.info(f"Miner starting at block: {self.block}")
        while not self.should_exit:
            if self.metagraph and self.block - self.metagraph.last_update[self.metagraph.uids[0]] >= 100:
                self.sync()
                self.step_count += 1
                self.step()
            time.sleep(5)

    def run_in_background_thread(self):
        if not self.is_running:
            bt.logging.debug("Starting miner in background thread.")
            self.should_exit = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.is_running = True
            bt.logging.debug("Started")

    def stop_run_thread(self):
        if self.is_running:
            bt.logging.debug("Stopping miner in background thread.")
            self.should_exit = True
            if self.thread is not None:
                self.thread.join(5)
            self.is_running = False
            bt.logging.debug("Stopped")

    def __enter__(self):
        self.run_in_background_thread()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_run_thread()