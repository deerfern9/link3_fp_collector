import threading
import time
import requests
from web3 import Web3
from eth_account.messages import encode_defunct

buy_tickets = 'n'       # write "y" so that the program automatically buys tickets
threads_count = 20      # number of threads
delay = 1               # delay between threads_count
bsc_rpc = "https://bsc.blockpi.network/v1/rpc/public"

# commenting = not claiming fp
ids_to_claim = {
    '[NFT] Subscribe a Profile': 'b5e4d3c0-619e-44cf-8203-7273877e67b3',
    '[NFT] Collect an EssenceNFT': '6bf4ac10-8b82-45ea-bdf7-fa94ecbd124b',
    '[FREE] Comment': '9d825ed6-a60a-45a6-93b0-020f00eb16f0',
    '[FREE] Like a Post': '466653ef-73f2-4ce3-ac8b-a3f70a00a14c',
    '[FREE] Create a Post': '65370e8f-fd69-41fa-ab9c-3be635ec4802',
    '[FREE] Follow a Profile': 'cb3901ad-529e-47f0-bb79-586dd75360c7',
    # 'Referral': 'c6a57cf2-d4e8-4676-97d7-5d32b07526ed',
}

w3 = Web3(Web3.HTTPProvider(bsc_rpc))

headers = {
    'authority': 'api.cyberconnect.dev',
    'accept': '*/*',
    'accept-language': 'en-GB,en;q=0.9,uk-UA;q=0.8,uk;q=0.7,ru-RU;q=0.6,ru;q=0.5,en-US;q=0.4',
    'content-type': 'application/json',
    'origin': 'https://link3.to',
    'referer': 'https://link3.to/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
}

if buy_tickets == 'y':
    reward_json_data = {
        'query': '\n    query getLoyaltyProgramRewards($handle: String!, $filter: LoyaltyProgramRewardFilter) {\n  loyaltyProgram(handle: $handle) {\n    rewards(filter: $filter) {\n      id\n      title\n      type\n      drawTime\n      startTime\n      endTime\n      rewards {\n        name\n        image\n        count\n      }\n      requirement {\n        points\n        type\n      }\n      totalTickets\n      sidePoolTickets\n      mainPoolTickets\n      userReward {\n        ownedTickets\n        wonRewards {\n          name\n          image\n          count\n        }\n      }\n      totalWinners\n    }\n  }\n}\n    ',
        'variables': {
            'handle': 'cyberconnect',
            'filter': 'REWARD_AVAILABLE',
        },
        'operationName': 'getLoyaltyProgramRewards',
    }

    reward_id = requests.post('https://api.cyberconnect.dev/profile/', headers=headers, json=reward_json_data).json()['data']['loyaltyProgram']['rewards'][0]['id']


def read_file(filename):
    result = []
    with open(filename, 'r') as file:
        for tmp in file.readlines():
            result.append(tmp.replace('\n', ''))

    return result


def write_to_file(filename, text):
    with open(filename, 'a') as file:
        file.write(f'{text}\n')


def get_nonce(address, proxy):
    json_data = {
        'query': '\n    mutation nonce($address: EVMAddress!) {\n  nonce(request: {address: $address}) {\n    status\n    message\n    data\n  }\n}\n    ',
        'variables': {
            'address': address,
        },
        'operationName': 'nonce',
    }

    response = requests.post('https://api.cyberconnect.dev/profile/', headers=headers, json=json_data, proxies=proxy)
    nonce = response.json()['data']['nonce']['data']
    return nonce


def sign_signature(private_key, message):
    message_hash = encode_defunct(text=message)
    signed_message = w3.eth.account.sign_message(message_hash, private_key)

    signature = signed_message.signature.hex()
    return signature


def get_auth_token(address, message, signature, proxy):
    json_data = {
        'query': '\n    mutation login($address: EVMAddress!, $signature: String!, $signedMessage: String!, $token: String, $isEIP1271: Boolean, $chainId: Int) {\n  login(\n    request: {address: $address, signature: $signature, signedMessage: $signedMessage, token: $token, isEIP1271: $isEIP1271, chainId: $chainId}\n  ) {\n    status\n    message\n    data {\n      id\n      privateInfo {\n        address\n        accessToken\n        kolStatus\n      }\n    }\n  }\n}\n    ',
        'variables': {
            'signedMessage': message,
            'token': '',
            'address': address,
            'chainId': 56,
            'signature': signature,
            'isEIP1271': False,
        },
        'operationName': 'login',
    }

    resp = requests.post('https://api.cyberconnect.dev/profile/', headers=headers, json=json_data, proxies=proxy).json()
    try:
        token = resp['data']['login']['data']['privateInfo']['accessToken']
        return token
    except Exception as e:
        print(resp, e)


