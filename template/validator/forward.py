# template/validator/forward.py
import time
import bittensor as bt

from template.protocol import RecommendationSynapse
from template.validator.reward import get_rewards
from template.utils.uids import get_random_uids

async def forward(self):
    """
    The forward function is called by the validator every time step.

    It is responsible for querying the network and scoring the responses.

    Args:
        self (:obj:`bittensor.neuron.Neuron`): The neuron object containing the validator's state.
    """
    # Select random miner UIDs to query
    # TODO(developer): Customize how miners are selected if needed (e.g., based on stake or performance)
    miner_uids = get_random_uids(self, k=self.config.neuron.sample_size)

    # Query the selected miners using the dendrite client
    responses = await self.dendrite(
        # List of axons to query, derived from the metagraph
        axons=[self.metagraph.axons[uid] for uid in miner_uids],
        # Construct a recommendation query with a sample username and results limit
        # TODO(developer): Replace 'humansofny' with a dynamic username selection logic if desired
        synapse=RecommendationSynapse(username="humansofny", results_limit=10),
        # Deserialize the responses (calls RecommendationSynapse.deserialize())
        deserialize=True,
    )

    # Score the responses (optional, depending on your reward logic)
    # TODO(developer): Implement reward logic in get_rewards if needed
    rewards = get_rewards(self, responses=responses, uids=miner_uids)

    # Update validator state (e.g., step counter)
    self.step += 1

    # Return responses for logging or further processing (optional)
    return responses