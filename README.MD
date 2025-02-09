# Game project on python 🐍

This project is an experimental game, which intends to lean new algorithm and working for fun.

## 📖 Summary

- [Purpose of this project](#Purpose-of-this-project)
- [How to make this work](#How-to-make-this-work)


## Purpose of this project
This project is an open world, auto-generated 2D game. The mandatory features are simplicity 
of the game and fast-processing game (optimized game, even in python 😁).

### What's is planned 
- The game is an infinite 2D world. It's limitations are on the north and the south. barriers 
must be placed at the top end and bottom of the map. The West and Est are infinite generated.
- Biomes are mostly defined by latitude.
- Each biome has its own gameplay characteristics. Some of them still have to be defined.
- The goal of the game is to explore the map from the north to th south. The farther 
the player goes to the south, the harder the gameplay becomes.
- This game must stay very simple, but it is inspired from Factorio gameplay. Most 
gameplay mechanics need to be defined. One of the objectives is to create something new
compares to others games.

### Features
Pygame is very bad optimized for games, especially when a lot of sprites are shown on the 
screen. This project uses pygame._sdl2 the render sprites with GPU. Despite limitations
of PySDL2, this addon has been chosen compare to others such as RayLib because
PySDL2 is much easier to learn. This addon is also the most effective in terms of fps.

The project uses at least as possible framework. Only pygame._sdl2 is massively used.

## How to make this work
To run the game as a compiled project, you need:
- Python 3.12

To run the game as a python project, you need at least:
- Python 3.12
- PySDL2 (v0.9.17)
- numpy (v2.2.1)
- pillow (v11.1.0)
- pygame (v2.6.1)
- (pip)

Execute the App.py file to start the game.


## Developers
[Arthur-M15](https://github.com/Arthur-M15/profile)

