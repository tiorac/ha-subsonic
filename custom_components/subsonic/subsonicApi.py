import socket
import aiohttp
import asyncio
import hashlib
import secrets
from typing import Self
from aiohttp import hdrs
from .const import LOGGER
from dataclasses import dataclass
from .xmlHelper import getAttributes, \
    getTagAttributes, \
    getTagsAttributesToList, \
    getTagsTexts
from homeassistant.config_entries import ConfigEntry


@dataclass
class SubsonicApi:

    userAgent: str
    entry: ConfigEntry
    requestTimeout: float = 8.0
    apiVersion: str = "1.16.1"
    session: aiohttp.client.ClientSession | None = None
        
    @property
    def url(self) -> str:
        return self.__getProperty("url")
    
    @property
    def user(self) -> str:
        return self.__getProperty("user")
    
    @property
    def password(self) -> str:
        return self.__getProperty("password")

    @property
    def salt(self) -> str:
        return secrets.token_hex(5)
    
    def __getProperty(self, property, dafultValue=None):
        if self.entry is None:
            return dafultValue
        
        if self.entry.data is None:
            return dafultValue
        
        if property not in self.entry.data:
            return dafultValue
        
        return self.entry.data[property]

    def __generateToken(self, password: str, salt: str) -> str:
        return hashlib.md5((password + salt).encode()).hexdigest()

    def __getSession(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._close_session = True
        
        return self.session
    
    def __getRequestParams(self, params):
        s = self.salt

        p = {
            "u": self.user,
            "t": self.__generateToken(self.password, s),
            "s": s,
            "v": self.apiVersion,
            "c": "HomeAssistant"
        }

        if params is not None:
            p.update(params)

        return p

    async def __request(self, method, path, params=None):
        url = f"{self.url}/rest/{path}.view"
        p = self.__getRequestParams(params)

        headers = {
            hdrs.USER_AGENT: self.userAgent
        }

        s = self.__getSession()

        try:
            async with asyncio.timeout(self.requestTimeout):
                response = await s.request(method, 
                                        url, 
                                        headers=headers, 
                                        params=p,
                                        raise_for_status=True)
                
                content_type = response.headers.get("Content-Type", "")

                if "application/json" in content_type:
                    return await response.json()
                else:
                    text = await response.text()
                    return text
                
        except asyncio.TimeoutError as exception:
            LOGGER.error("Timeout error")
            raise Exception("Timeout error") from exception
        
        except (aiohttp.ClientError, socket.gaierror) as exception:
            LOGGER.error("Error connecting to Navidrome")
            raise Exception("Error connecting to Navidrome") from exception

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()    
    
    async def ping(self) -> bool:
        pingResponse = await self.__request("GET", "ping")

        ping = getAttributes(pingResponse)
        LOGGER.info(f"Ping: {ping}")

        if "status" not in ping:
            return False
        
        return ping["status"] == "ok"
    
    async def getRadioStations(self) -> dict:
        radioResponse = await self.__request("GET", "getInternetRadioStations")
        radios = getTagsAttributesToList(radioResponse, "internetRadioStation")

        return radios
    
    async def getAlbums(self) -> list:
        params = {
            "type": "alphabeticalByName"
        }
        albumsResponse = await self.__request("GET", "getAlbumList2", params)
        albums = getTagsAttributesToList(albumsResponse, "album")

        return albums
    
    async def getAlbum(self, id: str) -> dict:
        params = {
            "id": id
        }
        albumResponse = await self.__request("GET", "getAlbum", params)
        album = getTagAttributes(albumResponse, "album")

        songs = getTagsAttributesToList(albumResponse, "song")
        album["songs"] = songs

        return album

    async def getPlaylists(self) -> list:
        playlistsResponse = await self.__request("GET", "getPlaylists")
        playlists = getTagsAttributesToList(playlistsResponse, "playlist")

        return playlists
    
    async def getPlaylist(self, id: str) -> dict:
        params = {
            "id": id
        }
        playlistResponse = await self.__request("GET", "getPlaylist", params)
        playlist = getTagAttributes(playlistResponse, "playlist")

        songs = getTagsAttributesToList(playlistResponse, "entry")
        playlist["songs"] = songs

        return playlist

    async def getGenres(self) -> list[str]:
        genresResponse = await self.__request("GET", "getGenres")
        genres = getTagsTexts(genresResponse, "genre")
        return genres
    
    async def getSongsByGenre(self, id: str) -> list:
        params = {
            "genre": id
        }
        songsResponse = await self.__request("GET", "getSongsByGenre", params)
        songs = getTagsAttributesToList(songsResponse, "song")

        return songs
    
    async def getArtists(self) -> list:
        artistsResponse = await self.__request("GET", "getArtists")
        artists = getTagsAttributesToList(artistsResponse, "artist")

        return artists
    
    async def getArtist(self, id: str) -> dict:
        params = {
            "id": id
        }
        
        artistResponse = await self.__request("GET", "getArtist", params)
        artist = getTagAttributes(artistResponse, "artist")

        albums = getTagsAttributesToList(artistResponse, "album")
        artist["albums"] = albums

        return artist

    async def getSong(self, id: str) -> dict:
        params = {
            "id": id
        }
        songResponse = await self.__request("GET", "getSong", params)
        song = getTagAttributes(songResponse, "song")

        return song

    def getCoverArtUrl(self, id: str) -> str:
        params = {
            "id": id
        }

        p = self.__getRequestParams(params)

        query = "&".join([f"{k}={v}" for k, v in p.items()])
        url = f"{self.url}/rest/getCoverArt.view?{query}"

        return url

    def getSongStreamUrl(self, id: str) -> str:
        params = {
            "id": id
        }

        p = self.__getRequestParams(params)

        query = "&".join([f"{k}={v}" for k, v in p.items()])
        url = f"{self.url}/rest/stream.view?{query}"

        return url


    async def __aenter__(self) -> Self:
        return self
    
    async def __aexit__(self, *_exc_info: object) -> None:
        await self.close()
