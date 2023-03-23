import pymongo


client = pymongo.MongoClient(
    "mongodb+srv://spotGenes:dps82212201@serverlessinstance0.tfaa4sm.mongodb.net/test"
)

db = client.get_database("SpotifyGenetics")
print(db)
users = db.get_collection("users")
print(users)
users.insert_one({"name": "test"})
