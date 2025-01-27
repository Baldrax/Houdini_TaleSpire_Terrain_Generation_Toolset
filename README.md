# Houdini_TaleSpire_Terrain_Generation_Toolset
A toolset to procedurally create terrain for TaleSpire in Houdini.

![TerrainGenerationExamples](https://user-images.githubusercontent.com/100365731/200086786-b029760e-56f0-46f3-9caf-729247d36fbe.png)

## About the Toolset
This is a set of tools to aid in the creation of [TaleSpire](https://talespire.com/) Terrain 
in [SideFX Software's Houdini](https://www.sidefx.com/products/houdini/). Houdini has a free "Apprentice" license 
available for non-commercial work.
It is designed to let creativity flow, you can use every aspect of Houdini to help you sculpt creations for 
TaleSpire by hand or procedurally. 
At its core these tools utilize the Heightfield features of Houdini to craft landscapes so if you are 
new to Houdini learning that aspect of the software is a good start.

Houdini is a node-based procedural system so the Toolset consist of a set of Houdini Nodes called
HDA's (Houdini Digital Assets)

### Overview Video
Feature overview video:

[<img src="https://user-images.githubusercontent.com/100365731/200082578-f8a54857-8b44-46fa-9ebf-432656713204.png">](https://www.youtube.com/watch?v=193IomvemaA)

### Tutorial Video's
For more instructional videos refer to the [Tutorials](https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset/wiki/Tutorials) page on the wiki.

### Current Nodes
#### TaleSpire_Terrain
The main node for managing a terrain project, this node contains subnetworks that allow a workspace to 
craft your terrain. It is also the main interface for setting up the terrain and exporting the final results.

#### TaleSpire_Object
This node is used to import a TaleSpire Tile, Prop or Slab for use in the system. It has controls over the 
placement of these objects in regard to how they interact with other nodes like TaleSpire_Tiler and TaleSpire_Scatter.
You can also export directly from this node, in case you just want to rotate or replace assets.

#### TaleSpire_Biome
This node defines a Biome which controls what TaleSpire Tiles and Props get put on to the terrain. It has 
subnetworks within for defining sets of objects, rules for placing Tiles and rules for placing/scattering Props.

#### TaleSpire_Tiler
This node is used within the TaleSpire_Biome node to define what areas specific sets of tiles are placed on the terrain.

#### TaleSpire_Scatter
This node is used to scatter props on to a heightfield terrain based on rules and masks. It can work inside a
TaleSpire_Biome node or externally if used with the new TaleSpire_Object_Set node.

#### TaleSpire_Copy
This node allows you to place assets on specific points fed in to the 1st input. It can work
inside or outside a biome. The 2nd input can be used to designate which objects to place on the 
points, as defined in a TaleSpire_Object_Set node.

#### TaleSpire_Object_Set
This node is a container for TaleSpire_Object nodes, it works similar to the objects network
in the TaleSpire_Biome node. This allows you to define sets of objects to use in nodes like 
TaleSpire_Scatter and TaleSpire_Copy allowing those nodes to work external from a Biome if desired.

#### TaleSpire_Export
This node can take the data from TaleSpire_Scatter and TaleSpire_Copy nodes and export them directly
to a slab or multi-slab without needing to set up a terrain.
Its feature set is currently limited but will eventually support all the features of the terrain nodes export.

#### TaleSpire_Fetch_Water
This node can be used in biomes to get the water level of the heightfield. It can return a mask as either a 0-1 
mask representing where water is and isn't, or a depth mask, which you can use to determine how far the current surface
is above or below the waterline.

#### TaleSpire_Set_Water_Level
This node can be used in the terrain edit network to set the water level, either from the water plane or from a 2nd
input which is a heightfield depicting the water level. This node is also used behind the scene to set the water level
if you don't do it explicitly.

#### TaleSpire_Preview
This node is used to preview the results at various points in the network, usually after a TS Copy/Scatter/Tiler node or
after merging the results of those nodes.

#### TaleSpire_Cavern_Helper
This is an object level node that allows you to input a floorplan layout of a cavern using the "Swamp Floor" 1x1 and/or 
2x2 floor tiles in TS. More detailed notes on this node can be found on the 
[wiki](https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset/wiki/TaleSpire_Cavern_Helper).

### NEW Nodes!
The following nodes are new as of v0.24.0-alpha and are considered Work In Progress.
Some features may be missing or broken.

#### TaleSpire_Heightfield_Mask_Distance
A useful heightfield based node to calculate a distance based off of the incoming mask.

#### TaleSpire_Heightfield_Pocket_Mask
Generates scattered pockets within a mask on a heightfield. Useful for sparse masks or pockets of items you want to 
scatter.

#### TaleSpire_Heightfield_Tile_Edge_Mask
Creates a mask around the edges of ground tiles. Useful for hiding the height transition between tiles.

#### TaleSpire_Heightfield_Remap
An alternative to the stock Houdini Heightfield Remap node that fixes a bug with ramps and allows for repetitive ramps.

## Installation
The installation instructions are available on the wiki.
* [Toolset Installation Instructions](https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset/wiki/Installation)


### Examples
#### Terrain
There is an example Houdini scene file included with this distribution `hip/examples/example_Forest_Gully.hipnc`.
It is best to copy this scene to an alternate location before running it as it needs to save local data. Alternately you 
can launch it and "Save As" to a working directory.

I recommend running through all the comments before attempting to resize the map from its 60x60 default since there are a 
few areas that may not work properly which are noted within the file.

#### Biomes
There is a scene file containing example biomes being used for development, more biomes will be available in
the future. `hip/examples/biomes.hipnc`

#### Geometric Shapes
This scene file demonstrates multiple ways to make geometric shapes like spiral staircases
brick smokestacks, towers, walls, tunnels and more.
`hip/examples/geometric_examples.hipnc`

### Better with Mods!
This tool supports use of a mod that allows multiple slab pastes at once. That's right, instead of laboriously hand 
placing hundreds of slabs you could do it all with a single click and paste.

To install and use the mods visit the wiki page:
* [Multi-Paste Feature](https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset/wiki/Multi-Paste-Feature)

## Contact
Join us on Discord to discuss the toolset, share work and inspiration and to get the latest news.

https://discord.gg/Wx54CAtz4H

### Attributions
The TaleSpire Slab Encoding/Decoding code was originally authored by LuPro 
at [LuPro/SlabelFish](https://github.com/LuPro/SlabelFish)
