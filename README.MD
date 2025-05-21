# Game project on python 🐍 (Version 0.5)

This project is an experimental game, which intends to lean new algorithms and working for fun.

## 📖 Summary

- [Purpose of this project](#Purpose-of-this-project)
- [How to make this work ?](#How-to-make-this-work-)
- [Credits](#Credits)
- [What's next ?](#Whats-next-)


## Purpose of this project
This project is an open world, auto-generated 2D game. The mandatory features are simplicity 
of the game and fast-processing game (optimized game, even in python 😁).

### What is planned ?
- The game is an infinite 2D world. It's limitations are on the north and the south. barriers 
must be placed at the top end and bottom of the map. The West and Est are infinite generated.
- Biomes are mostly defined by latitude.
- Each biome has its own gameplay characteristics. Some of them still have to be defined.
- The goal of the game is to explore the map from the north to th south. The farther 
the player goes to the south, the harder the gameplay becomes.
- This game must stay very simple, but it is inspired from Factorio gameplay. Most 
gameplay mechanics have to be defined. One of the objectives is to create something new
compares to others games.

### Features
Pygame is very bad optimized for games, especially when a lot of sprites are shown on the 
screen. This project uses pygame._sdl2 to render sprites with the GPU. Despite limitations
of PySDL2, this addon has been chosen compare to others such as RayLib because
PySDL2 is much easier to learn. This addon is also the most effective in terms of fps.

The project uses as least as possible framework, game engine, etc... Only pygame._sdl2 is 
massively used. The goal is to create most code of the application.
pygame._sdl2 has poor documentation. I may later extend its documentation.

## How to make this work ?
To run the game as a compiled project (.exe), you need:
- Running on Windows
- (Maybe later on Linux and MacOS)

To run the game as a python project, you need at least:
- Python 3.12
- PySDL2 (v0.9.17)
- numpy (v2.2.1)
- pillow (v11.1.0)
- pygame (v2.6.1)

Execute the App.py file to start the game.

## What's next ?
A lot of work is remaining. Most features have not even been thought, because most tasks
are on optimisation, reliability and the core of the application (map generation, sprites
display, thread handling, and so on...)

No element of gameplay will be added before this. The core of the app must be finished before. 

The multiplayer is not planned yet. This feature might be too complicated.


## Credits
[Arthur-M15](https://github.com/Arthur-M15/profile)

