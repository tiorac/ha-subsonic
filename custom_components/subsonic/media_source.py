from homeassistant.components.media_player import BrowseError, MediaClass, MediaType
from homeassistant.components.media_source.error import Unresolvable
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, LOGGER
from .subsonicApi import SubsonicApi
from .translation import getTranslation


class SubsonicSource(MediaSource):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(DOMAIN)
        self.hass = hass
        self.entry = entry
        self.__api = None
        self.name = self.title

    @property
    def title(self) -> str:
        return "Subsonic" if self.entry is None else self.entry.title

    @property
    def artists(self) -> bool:
        return self.__getOption("artists", True)
    
    @property
    def albums(self) -> bool:
        return self.__getOption("albums", True)
    
    @property
    def playlists(self) -> bool:
        return self.__getOption("playlists", True)
    
    @property
    def favorites(self) -> bool:
        return self.__getOption("favorites", True)

    @property
    def genres(self) -> bool:
        return self.__getOption("genres", True)

    @property
    def radio(self) -> bool:
        return self.__getOption("radio", False)

    @property
    def api(self) -> SubsonicApi:
        if self.__api is None:
            self.__api = self.hass.data[DOMAIN]

        return self.__api

    def __getProperty(self, property, dafultValue=None):
        if (self.entry is not None
            and self.entry.data is not None
            and property in self.entry.data):
            return self.entry.data[property]

        if isinstance(dafultValue, Exception):
            raise dafultValue
        
        return dafultValue
    
    def __getOption(self, option, defaultValue=None):
        if (self.entry is not None
            and self.entry.options is not None
            and option in self.entry.options):
            return self.entry.options[option]

        if isinstance(defaultValue, Exception):
            raise defaultValue

        return defaultValue
    
    def __getTranslation(self, key: str) -> str:
        lang = self.hass.config.language
        return getTranslation(lang, key)



    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        if item.identifier.startswith("radio/"):
            return await self.async_resolve_radio(item.identifier)
        
        if item.identifier.startswith("song/"):
            return await self.async_resolve_song(item.identifier)
        
        raise Unresolvable("Can't resolve media item")
    
    async def async_resolve_radio(self, identifier: str) -> PlayMedia:
        radioId = identifier.replace("radio/", "")
        radios = await self.api.getRadioStations()
        radio = next((r for r in radios if r["id"] == radioId), None)

        if radio is None:
            raise Unresolvable(f"Radio {radioId} not found")

        return PlayMedia(radio["streamUrl"], "audio/mpeg")

    async def async_resolve_song(self, identifier: str) -> PlayMedia:
        songId = identifier.replace("song/", "")
        song = await self.api.getSong(songId)
        contentType = song["contentType"] if "contentType" in song else "audio/mpeg"

        streamUrl = self.api.getSongStreamUrl(songId)

        return PlayMedia(streamUrl, contentType)



    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:

        identifier = item.identifier or ""

        if identifier.startswith("browser/"):
            return await self.async_browser_item(item.identifier.replace("browser/", ""))
        elif identifier.startswith("album/"):
            return await self.async_list_songs_album(identifier.replace("album/", ""))
        elif identifier.startswith("playlist/"):
            return await self.async_list_songs_playlist(identifier.replace("playlist/", ""))
        elif identifier.startswith("genre/"):
            return await self.async_list_songs_genre(identifier.replace("genre/", ""))
        elif identifier.startswith("artist/"):
            return await self.async_list_albums_artist(identifier.replace("artist/", ""))


        return await self.async_browse_root()
    
    async def async_browse_root(self) -> BrowseMediaSource:

        childrens = []
        lang = self.__getTranslation("subsonic")

        if self.artists:
            childrens.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="browser/artists",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MUSIC,
                    title=self.__getTranslation("artists"),
                    can_play=False,
                    can_expand=True,
                    # thumbnail="https://avatars.githubusercontent.com/u/26692192?s=256"
                )
            )

        if self.albums:
            childrens.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="browser/albums",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MUSIC,
                    title=self.__getTranslation("albums"),
                    can_play=False,
                    can_expand=True,
                )
            )

        if self.playlists:
            childrens.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="browser/playlist",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MUSIC,
                    title=self.__getTranslation("playlists"),
                    can_play=False,
                    can_expand=True,
                )
            )

        if self.radio:
            childrens.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="browser/radio",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MUSIC,
                    title=self.__getTranslation("radios"),
                    can_play=False,
                    can_expand=True,
                )
            )

        """
        if self.favorites:
            childrens.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="browser/favorites",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MUSIC,
                    title=self.__getTranslation("favorites"),
                    can_play=False,
                    can_expand=True,
                )
            )
        """

        if self.genres:
            childrens.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="browser/genres",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MUSIC,
                    title=self.__getTranslation("genres"),
                    can_play=False,
                    can_expand=True,
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.CHANNEL,
            media_content_type=MediaType.MUSIC,
            title=self.title,
            can_play=False,
            can_expand=True,
            thumbnail="https://avatars.githubusercontent.com/u/26692192?s=256",
            children_media_class=MediaClass.DIRECTORY,
            children=childrens,
        )
    
    async def async_browser_item(self, identifier: str) -> BrowseMediaSource:
        title = identifier
        childrens = []
        content_type = MediaType.MUSIC
        children_type = MediaClass.DIRECTORY

        if identifier == "radio":
            title = self.__getTranslation("radios")
            childrens = await self.async_list_radios()
            children_type = MediaClass.MUSIC
        elif identifier == "albums":
            title = self.__getTranslation("albums")
            childrens = await self.async_list_albums()
            children_type = MediaClass.ALBUM
        elif identifier == "playlist":
            title = self.__getTranslation("playlists")
            childrens = await self.async_list_playlists()
            children_type = MediaClass.PLAYLIST
        elif identifier == "genres":
            title = self.__getTranslation("genres")
            childrens = await self.async_list_genres()
            children_type = MediaClass.GENRE
        elif identifier == "artists":
            title = self.__getTranslation("artists")
            childrens = await self.async_list_artists()
            children_type = MediaClass.ARTIST

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=identifier,
            media_class=MediaClass.DIRECTORY,
            media_content_type=content_type,
            title=title,
            can_play=False,
            can_expand=True,
            children_media_class=children_type,
            children=childrens,
        )
    
    async def async_list_radios(self) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []
        radios = await self.api.getRadioStations()

        for radio in radios:
            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"radio/{radio['id']}",
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=radio["name"],
                    can_play=True,
                    can_expand=False,
                )
            )

        return items
    
    async def async_list_albums(self) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []
        albums = await self.api.getAlbums()

        for album in albums:
            coveart = None

            if ("coverArt" in album
                and album["coverArt"] is not None
                and album["coverArt"] != ""):
                coveart = self.api.getCoverArtUrl(album["coverArt"])

            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"album/{album['id']}",
                    media_class=MediaClass.ALBUM,
                    media_content_type=MediaType.ALBUM,
                    title=album["name"],
                    can_play=False,
                    can_expand=True,
                    thumbnail=coveart,
                )
            )

        return items
    
    async def async_list_playlists(self) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []
        playlists = await self.api.getPlaylists()

        for playlist in playlists:
            coveart = None

            if ("coverArt" in playlist
                and playlist["coverArt"] is not None
                and playlist["coverArt"] != ""):
                coveart = self.api.getCoverArtUrl(playlist["coverArt"])

            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"playlist/{playlist['id']}",
                    media_class=MediaClass.PLAYLIST,
                    media_content_type=MediaType.PLAYLIST,
                    title=playlist["name"],
                    can_play=False,
                    can_expand=True,
                    thumbnail=coveart
                )
            )

        return items
    
    async def async_list_genres(self) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []
        genres = await self.api.getGenres()

        for genre in genres:
            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"genre/{genre}",
                    media_class=MediaClass.GENRE,
                    media_content_type=MediaType.MUSIC,
                    title=genre,
                    can_play=False,
                    can_expand=True,
                )
            )

        return items

    async def async_list_artists(self) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []

        artists = await self.api.getArtists()

        for artist in artists:
            coverArt = None

            if ("coverArt" in artist
                and artist["coverArt"] is not None
                and artist["coverArt"] != ""):
                coverArt = self.api.getCoverArtUrl(artist["coverArt"])

            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"artist/{artist['id']}",
                    media_class=MediaClass.ARTIST,
                    media_content_type=MediaType.MUSIC,
                    title=artist["name"],
                    can_play=False,
                    can_expand=True,
                    thumbnail=coverArt
                )
            )

        return items

        

    async def async_list_songs_album(self, albumId: str) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []
        album = await self.api.getAlbum(albumId)

        for song in album["songs"]:
            coveart = None

            if ("coverArt" in album
                and album["coverArt"] is not None
                and album["coverArt"] != ""):
                coveart = self.api.getCoverArtUrl(album["coverArt"])

            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"song/{song['id']}",
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=song["title"],
                    can_play=True,
                    can_expand=False,
                    thumbnail=coveart
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"album/{albumId}",
            media_class=MediaClass.ALBUM,
            media_content_type=MediaType.ALBUM,
            title=album["name"],
            can_play=False,
            can_expand=True,
            thumbnail=coveart,
            children_media_class=MediaClass.MUSIC,
            children=items,
        )
    
    async def async_list_songs_playlist(self, playlistId: str) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []

        playlist = await self.api.getPlaylist(playlistId)
        coveart = None

        if ("coverArt" in playlist
            and playlist["coverArt"] is not None
            and playlist["coverArt"] != ""):
            coveart = self.api.getCoverArtUrl(playlist["coverArt"])

        for song in playlist["songs"]:
            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"song/{song['id']}",
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=song["title"],
                    can_play=True,
                    can_expand=False,
                    thumbnail=coveart
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"playlist/{playlistId}",
            media_class=MediaClass.PLAYLIST,
            media_content_type=MediaType.PLAYLIST,
            title=playlist["name"],
            can_play=False,
            can_expand=True,
            thumbnail=coveart,
            children_media_class=MediaClass.MUSIC,
            children=items,
        )
    
    async def async_list_songs_genre(self, genreId: str) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []

        songs = await self.api.getSongsByGenre(genreId)

        for song in songs:
            coveart = None

            if ("coverArt" in song
                and song["coverArt"] is not None
                and song["coverArt"] != ""):
                coveart = self.api.getCoverArtUrl(song["coverArt"])

            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"song/{song['id']}",
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=song["title"],
                    can_play=True,
                    can_expand=False,
                    thumbnail=coveart
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"genre/{genreId}",
            media_class=MediaClass.GENRE,
            media_content_type=MediaType.MUSIC,
            title=genreId,
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.MUSIC,
            children=items,
        )
        
    async def async_list_albums_artist(self, artistId: str) -> list[BrowseMediaSource]:
        items: list[BrowseMediaSource] = []

        artist = await self.api.getArtist(artistId)
        coveart = None

        if ("coverArt" in artist
            and artist["coverArt"] is not None
            and artist["coverArt"] != ""):
            coveart = self.api.getCoverArtUrl(artist["coverArt"])

        for album in artist["albums"]:
            albumCoveart = None

            if ("coverArt" in album
                and album["coverArt"] is not None
                and album["coverArt"] != ""):
                albumCoveart = self.api.getCoverArtUrl(album["coverArt"])

            items.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"album/{album['id']}",
                    media_class=MediaClass.ALBUM,
                    media_content_type=MediaType.ALBUM,
                    title=album["name"],
                    can_play=False,
                    can_expand=True,
                    thumbnail=albumCoveart
                )
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"artist/{artistId}",
            media_class=MediaClass.ARTIST,
            media_content_type=MediaType.MUSIC,
            title=artist["name"],
            can_play=False,
            can_expand=True,
            thumbnail=coveart,
            children_media_class=MediaClass.ALBUM,
            children=items,
        )

async def async_get_media_source(hass: HomeAssistant) -> SubsonicSource:
    LOGGER.warning("async_get_media_source")
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    return SubsonicSource(hass, entry)