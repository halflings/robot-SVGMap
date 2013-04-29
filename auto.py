# -*- coding: utf8 -*-

"""
    auto.py - The view shown when monitoring the car's autonomous movements
    on the map or doing simulations.
"""

from PySide import QtSvg
from PySide.QtGui import *
from PySide.QtCore import *

import widgets
import probability

from collections import deque
import math
import random

class AutoScene(QGraphicsScene):

    def __init__(self, car, parent=None):
        super(AutoScene, self).__init__(parent)
        # self.setDragMode(QGraphicsScene.ScrollHandDrag)

        self.x = 0
        self.y = 0

        # Car object model only
        self.car = car

        # Car graphic representation
        self.graphicCar = None

        # Map generated by parsing an svg file
        self.map = None

        # The last generated path
        self.path = None

        # Graphical representation of the last generated path
        self.graphicalPath = None

        # Heatmap, should be used for probabilities [WIP]
        self.particleFilter = None
        # ( initialized when pressing 'H' )

    def pathfinding(self, x, y):
        # We generate a path from the car to where we clicked and show it on the UI
        # We get the path from our 'map' object
        self.path = self.map.search((self.car.x, self.car.y), (x, y))

        if len(self.path) > 0:
            # We build a polyline graphic item
            painterPath = QPainterPath()
            painterPath.moveTo(self.path[0].x, self.path[0].y)
            for i in xrange(1, len(self.path)):
                painterPath.lineTo(self.path[i].x, self.path[i].y)

            # We set the path as the path to be shown on screen
            # self.graphicalPath.setPath(painterPath)

             # If a path is already shown on screen, we just update it with the new path
            if self.graphicalPath is not None:
                self.graphicalPath.setPath(painterPath)
            # Else, we create a new graphical path
            else:
                self.graphicalPath = QGraphicsPathItem(painterPath)
                self.graphicalPath.setZValue(-1)

                pen = QPen()
                pen.setColor(QColor(180, 200, 240))
                pen.setWidth(3)
                # pen.setCapStyle(Qt.RoundCap)
                pen.setMiterLimit(10)
                pen.setJoinStyle(Qt.RoundJoin)
                space = 4
                pen.setDashPattern([8, space, 1, space])
                self.graphicalPath.setPen(pen)
                self.graphicalPath.setOpacity(0.8)

                self.addItem(self.graphicalPath)

            # Calculating the animation speed
            totalLength = painterPath.length()
            pixelsPerSecond = 200.0
            totalDuration = 1000. * (totalLength / pixelsPerSecond)

            # Animating the car on the path
            self.animation = QParallelAnimationGroup()

            posAnim = QPropertyAnimation(self.car, "positionProperty")
            rotAnim = QPropertyAnimation(self.car, "angleProperty")

            posAnim.setDuration(totalDuration)
            rotAnim.setDuration(totalDuration)

            posAnim.setKeyValueAt(0, QPointF(self.car.x, self.car.y))
            rotAnim.setKeyValueAt(0, self.car.readAngle())

            nKeys = len(self.path) - 1
            angles = deque()
            angles.append(self.graphicCar.rotation())

            for i in xrange(1, len(self.path)):
                pt = self.path[i]
                lastPt = self.path[i-1]

                # Current angle calculus and format according to the trigonometric sens
                angle = math.pi - math.atan2(lastPt.y - pt.y, lastPt.x - pt.x)

                # We add the 'current angle' to the angles queue and calculate the mean
                angles.append(angle)
                meanAngle = sum(angles) / len(angles)

                # If we already have too many angles, we drop the oldest ones
                if len(angles) > 10:
                    angles.popleft()

                posAnim.setKeyValueAt(float(i)/nKeys, QPointF(pt.x, pt.y))
                rotAnim.setKeyValueAt(float(i)/nKeys, meanAngle)

            self.animation.addAnimation(rotAnim)
            self.animation.addAnimation(posAnim)

            self.animation.finished.connect(self.pathFinished)

            self.animation.start(QAbstractAnimation.DeleteWhenStopped)
            self.car.setMoving(True)

    def pathFinished(self):
    # Called when the car has arrived to the path's end
        self.car.setMoving(False)
        self.path = []
        self.graphicalPath.setPath(QPainterPath())

    def mousePressEvent(self, event):
        x, y = event.scenePos().x(), event.scenePos().y()

        self.pathfinding(x, y)

        super(AutoScene, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        x, y = event.scenePos().x(), event.scenePos().y()

        if not self.car.moving:
            # We calculate the angle (in radians) and convert it to the trigonometric referential
            angle = math.pi - math.atan2(self.car.y - y, self.car.x - x)

            self.car.setAngle(angle)

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_H:
            # Hiding/showing the particle filter
            self.heatmap.setVisible(not self.heatmap.isVisible())
        elif event.key() == Qt.Key_R:
            # Reseting the particle filter
            self.particleFilter.reset()
            self.heatmap.update()
        elif not self.car.moving:
            # Moving the car

            speed = 0
            deltaAngle = 0

            if event.key() == Qt.Key_Up or event.key() == Qt.Key_Z:
                speed = 20
            elif event.key() == Qt.Key_Down or event.key() == Qt.Key_S:
                speed = -20
            elif event.key() == Qt.Key_Right or event.key() == Qt.Key_D:
                deltaAngle = -math.pi/10
            elif event.key() == Qt.Key_Left or event.key() == Qt.Key_Q:
                deltaAngle = math.pi/10

            if speed != 0 or deltaAngle != 0:
                # Adding some noise to the displacement
                nSpeed = speed + random.gauss(0.0, self.car.displacement_noise)
                if speed != 0:
                    # Simulating car's deviation
                    deltaAngle += random.gauss(0.0, math.radians(self.car.rotation_noise))
                    self.car.move(nSpeed)
                    
                self.car.setAngle(self.car.angle + deltaAngle)

                if self.heatmap.isVisible():
                    # Noise on the car's current angle
                    noisyCarAngle = self.car.angle + random.gauss(0.0, math.radians(self.car.rotation_noise)) 
                    self.particleFilter.setAngle(noisyCarAngle)
                    self.particleFilter.move(speed)
                    self.particleFilter.sense(self.car.distance, noisyCarAngle)
                    self.particleFilter.resample()
                    self.heatmap.update()

                # Putting back the car into the map if it got out
                # x = min(max(0, self.car.x), self.map.width - 1)
                # y = min(max(0, self.car.y), self.map.height - 1)
                # self.car.setPosition(QPointF(x, y))

class AutoView(QGraphicsView):
    Native, OpenGL, Image = range(3)

    def __init__(self, car, parent=None):
        super(AutoView, self).__init__(parent)

        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        self.renderer = AutoView.OpenGL
        self.svgItem = None
        self.backgroundItem = None

        self.setScene(AutoScene(car=car, parent=self))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self.setBackgroundBrush(QImage("img/blueprintDark.png"))
        self.setCacheMode(QGraphicsView.CacheBackground)

        # Disabling scrollbars
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


    def openMap(self, svg_map):
        s = self.scene()

        # Reset the zoom factor
        self.factor = 1
        # Recreate a map tree by parsing the SVG
        s.map = svg_map
        s.path = None
        s.graphicalPath = None

        # We remove the current view from the car's model
        s.car.removeView(s.graphicCar)

        if self.backgroundItem:
            drawBackground = self.backgroundItem.isVisible()
        else:
            drawBackground = True

        s.clear()
        self.resetTransform

        # Graphic visualization of the SVG map
        self.svgItem = QtSvg.QGraphicsSvgItem(svg_map.path)
        self.svgItem.setFlags(QGraphicsItem.ItemClipsToShape)
        self.svgItem.setZValue(0)
        s.addItem(self.svgItem)

        # The svg item's dimensions:
        width, height = self.svgItem.boundingRect().width(), self.svgItem.boundingRect().height()

        # Background (blueprint image)
        self.backgroundItem = QGraphicsRectItem(self.svgItem.boundingRect())
        self.backgroundItem.setBrush(QImage("img/blueprint.png"))
        self.backgroundItem.setPen(QPen())
        self.backgroundItem.setVisible(drawBackground)
        self.backgroundItem.setZValue(-1)
        self.backgroundItem.setCacheMode(QGraphicsItem.ItemCoordinateCache)
        s.addItem(self.backgroundItem)

        # Shadow effect on the background
        # TODO : See why this is *so* slow when we zoom in ?
        # self.shadow = QGraphicsDropShadowEffect()
        # self.shadow.setBlurRadius(50)
        # self.shadow.setColor( QColor(20, 20, 40) )
        # self.shadow.setOffset(0, 0)
        # self.backgroundItem.setGraphicsEffect( self.shadow )

        # Title text
        self.titleItem = QGraphicsTextItem("INSAbot visualization UI")
        self.titleItem.setFont(QFont("Ubuntu-L.ttf", 35, QFont.Light))
        # 'Dirty' centering of the text
        self.titleItem.setPos(width/2 - self.titleItem.boundingRect().width()/2, 5)
        self.titleItem.setDefaultTextColor(QColor(210, 220, 250))
        s.addItem(self.titleItem)
        # Drop shadow on the text
        self.textShadow = QGraphicsDropShadowEffect()
        self.textShadow.setBlurRadius(3)
        self.textShadow.setColor(QColor(20, 20, 40))
        self.textShadow.setOffset(1, 1)
        self.titleItem.setGraphicsEffect(self.textShadow)

        # Car visualization
        s.car.map = s.map
        s.graphicCar = widgets.GraphicsCarItem(s.car)
        s.addItem(s.graphicCar)

        # Heatmap
        s.particleFilter = probability.ParticleFilter(car=s.car, map=s.map)
        s.heatmap = widgets.GraphicalParticleFilter(s.particleFilter)
        s.heatmap.setVisible(False)
        s.addItem(s.heatmap)

        self.x = 0
        self.y = 0

        self.updateScene()

    def updateScene(self):
        self.scene().setSceneRect(self.svgItem.boundingRect().adjusted(self.x-10, self.y-10, self.x+10, self.y+10))

    def setRenderer(self, renderer):
        self.renderer = renderer
        self.setViewport(QWidget())

    def setViewBackground(self, enable):
        if self.backgroundItem:
            self.backgroundItem.setVisible(enable)

    def setViewOutline(self, enable):
        if self.outlineItem:
            self.outlineItem.setVisible(enable)

    def wheelEvent(self, event):
        factor = 1.2**(event.delta() / 240.0)

        self.scale(factor, factor)

        event.accept()
