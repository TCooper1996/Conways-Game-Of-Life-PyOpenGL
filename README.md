# Conways-Game-Of-Life-PyOpenGL
This is a very simple implementation of Conway's Game of Life using Python, QT5 and OpenGL
The user can click and drag on tiles individually or drag the mouse over tiles while holding the left mouse button to activate cells.
Right clicking and dragging removes cells. Clicking the play button at the bottom starts the simulation. Pressing the button again pauses the simulation. There are two sliders at the bottom, the top of which controls the speed at which generation progress, wheras the bottom adjusts the zoom. 

NOTE: Clicking on a tile alone will not toggle it; you must click and drag the mouse just a bit for it to register.


This application requires numpy, pyOpenGL and PyQt5
To run it:

clone it
```
git clone https://github.com/TCooper1996/Conways-Game-Of-Life-PyOpenGL/
cd Conways-Game-Of-Life-PyOpenGL
```

install dependencies
```
sudo pip3 install numpy
```

run
```
python3 Main.py
```
