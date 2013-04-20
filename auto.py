"""
    auto.py - The view shown when monitoring the car's autonomous movements
    on the map or doing simulations.
"""

from PySide import QtCore, QtGui, QtSvg

import engine

import svg
import heatmap

from collections import deque
import math

class AutoScene(QtGui.QGraphicsScene):

    def __init__(self, parent=None):
        super(AutoScene, self).__init__(parent)
        #self.setDragMode(QtGui.QGraphicsScene.ScrollHandDrag)

        self.x = 0
        self.y =0

        # Car object (model + graphics informations)
        self.car = None

        # Map generated by parsing an svg file
        self.map = None

        # The last generated path
        self.path = None

        # Graphical representation of the last generated path
        self.graphicalPath = None
        # self.graphicalPath = QtGui.QGraphicsPathItem( QtGui.QPainterPath() )
        # self.graphicalPath.setZValue(-1)


        # self.graphicalPath.setPen(pen)

        # self.addItem( self.graphicalPath )

        # Not used (as of 29/03), should be a graphic item for the car's "ray"
        self.ray = None

        # Heatmap, should be used for probabilities [WIP]
        self.heatmap = None
        # ( initialized when pressing 'H' )

    def mousePressEvent(self, event):
        x, y = event.scenePos().x(), event.scenePos().y()

        # If the car doesn't exist yet, we place it where we clicked
        if not self.car:
            self.car = engine.Car(self.map, x, y)
            self.addItem(self.car)

            #Fade in animation
            self.animation = QtCore.QPropertyAnimation(self.car, "opacity")
            self.animation.setDuration(300)
            self.animation.setStartValue( 0.0 )
            self.animation.setEndValue( 1.0 )
            self.animation.start( QtCore.QAbstractAnimation.DeleteWhenStopped )

        # If the car already exists, we generate a path from the car to where we clicked
        # and show it on the UI
        else:
            #We get the path from our 'map' object
            self.path = self.map.search((self.car.x(), self.car.y()), (x,y))

            if len(self.path) > 0:
                # We build a polyline graphic item
                painterPath = QtGui.QPainterPath()
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
                    self.graphicalPath = QtGui.QGraphicsPathItem(painterPath)
                    self.graphicalPath.setZValue(-1)

                    pen = QtGui.QPen()
                    pen.setColor(QtGui.QColor(180, 200, 240))
                    pen.setWidth(3)
                    # pen.setCapStyle(QtCore.Qt.RoundCap)
                    pen.setMiterLimit(10)
                    pen.setJoinStyle(QtCore.Qt.RoundJoin)
                    space = 4
                    pen.setDashPattern([8, space, 1, space] )
                    self.graphicalPath.setPen(pen)
                    self.graphicalPath.setOpacity(0.8)

                    self.addItem( self.graphicalPath )

                # Calculating the animation speed
                totalLength = painterPath.length()
                pixelsPerSecond = 200.0
                totalDuration = 1000. * (totalLength / pixelsPerSecond)

                # Animating the car on the path
                self.animation = QtCore.QParallelAnimationGroup();

                self.posAnim = QtCore.QPropertyAnimation(self.car, "pos")
                self.rotationAnim = QtCore.QPropertyAnimation(self.car, "angleProperty")

                self.posAnim.setDuration(totalDuration)
                self.rotationAnim.setDuration(totalDuration)

                self.posAnim.setKeyValueAt(0, self.car.pos())
                self.rotationAnim.setKeyValueAt(0, self.car.rotation())

                nKeys = len(self.path) - 1
                angles = deque()
                angles.append(self.car.rotation())

                for i in xrange(1, len(self.path)):
                    pt = self.path[i]
                    lastPt = self.path[i-1]

                    # Current angle calculus and format according to the trigonometric sens
                    angle = math.pi - math.atan2(lastPt.y - pt.y, lastPt.x - pt.x)
                    if angle > math.pi:
                        angle = angle - 2*math.pi

                    # We add the 'current angle' to the angles queue and calculate the mean
                    angles.append(angle)
                    meanAngle = sum(angles) / len(angles)

                    # If we already have many angles, with drop the oldest one
                    if len(angles) > 15:
                        angles.popleft()

                    self.posAnim.setKeyValueAt(float(i)/nKeys, QtCore.QPointF(pt.x, pt.y))
                    self.rotationAnim.setKeyValueAt(float(i)/nKeys, meanAngle)

                self.animation.addAnimation(self.rotationAnim)
                self.animation.addAnimation(self.posAnim)

                self.animation.finished.connect(self.pathFinished)

                self.animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
                self.car.moving = True

        super(AutoScene,self).mousePressEvent(event)

    # Called when the car have arrived to the path's end
    def pathFinished(self):
        self.car.moving = False
        self.path =  []
        self.graphicalPath.setPath(QtGui.QPainterPath())

    def mouseMoveEvent(self, event):
        x, y = event.scenePos().x(), event.scenePos().y()

        if self.car and not self.car.moving:
            #We calculate the angle (in radians) and convert it to the trigonometric referential
            angle = math.pi - math.atan2(self.car.y() - y, self.car.x() - x)
            if angle > math.pi:
                angle = angle - 2*math.pi

            self.car.setAngle(angle)

    def keyPressEvent(self, event):

        # Moving the car
        speed = 20
        if self.car and not self.car.moving:
            if event.key()==QtCore.Qt.Key_Up or event.key()==QtCore.Qt.Key_Z:
                self.car.move(speed)
            elif event.key()==QtCore.Qt.Key_Down or event.key()==QtCore.Qt.Key_S:
                self.car.move(-speed)

        # Heatmap
        if event.key() == QtCore.Qt.Key_H:
            self.heatmap = heatmap.Heatmap(self.map.width ,  self.map.height)
            self.graphicalHeatmap = heatmap.GraphicalHeatmap(self.heatmap)
            self.graphicalHeatmap.setZValue(-1)
            self.addItem( self.graphicalHeatmap )

