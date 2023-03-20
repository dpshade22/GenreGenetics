from src.UserGenes import UserGenes

userGenes = UserGenes()
userGenes.authenticate()
userGenes.initTracksDF()

# print(userGenes.recentTracksDF.head())
print(userGenes.topTracksDF.head())
userGenes.topTracksDF.to_csv("topTracks.csv")