def claim_fp(auth, private, proxy):
    er_proxy = proxy['http'].split("//")[1].split("'")[0]
    result = 0
    claim_fp_headers = {
        'authority': 'api.cyberconnect.dev',
        'accept': '*/*',
        'authorization': auth,
        'content-type': 'application/json',
        'origin': 'https://link3.to',
        'referer': 'https://link3.to/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }
    for name, task_id in ids_to_claim.items():
        json_data = {
            'query': '\n    mutation claimPoints($id: ID!) {\n  claimPoints(input: {engagementId: $id}) {\n    status\n  }\n}\n    ',
            'variables': {
                'id': task_id,
            },
            'operationName': 'claimPoints',
        }
        try:
            response = requests.post('https://api.cyberconnect.dev/profile/', headers=claim_fp_headers, json=json_data, proxies=proxy)
        except Exception as e:
            print(e)
            time.sleep(1)
            claim_fp(auth, private, proxy)
            exit()
        resp = response.json()['data']['claimPoints']['status']
        print(f'[{private}] {name}: {resp}\n', end='')
        if resp == 'NOT_QUALIFIED':
            result = f'{private};{er_proxy};{name}'
            write_to_file('not claimed fp.txt', result)
    return result


def buy_ticket(auth, private, num, proxy):
    if num >= 1:
        buy_ticket_headers = {
            'authority': 'api.cyberconnect.dev',
            'accept': '*/*',
            'authorization': auth,
            'content-type': 'application/json',
            'origin': 'https://link3.to',
            'referer': 'https://link3.to/',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        }

        json_data = {
            'query': '\n    mutation consumePoints($id: ID!, $count: Int!) {\n  consumePoints(input: {rewardId: $id, count: $count}) {\n    status\n  }\n}\n    ',
            'variables': {
                'id': reward_id,
                'count': num,
            },
            'operationName': 'consumePoints',
        }

        response = requests.post('https://api.cyberconnect.dev/profile/', headers=buy_ticket_headers, json=json_data, proxies=proxy).json()
        result = response['data']['consumePoints']['status']
        return result
    else:
        return private


def point_history(auth, proxy):
    point_headers = {
        'authority': 'api.cyberconnect.dev',
        'accept': '*/*',
        'authorization': auth,
        'content-type': 'application/json',
        'origin': 'https://link3.to',
        'referer': 'https://link3.to/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    json_data = {
        'query': '\n    query getLoyaltyMemberPassStatus($handle: String!) {\n  loyaltyProgram(handle: $handle) {\n    membershipPass {\n      totalPoints\n      availablePoints\n      joinedAt\n      level\n      previousLevelPoints\n      nextLevelPoints\n    }\n    rewardsCount\n  }\n}\n    ',
        'variables': {
            'handle': 'cyberconnect',
        },
        'operationName': 'getLoyaltyMemberPassStatus',
    }

    response = requests.post('https://api.cyberconnect.dev/profile/', headers=point_headers, json=json_data, proxies=proxy)
    points = response.json()['data']['loyaltyProgram']['membershipPass']['availablePoints']
    return points


def get_num_of_bought_tickets(authorization, proxy, address):
    num_of_bought_headers = {
        'authority': 'api.cyberconnect.dev',
        'accept': '*/*',
        'authorization': authorization,
        'content-type': 'application/json',
        'origin': 'https://link3.to',
        'referer': 'https://link3.to/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    json_data = {
        'query': '\n    query getLoyaltyProgramRewards($handle: String!, $filter: LoyaltyProgramRewardFilter) {\n  loyaltyProgram(handle: $handle) {\n    rewards(filter: $filter) {\n      id\n      title\n      type\n      drawTime\n      startTime\n      endTime\n      rewards {\n        name\n        image\n        count\n      }\n      requirement {\n        points\n        type\n      }\n      totalTickets\n      sidePoolTickets\n      mainPoolTickets\n      userReward {\n        ownedTickets\n        wonRewards {\n          name\n          image\n          count\n        }\n      }\n      totalWinners\n    }\n  }\n}\n    ',
        'variables': {
            'handle': 'cyberconnect',
            'filter': 'REWARD_AVAILABLE',
        },
        'operationName': 'getLoyaltyProgramRewards',
    }

    response = requests.post('https://api.cyberconnect.dev/profile/', headers=num_of_bought_headers, json=json_data, proxies=proxy).json()
    bought_tickets = response['data']['loyaltyProgram']['rewards'][0]['userReward']['ownedTickets']
    print(f'{address};{bought_tickets}\n', end='')
    write_to_file('bought tickets.txt', f'{address};{bought_tickets}')


def main(private, proxy):
    address = w3.eth.account.from_key(private).address
    proxy = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    nonce = get_nonce(address, proxy)
    message = f'''link3.to wants you to sign in with your Ethereum account:\n{address}\n\n\nURI: https://link3.to\nVersion: 1\nChain ID: 56\nNonce: {nonce}\nIssued At: 2023-03-19T14:04:18.580Z\nExpiration Time: 2023-04-02T14:04:18.580Z\nNot Before: 2023-03-19T14:04:18.580Z'''
    sign = sign_signature(private, message)
    authorization = get_auth_token(address, message, sign, proxy)

    claim_fp(authorization, private, proxy)

    if buy_tickets == 'y':
        try:
            num_of_fp = point_history(authorization, proxy)
            num_of_tickets_to_buy = num_of_fp//500
        except:
            num_of_fp = num_of_tickets_to_buy = 0

        if num_of_tickets_to_buy > 0:
            write_to_file('bought tickets.txt', f'{address};{num_of_fp};{num_of_tickets_to_buy}')
            if (t := buy_ticket(authorization, private, num_of_tickets_to_buy, proxy)) == 'SUCCESS':
                print(f'[{private if len(private) == 66 else "0x" + private}] Ticket purchase status: {t}; Bought tickets: {num_of_tickets_to_buy}; FP remained: {num_of_fp % 500}\n', end='')
            else:
                if t == private:
                    print(f'[{private if len(private) == 66 else "0x" + private}] Ticket purchase status: Not enough fp for ticket; FP remained: {num_of_fp}\n', end='')
                else:
                    print(f'[{private if len(private) == 66 else "0x" + private}] Ticket purchase status: {t}; FP remained: {num_of_fp}\n', end='')


def start():
    privates = read_file('privates.txt')
    proxies = read_file('proxies.txt')
    i = 0

    for j in range(int(len(privates)/threads_count)+1):
        for k in range(threads_count):
            try:
                threading.Thread(target=main, args=(privates[i], proxies[i])).start()
                i += 1
            except:
                pass
        time.sleep(1)


if __name__ == '__main__':
    start()
