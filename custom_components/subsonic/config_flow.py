from typing import Any
import voluptuous as vol
from .const import DOMAIN, TITLE, LOGGER
from .subsonicApi import SubsonicApi
from homeassistant.core import callback
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry

class SubsonicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    async def validate_input(self, config: dict) -> bool:
        userAgent = "HomeAssistant"
        
        api = SubsonicApi(userAgent=userAgent, config=config)
        if not await api.ping():
            return False
        return True

    async def async_step_user(self, user_input=None, error=None):
        
        schema = {
            vol.Required("url"): str,
            vol.Required("user"): str,
            vol.Required("password"): str,
            vol.Required("app"): vol.In({
                "subsonic": "Subsonic",
                "navidrome": "Navidrome"
            }),
            vol.Optional("title", default=""): str,
        }

        if user_input is not None:
            app = user_input["app"]
            title = user_input["title"] if user_input["title"] != "" else TITLE[app]

            data = {
                "url": user_input["url"],
                "user": user_input["user"],
                "password": user_input["password"],
                "app": app,
                "title": title
            }

            options = { 
                "artists": True,
                "albums": True,
                "playlists": True,
                "genres": True,
                "radio": True,
            }

            if await self.validate_input(data):
                return self.async_create_entry(title=title, data=data, options=options)
            else:
                return self.async_show_form(step_id="user", data_schema=vol.Schema(schema), errors={"base": "cannot_connect"})

        return self.async_show_form(step_id="user", data_schema=vol.Schema(schema))
    
    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry):
        return SubsonicOptionsFlow(entry)
    
class SubsonicOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: ConfigEntry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=self.entry.title, 
                                            data=user_input)
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("artists", default=self.entry.options.get("artists", True)): bool,
                    vol.Optional("albums", default=self.entry.options.get("albums", True)): bool,
                    vol.Optional("playlists", default=self.entry.options.get("playlists", True)): bool,
                    vol.Optional("genres", default=self.entry.options.get("genres", True)): bool,
                    vol.Optional("radio", default=self.entry.options.get("radio", False)): bool,
                }
            ),
        )
        