# template/protocol.py
import typing
import bittensor as bt

class RecommendationSynapse(bt.Synapse):
    username: str
    results_limit: int = 10
    output: typing.Optional[dict] = None

    def deserialize(self) -> dict:
        return self.output