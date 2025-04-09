# neurons/miner.py
import time
import logging
import argparse
import bittensor as bt
from template.base.utils.miner import BaseMinerNeuron
from template.base.utils.main import main as recommendation_main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Miner(BaseMinerNeuron):
    def __init__(self, config=None):
        super().__init__(config=config)
        logger.info("Miner initialized with config: %s", self.config)

    def step(self):
        try:
            logger.info("Starting recommendation pipeline step: %d", self.step_count)
            result = recommendation_main()
            if result["success"]:
                logger.info("Pipeline completed successfully. Processed %d datasets", result["processed"])
            else:
                logger.error("Pipeline failed after processing %d datasets", result["processed"])
        except Exception as e:
            logger.error("Error in pipeline step: %s", str(e))
            import traceback
            logger.error(traceback.format_exc())

def main():
    parser = argparse.ArgumentParser(description="Run the Bittensor miner.")
    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    bt.axon.add_args(parser)  # Add axon args for ip/port
    bt.logging.add_args(parser)
    parser.add_argument("--netuid", type=int, default=2, help="Network UID")  # Explicitly add netuid
    config = bt.config(parser)
    # Ensure subtensor settings
    config.subtensor.network = "local"
    config.subtensor.chain_endpoint = "ws://127.0.0.1:9944"
    logger.info("Parsed config: %s", config)
    with Miner(config=config) as miner:
        while True:
            bt.logging.info(f"Miner running... {time.time()}")
            time.sleep(5)

if __name__ == "__main__":
    main()