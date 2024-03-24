LANGUAGES = {
    "en": {
        "artists": "Artists",
        "albums": "Albums",
        "tracks": "Tracks",
        "playlists": "Playlists",
        "radios": "Radios",
        "genres": "Genres"
    },
    "pt-BR": {
        "artists": "Artistas",
        "albums": "Álbuns",
        "tracks": "Músicas",
        "playlists": "Playlists",
        "radios": "Rádios",
        "genres": "Gêneros"
    }
}

def getTranslation(language: str, key: str) -> str:
    if language not in LANGUAGES:
        language = "en"

    if key not in LANGUAGES[language]:
        return key

    return LANGUAGES[language][key]