class AutoView(QtGui.QGraphicsView):
    Native, OpenGL, Image = range(3)

    def __init__(self, parent=None):
        super(AutoView, self).__init__(parent)

        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)

        self.renderer = AutoView.OpenGL
        self.svgItem = None
        self.backgroundItem = None
        self.outlineItem = None
        self.image = QtGui.QImage()

        self.setScene(AutoScene(self))
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)

        self.setBackgroundBrush(QtGui.QImage("img/blueprintDark.png"))
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)


    def openFile(self, svg_file):
        if not svg_file.exists():
            return

        s = self.scene()

        #Reset the zoom factor
        self.factor = 1
        #Reset the car
        s.car = None
        #Recreate a map tree by parsing the SVG
        s.map = svg.SvgTree(svg_file.fileName())
        s.path = None
        s.graphicalPath = None

        if self.backgroundItem:
            drawBackground = self.backgroundItem.isVisible()
        else:
            drawBackground = False

        # if self.outlineItem:
        #     drawOutline = self.outlineItem.isVisible()
        # else:
        #     drawOutline = True

        s.clear()
        self.resetTransform

        # View containg the SVG map
        self.svgItem = QtSvg.QGraphicsSvgItem(svg_file.fileName())
        self.svgItem.setFlags(QtGui.QGraphicsItem.ItemClipsToShape)
        self.svgItem.setCacheMode(QtGui.QGraphicsItem.NoCache)
        self.svgItem.setZValue(0)
        s.addItem(self.svgItem)

        # Title text
        self.titleItem = QtGui.QGraphicsTextItem("INSAbot visualization UI")
        self.titleItem.setFont(QtGui.QFont("Ubuntu-L.ttf", 35, QtGui.QFont.Light))
        # 'Dirty' centering of the text
        self.titleItem.setPos(self.svgItem.boundingRect().width()/2 - self.titleItem.boundingRect().width()/2, 5)
        self.titleItem.setDefaultTextColor(QtGui.QColor(210, 220, 250))
        s.addItem(self.titleItem)
        # Drop shadow on the text
        self.textShadow = QtGui.QGraphicsDropShadowEffect()
        self.textShadow.setBlurRadius(3)
        self.textShadow.setColor( QtGui.QColor(20, 20, 40) )
        self.textShadow.setOffset(1, 1)
        self.titleItem.setGraphicsEffect( self.textShadow )

        # Background (blueprint image)
        self.backgroundItem = QtGui.QGraphicsRectItem(self.svgItem.boundingRect())
        self.backgroundItem.setBrush( QtGui.QImage("img/blueprint.png") )
        self.backgroundItem.setPen(QtGui.QPen())
        self.backgroundItem.setVisible(not drawBackground)
        self.backgroundItem.setZValue(-1)
        s.addItem(self.backgroundItem)

        #Shadow effect on the background
        self.shadow = QtGui.QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(50)
        self.shadow.setColor( QtGui.QColor(20, 20, 40) )
        self.shadow.setOffset(0, 0)
        self.backgroundItem.setGraphicsEffect( self.shadow )

        # # A dashed (outline) of the SVG map
        # self.outlineItem = QtGui.QGraphicsRectItem(self.svgItem.boundingRect())
        # outline = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.DashDotLine)
        # outline.setCosmetic(True)
        # self.outlineItem.setPen(outline)
        # self.outlineItem.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        # self.outlineItem.setVisible(drawOutline)
        # self.outlineItem.setZValue(1)
        # s.addItem(self.outlineItem)

        self.x = 0
        self.y = 0

        self.updateScene()

    def updateScene(self):
        self.scene().setSceneRect(self.svgItem.boundingRect().adjusted(self.x-10, self.y-10, self.x+10, self.y+10))

    def setRenderer(self, renderer):
        self.renderer = renderer
        self.setViewport(QtGui.QWidget())

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
