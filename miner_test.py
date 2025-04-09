import bittensor as bt
from template.protocol import RecommendationSynapse

wallet = bt.wallet(name="miner", hotkey="default")
dendrite = bt.dendrite(wallet=wallet)
synapse = RecommendationSynapse(username="testuser")
response = dendrite.query("127.0.0.1:8091", synapse, timeout=10)
print(response)
