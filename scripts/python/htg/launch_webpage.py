"""Launches a webpage in the users browser."""
import sys
import webbrowser


urls = {
    "github": "https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset",
    "wiki": "https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset/wiki",
    "discord": "https://discord.com/invite/Wx54CAtz4H"
}

webbrowser.open(urls[sys.argv[1]], new=0, autoraise=True)
