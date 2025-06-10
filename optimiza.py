import re
from solcx import compile_source, install_solc
from web3 import Web3
import networkx as nx
import pprint
import sys


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



def analyze_solidity_file(file_path):
    if not file_path.endswith(".sol"):
        print("Error: Please provide a Solidity (.sol) file.")
        return
    else:
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
          
            
            compiled_sol = compile_source(content, solc_version="0.8.0")
            ast = compiled_sol['<stdin>:SumLoopExample']['ast']['nodes']
            
            cfg = traverse_ast_iteratively(ast)
            print(cfg)
            if cfg:

                optimized_code = optimize_loops(content)

                print("Optimized Solidity Code:\n", optimized_code)
                w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
                assert w3.is_connected(), "Ethereum node connection failed."
                print("etooo")
                account = w3.eth.accounts[0]
                print(w3)
                contract_address, contract_abi = compile_and_deploy(optimized_code, w3, account)
                print(f"Contract deployed at address: {contract_address}")

                measure_gas_usage(w3, contract_address, contract_abi, "calculateSum")

                
                print("Une boocle")
                
                
            else:
                print("Pas de boocle dans ce contract")

            
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <solidity_file.sol>")
    else:
        analyze_solidity_file(sys.argv[1])
