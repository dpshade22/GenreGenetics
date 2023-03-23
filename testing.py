import pymongo

client = pymongo.MongoClient("mongodb+srv://spotifyGeneticsApp:Aad5EcWJj7LDLHxC?@serverlessinstance0.tfaa4sm.mongodb.net/?retryWrites=true&w=majority")

print(client)
db = client.get_database('SpotifyGenetics')
print(db)
users = db.get_collection('users')
print(users)
users.insert_one({'name': 'test'})
