import xml.etree.ElementTree as ET
from .const import LOGGER

def getTagsAttributesToList(xml: str, tag: str) -> list:
    xml = xml.replace("xmlns=\"http://subsonic.org/restapi\"", "")
    root = ET.fromstring(xml)
    tagsItens = root.findall(f'.//{tag}')
    itens = [{attr: item.get(attr) for attr in item.keys()} for item in tagsItens]

    return itens

def getTagAttributes(xml: str, tag: str) -> dict:
    itens = getTagsAttributesToList(xml, tag)

    if len(itens) == 0:
        return {}
    
    return itens[0]

def getAttributes(xml: str) -> dict:
    root = ET.fromstring(xml)
    return {attr: root.get(attr) for attr in root.keys()}

def getTagsTexts(xml: str, tag: str) -> list[str]:
    xml = xml.replace("xmlns=\"http://subsonic.org/restapi\"", "")
    root = ET.fromstring(xml)
    tagsItens = root.findall(f'.//{tag}')
    itens = [item.text for item in tagsItens]

    return itens