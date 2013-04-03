Important
==========

This is a work in progress and the code base can change very radically. Don't except (for now) something working out of the box  !

Carosif - "SVGmap-robot"
============

A Python front-end for robot localization (and other uses) using SVG for the maps and Qt for the UI.
This includes a *really* basic SVG parser, a pathfinder (A\*),  some "collision" methods to calculate the distance to the closest obstacle and the visualization of the robot's movements and a 'heatmap' of the probabilities.

UPDATE March 2013
=======================

This now also includes a server/client made to be used in a Raspberry Pi connected to the Arduino controlling the car. Check how that work out in a 'joystick controlled' mode :

https://www.youtube.com/watch?v=rbX47X8HtGU

Dependencies
============

Python 2.7
Qt and PySide
Numpy
Pyserial
