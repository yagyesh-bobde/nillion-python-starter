import asyncio
import py_nillion_client as nillion
import os
from py_nillion_client import NodeKey, UserKey
from dotenv import load_dotenv
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey
from nillion_python_helpers import get_quote_and_pay, create_nillion_client, create_payments_config

home = os.getenv("HOME")
load_dotenv(f"{home}/.config/nillion/nillion-devnet.env")

async def main():
    # Environment setup
    cluster_id = os.getenv("NILLION_CLUSTER_ID")
    grpc_endpoint = os.getenv("NILLION_NILCHAIN_GRPC")
    chain_id = os.getenv("NILLION_NILCHAIN_CHAIN_ID")
    
    print(f"Cluster ID: {cluster_id}")
    print(f"GRPC Endpoint: {grpc_endpoint}")
    print(f"Chain ID: {chain_id}")

    # Create client
    seed = "voting_system_seed"
    client = create_nillion_client(
        UserKey.from_seed(seed),
        NodeKey.from_seed(seed),
    )
    print(f"Client created successfully. Party ID: {client.party_id}")

    # Setup payment configuration
    payments_config = create_payments_config(chain_id, grpc_endpoint)
    payments_client = LedgerClient(payments_config)
    payments_wallet = LocalWallet(
        PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
        prefix="nillion",
    )
    print("Payment configuration set up successfully")

    # Define a simple voting program
    voting_program_name = "simple_voting"
    program_mir_path = f"../nada_quickstart_programs/target/main.nada.bin"
    
    # Pay to store the program
    try:
        receipt_store_program = await get_quote_and_pay(
            client,
            nillion.Operation.store_program(program_mir_path),
            payments_wallet,
            payments_client,
            cluster_id,
        )
        print("Payment for storing program successful")
    except Exception as e:
        print(f"Error in payment for storing program: {str(e)}")
        return

    # Store voting program in the network
    try:
        print(f"Storing program in the network: {voting_program_name}")
        program_id = await client.store_program(
            cluster_id, voting_program_name, program_mir_path, receipt_store_program
        )
        print(f"Program stored successfully. Program ID: {program_id}")
    except Exception as e:
        print(f"Error storing program: {str(e)}")
        return

    # Set permissions for the client to compute on the program
    permissions = nillion.Permissions.default_for_user(client.user_id)
    permissions.add_compute_permissions({client.user_id: {program_id}})

    # Prepare for voting (simulated)
    votes = {
        "vote_1": nillion.SecretInteger(1),
        "vote_2": nillion.SecretInteger(0),
        "vote_3": nillion.SecretInteger(1)
    }
    compute_time_secrets = nillion.NadaValues(votes)

    # Pay for computation
    try:
        receipt_compute = await get_quote_and_pay(
            client,
            nillion.Operation.compute(program_id, compute_time_secrets),
            payments_wallet,
            payments_client,
            cluster_id,
        )
        print("Payment for computation successful")
    except Exception as e:
        print(f"Error in payment for computation: {str(e)}")
        return

    # Perform computation
    try:
        compute_bindings = nillion.ProgramBindings(program_id)
        compute_bindings.add_output_party("VotingSystem", client.party_id)
        
        compute_id = await client.compute(
            cluster_id,
            compute_bindings,
            [],  # No stored secrets
            compute_time_secrets,
            receipt_compute,
        )
        print(f"Computation initiated. Compute ID: {compute_id}")
    except Exception as e:
        print(f"Error initiating computation: {str(e)}")
        return

    # Wait for and process the computation result
    try:
        compute_event = await client.next_compute_event()
        if isinstance(compute_event, nillion.ComputeFinishedEvent):
            print(f"Computation complete. Result: {compute_event.result.value}")
        else:
            print(f"Unexpected compute event: {compute_event}")
    except Exception as e:
        print(f"Error processing compute event: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
