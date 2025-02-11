import re
from solcx import compile_source, install_solc
from web3 import Web3
import networkx as nx
import pprint
import re
install_solc("0.8.0")

def load_contract(filepath):
    with open(filepath, "r") as file:
        return file.read()

def traverse_ast_iteratively(ast):
    cfg = []  # Initialize directed graph for CFG
    current_function = None  # Track the current function being traversed
    nodes_to_visit = ast[:]  # Stack for iterative traversal
    
    # print(nodes_to_visit)
    while nodes_to_visit:
        node = nodes_to_visit.pop()        
        if isinstance(node, dict):
            # Check if this node is a FunctionCall
            if node.get('nodeType') == 'ForStatement':
                cfg.append("for") 
            for key in node:
                if isinstance(node[key], list):
                    nodes_to_visit.extend(node[key])
                elif isinstance(node[key], dict):
                    nodes_to_visit.append(node[key])

    return cfg

def optimize_loops(sol_code):
    
    def optimize_for_loop(match):
        loop_header = match.group(1)
        loop_body = match.group(2)
        optimized_body = re.sub(
            r"(\w+\.\w+\(.*?\))", 
            r"let cached = \1; // Cached external call\ncached",  
            loop_body,
        )
        return f"for ({loop_header}) {{ {optimized_body} }}"

    # Apply optimizations to for loops
    optimized_code = re.sub(r"for\s*\((.*?)\)\s*\{(.*?)\}", optimize_for_loop, sol_code, flags=re.DOTALL)
    return optimized_code

def compile_and_deploy(sol_code, w3, account):
    """
    Compiles and deploys the optimized Solidity contract using Web3.
    """
    compiled_sol = compile_source(sol_code, solc_version="0.8.0")
    contract_interface = compiled_sol["<stdin>:SumLoopExample"]

    # Deploy contract
    OptimizedContract = w3.eth.contract(
        abi=contract_interface["abi"], bytecode=contract_interface["bin"]
    )
    tx_hash = OptimizedContract.constructor().transact({"from": account})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt.contractAddress, contract_interface["abi"]

# Step 5: Measure Gas Usage
def measure_gas_usage(w3, contract_address, abi, function_name):
    """
    Measures gas usage of a specific contract function.
    """
    contract = w3.eth.contract(address=contract_address, abi=abi)
    gas_estimate = contract.functions[function_name]().estimate_gas({"from": w3.eth.accounts[0]})
    print(f"Gas estimate for function '{function_name}': {gas_estimate}")

# Connect to Ethereum Node
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
assert w3.is_connected(), "Ethereum node connection failed."

# Load, analyze, optimize, and deploy the contract
sol_file = "solidity.sol"  # Replace with your Solidity file path
original_code = load_contract(sol_file)



compiled_sol = compile_source(original_code, solc_version="0.8.0")

# updated_code = re.sub(r'(\bi)\s*\+\+', r'++\1', compiled_sol)


ast = compiled_sol['<stdin>:SumLoopExample']['ast']['nodes']

#récuperation avec cfg pour vérifier les boocles for
cfg = traverse_ast_iteratively(ast)

print(cfg)

if cfg:


    optimized_code = optimize_loops(original_code)


    # code = optimize_loops(original_code)

    print("Optimized Solidity Code:\n", optimized_code)

    account = w3.eth.accounts[0]
    print(w3)
    contract_address, contract_abi = compile_and_deploy(optimized_code, w3, account)
    print(f"Contract deployed at address: {contract_address}")

    measure_gas_usage(w3, contract_address, contract_abi, "calculateSum")

    
    print("Une boocle")
else:
    print("Pas de boocle dans ce contract")


