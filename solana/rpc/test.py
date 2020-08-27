from api import Client

http_client = Client("https://api.mainnet-beta.solana.com")
# marketAddress = PublicKey('6ibUz1BqSD3f8XP4wEGwoRH4YbYRZ1KDZBeXmrp3KosD')
print(http_client.is_connected())
print(http_client.get_balance("6ibUz1BqSD3f8XP4wEGwoRH4YbYRZ1KDZBeXmrp3KosD"))
