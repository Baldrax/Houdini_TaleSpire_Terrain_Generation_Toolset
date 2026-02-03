"""Launches a webpage in the users browser."""
import sys
import webbrowser

dco = "Wx54CAtz4H"
dc = "_uNGYt3XRfy_"

urls = {
    "github": "https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset",
    "wiki": "https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset/wiki",
    "discord": f"https://discord.com/invite/{dc.strip('_')}"
}

webbrowser.open(urls[sys.argv[1]], new=0, autoraise=True)
