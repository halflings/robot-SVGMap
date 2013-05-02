"""
    astar.py - A* algorithm implementation
"""

from math import sqrt, atan2
import scipy
import scipy.signal

class Cell(object):

    def __init__(self, x, y, reachable=True):
        self.reachable = reachable
        self.x = int(x)
        self.y = int(y)
        self.parent = None

        # Cost to move to an adjacent cell
        self.g = 0

        # Estimated distance to the goal (Manhattan distance)
        self.h = 0

        # Total "score" : h + g
        self.f = 0

    def __eq__(self, cell):
        return self.x == cell.x and self.y == cell.y and self.reachable == cell.reachable

    def distance(self, cell):
        return sqrt((self.x - cell.x)**2 + (self.y - cell.y)**2)

    def heuristicDistance(self, cell):
        return self.manhattanDistance(cell)

    def manhattanDistance(self, cell):
        return abs(self.x - cell.x) + abs(self.y - cell.y)

    def diagonalDistance(self, cell):

        xDist = abs(self.x - cell.x)
        yDist = abs(self.y - cell.y)

        if xDist > yDist:
            return 1.4 * yDist + (xDist - yDist)
        else:
            return 1.4 * xDist + (yDist - xDist)

    def path(self):
        """ Returns the path that led to this cell """
        resPath = [self]
        cell = self
        while cell.parent != None:
            resPath.append(cell.parent)
            cell = cell.parent

        # Returning the reversed list (as resPath goes bottom-up)
        return resPath[::-1]

    def __str__(self):
        """ String representation,  for debugging only """
        strRep = "Cell [{}, {}]".format(self.x, self.y)
        if not self.reachable:
            strRep += " (wall)"

        return strRep


class DiscreteMap:

    def __init__(self, svgMap, division=5, radius=100):

        self.division = division

        self.width = int(svgMap.width/division)
        self.height = int(svgMap.height/division)
        self.division = division

        # Open and closed list, used for A* algorithm
        self.ol = set()
        self.cl = set()

        self.svgMap = svgMap

        self.initgrid = [[Cell(x, y) for x in xrange(self.width)] for y in xrange(self.height)]
        self.grid = [[Cell(x, y) for x in xrange(self.width)] for y in xrange(self.height)]

        for y in xrange(self.height):
            for x in xrange(self.width):
                # The cell (x, y) will represent the point ( (x + 0.5)*division, (y + 0.5)*division )
                xi, yi = (x + 0.5)*self.division, (y + 0.5)*self.division
                obstacle = self.svgMap.isObstacle(xi, yi)
                self.initgrid[y][x].reachable = not obstacle
                self.grid[y][x].reachable = not obstacle

        self.setRadius(radius)

    def setRadius(self, radius=0):
        # Taking into account the car's width (radius)
        r = radius / self. division
        # 1 : Unreachable ; 0 : Reachable
        car = scipy.array([[1 for i in xrange(r)] for j in xrange(r)])
        grid = scipy.array([[0 if self.initgrid[i][j].reachable else 1 for j in xrange(
            self.width)] for i in xrange(self.height)])

        result = scipy.signal.fftconvolve(grid, car, 'same')

        for i in xrange(self.height):
            for j in xrange(self.width):
                self.grid[i][j].reachable = int(result[i][j]) == 0

    def neighbours(self, cell, radius=1, unreachables=False, diagonal=True):
        neighbours = set()
        for i in xrange(-radius, radius + 1):
            for j in xrange(-radius, radius + 1):
                x = cell.x + j
                y = cell.y + i
                if 0 <= y < self.height and 0 <= x < self.width and (self.grid[y][x].reachable or unreachables) and (diagonal or (x == cell.x or y == cell.y)):
                    neighbours.add(self.grid[y][x])

        return neighbours

    def search(self, begin, goal):

        if goal.x not in range(self.width) or goal.y not in range(self.height):
            print "Goal is out of bound"
            return []
        elif not self.grid[begin.y][begin.x].reachable:
            print "Beginning is unreachable"
            return []
        elif not self.grid[goal.y][goal.x].reachable:
            print "Goal is unreachable"
            return []
        else:
            # We intialize the closed and open list
            cl = set()
            ol = set()
            ol.add(begin)

            # We initialize the
            begin.g = 0
            begin.h = begin.diagonalDistance(goal)
            begin.f = begin.g + begin.h

            while len(ol) > 0:
                curCell = min(ol, key=lambda cell: cell.f)

                if curCell == goal:
                    # We get the path to the current cell, minus the first cell
                    path = curCell.path()[1:]

                    # Before returning the result, we clear the grid (from all weights, parents, ...)
                    self.clear()

                    return path

                ol.remove(curCell)
                cl.add(curCell)

                for neighbor in self.neighbours(curCell):
                    gScore = curCell.g + curCell.distance(neighbor)

                    if neighbor in cl:
                        if gScore >= neighbor.g:
                            continue

                    if neighbor not in ol or gScore < neighbor.g:
                        neighbor.parent = curCell
                        neighbor.g = gScore
                        neighbor.f = neighbor.g + neighbor.diagonalDistance(goal)
                        if neighbor not in ol:
                            ol.add(neighbor)

            self.clear()
            return []

    def altsearch(self, begin, goal):
        if not (0 < goal.x < self.width and 0 < goal.y < self.height):
            print "Goal is out of bound"
            return []
        elif not self.grid[begin.y][begin.x].reachable:
            print "Beginning is unreachable"
            return []
        elif not self.grid[goal.y][goal.x].reachable:
            print "Goal is unreachable"
            return []
        else:

            self.cl = set()
            self.ol = set()

            curCell = begin
            self.ol.add(curCell)

            while len(self.ol) > 0:

                # We choose the cell in the open list having the minimum score as our current cell
                curCell = min(self.ol, key=lambda cell: cell.f)

                # We add the current cell to the closed list
                self.ol.remove(curCell)
                self.cl.add(curCell)

                # We check the cell's (reachable) neighbours :
                neighbours = self.neighbours(curCell, diagonal=True)

                for cell in neighbours:
                    # If the goal is a neighbour cell :
                    if cell == goal:
                        cell.parent = curCell
                        self.path = cell.path()
                        # self.display()
                        self.clear()
                        return self.path
                    elif cell not in self.cl:
                        # We process the cells that are not in the closed list
                        # (processing <-> calculating the "F" score)
                        cell.process(curCell, goal)

                        self.ol.add(cell)

                # To vizualize the algorithm in ASCII
                # self.display()
                # sleep(0.02)

            # If the open list gets empty : no path can be found
            self.clear()
            return []

    def clear(self):
        for line in self.grid:
            for cell in line:
                cell.f = 0
                cell.h = 0
                cell.g = 0
                cell.parent = None

    def display(self):

        dispMatrix = [[' ' for x in range(self.width)] for y in range(self.height)]
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[y][x].reachable:
                    dispMatrix[y][x] = ' '
                else:
                    dispMatrix[y][x] = '#'
        # for cell in self.cl:
        #     dispMatrix[cell.y][cell.x] = 'X'
        for cell in self.path:
            print len(self.path)
            dispMatrix[cell.y][cell.x] = 'o'

        print ' ' + '__'*(1 + self.width)
        for i in range(self.height):
            print '| ',
            for j in range(self.width):
                print dispMatrix[i][j],
            # End of line
            print "|\n",
        print '|' + '__'*(1 + self.width) + '|'
