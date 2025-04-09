import bittensor

def main():
    # Setup config
    config = bittensor.subtensor.config()
    config.subtensor.network = "local"
    config.subtensor.chain_endpoint = "ws://127.0.0.1:9944"

    # Create subtensor object with updated config
    sub = bittensor.subtensor(config=config)

    print("✅ Connected to local subtensor node")

    # Fetch and print current block number
    block_number = sub.block
    print("Current block:", block_number)

    # Get subnet metadata
    subnets_info = sub.all_subnets()
    print("Netuids on chain:", subnets_info)

    # Loop through each subnet and fetch metagraph info
    for info in subnets_info:
        netuid = info.netuid
        try:
            metagraph = sub.metagraph(netuid=netuid)
            print(f"→ NetUID {netuid}: {len(metagraph.hotkeys)} hotkeys")
        except Exception as e:
            print(f"⚠️ Error fetching metagraph for netuid {netuid}: {e}")

if __name__ == "__main__":
    main()
