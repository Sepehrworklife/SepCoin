from django.shortcuts import render
import datetime
import hashlib
import json
from django.http import JsonResponse, HttpResponse, HttpRequest
from uuid import uuid4
import socket
from urllib.parse import urlparse
from django.views.decorators.csrf import csrf_exempt


class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions= []
        self.create_block(nonce = 1, previous_hash = '0')
        self.nodes = set()



    def create_block(self, nonce, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'nonce': nonce,
            'previous_hash': previous_hash,
            'transations': self.transactions
        }
        self.transactions = []
        self.chain.append(block)
        return block



    def get_previous_block(self):
        return self.chain[-1]


    def proof_of_work(self, previous_nonce):
        new_nonce = 1
        check_nonce = False
        while check_nonce is False:
            hash_operation = hashlib.sha256(str(new_nonce**2 - previous_nonce**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_nonce = True
            else:
                new_nonce += 1
        return new_nonce


    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_nonce = previous_block['nonce']
            nonce = block['nonce']
            hash_operation = hashlib.sha256(str(nonce**2 - previous_nonce**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    def add_transaction(self, sender, receiver, amount, time):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'time': str(datetime.datetime.now())
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1


    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status.code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
            if longest_chain:
                self.chain = longest_chain
                return True
        return False



#Crating blockchain
blockchain = Blockchain()
node_address = str(uuid4()).replace('-', '')
root_node = 'e36f0158f0aed45b3bc755dc52ed4560d'

def mine_block(request):
    if request.method == 'GET':
        previous_block = blockchain.get_previous_block()
        previous_nonce = previous_block['nonce']
        nonce = blockchain.proof_of_work(previous_nonce)
        previous_hash = blockchain.hash(previous_block)
        blockchain.add_transaction(sender = root_node, receiver = node_address, amount = 1.5, time = str(datetime.datetime.now()))
        block = blockchain.create_block(nonce, previous_hash)
        response = {'message': 'Congrajulation you just mined a block!',
                    'index': block['index'],
                    'timestamp': block['timestamp'],
                    'nonce': block['nonce'],
                    'previous_hash': block['previous_hash'],
                    'transactions': block['transactions']}
        return JsonResponse(response)

#Getting the full Chain
def get_chain(request):
    if request.method == 'GET':
        response = {'chain': blockchain.chain,
                    'length': len(blockchain.chain)}
        return JsonResponse(response)

def is_valid(request):
    if request.method == 'GET':
        is_valid = blockchain.is_chain_valid(blockchain.chain)
        if is_valid:
            response = {'message': 'All good, The BlockChain is Valid'}
        else:
            reponse = {'message': 'We have a Problem, the blockchain is not valid'}
    return JsonResponse(response)

def add_transaction(request):
    if request.method == 'POST':
        received_json = json.loads(request.body)
        transaction_keys = ['sender', 'receiver', 'amount', 'time']
        if not all(key in received_json for key in transaction_keys):
            return 'Some elements of the transaction are missing!'
        index = blockchain.add_transaction(received_json['sender'], received_json['receiver'],received_json['amount'], received_json['time'])
        response = {'message' : f'This transaction will be added to Block {index}'}
    return JsonResponse(response)

@csrf_exempt
def connect_node(request):
    if request.method == "POST":
        received_json = json.loads(request.body)
        nodes = received_json.get('nodes')
        if nodes is None:
            return "No Node", HttpResponse(status=400)
        for node in nodes:
            blockchain.add_node(node)
        response = {'message': 'All the nodes are connected, The coin blockchain contain the following nodes:',
                    'total_nodes': list(blockchain.nodes)}
    return JsonResponse(response)


def replace_chain(request):
    if request.method == 'POST':
        is_chain_replaced = blockchain.replace_chain()
        if is_chain_replaced:
            response = {'message': ' The nodes had diffrent chain so the longest one is the one!',
                        'new_chain': blockchain.chain}
        else:
            response = {'message': 'All good, the chain is the largest one',
                        'acual_chain': blockchain.chain}
    return JsonResponse(response)
