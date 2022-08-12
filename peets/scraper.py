from peets.entities.movie import Movie
import tmdbsimple as tmdb
tmdb.API_KEY = "42dd58312a5ca6dd8339b6674e484320"

api = tmdb.Movies(603)
response = api.info()
