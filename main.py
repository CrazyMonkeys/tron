import sys
import math
import copy
import time
import cProfile
import random

LOGGING = False

def cprint(iString):
    if LOGGING:
         print >> sys.stderr, str(iString)

def do_cprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            profile.print_stats()
    return profiled_func

#possible status of a cell of the board
class cellStatus:
    EMPTY=0
    PLAYER=1
    LIGHT=2
    DRONE=3
    OUT=4
    OPLAYER0=5
    OPLAYER1=6
    OPLAYER2=7
    OPLAYER3=8
    
    def getPlayer(self, iIntPlayer):
        if iIntPlayer == 1:
            return cellStatus.OPLAYER1
        elif iIntPlayer == 2:
            return cellStatus.OPLAYER2
        elif iIntPlayer == 3:
            return cellStatus.OPLAYER3
        elif iIntPlayer == 4:
            return cellStatus.OPLAYER4

#Possible actions for a player
class actions:
    UP=0
    DOWN=1
    RIGHT=2
    LEFT=3

    
#Give the string label for the action to perform
def getLabel(iLabel):
    if iLabel == 0:
        return "UP"
    elif iLabel == 1:
        return "DOWN"
    elif iLabel == 2:
        return "RIGHT"
    elif iLabel == 3:
        return "LEFT"

#Board size, origin position = 0
class boardSize:
    X=29
    Y=19
    
#Static method retuning an updated position based on  current pos + move. Thore board is taken into account
def normalizePosition(iPos, iAction):
    aNewX = iPos[0]
    aNewY = iPos[1]
    if iAction == actions.UP:
        aNewY -=1 
    elif iAction == actions.DOWN:
        aNewY +=1
    elif iAction == actions.RIGHT:
        aNewX +=1
    elif iAction == actions.LEFT:
        aNewX -=1
    aOutput = [aNewX,aNewY]
    return aOutput

     
class board:
    def __init__(self):
        self.xMax = 30
        self.yMax = 20
        self.grille = []
        #creates represntation of the board
        for i in range(0,self.yMax):
            self.grille.append([cellStatus.EMPTY]*self.xMax)
            
    #get the content of cell located at iPos
    def getContent(self, iPos):
        if iPos[0] < 0 or iPos[1] <0 or  iPos[0] > boardSize.X or iPos[1] > boardSize.Y:
            return cellStatus.OUT
        return self.grille[iPos[1]][iPos[0]]
        
    #Set the content of cell located at iPos       
    def setContent(self, iPos,iContent):
        self.grille[iPos[1]][iPos[0]]=iContent
    
    def printObject(self):
        for line in self.grille:
            print >> sys.stderr,str((' ').join([str(i).replace("0", ".") for i in line]))


class move:
    def __init__(self, iEnumMove):
        self.value = iEnumMove
        
    #Transforms current coords to new coords dependgin on move type
    def getNewCoord(self,iPos):
        return normalizePosition(iPos,self.value)


class game:
    def __init__(self):
        self.board = board()
        self.playerPosition = []
        self.playerDronePosition = []
        self.myPosition = [-1, -1]
        self.previousAction = None

    #Init step: set the position of players
    def refreshPosition(self,iPlayer, iX, iY):
        if iX == -1:
            self.refreshRemovePosition(iPlayer)
        else:
            self.playerPosition.append([iX, iY,iPlayer])

    #Init step: set the position of our player
    def setMyPosition(self, x ,y):
        self.myPosition = [x, y]
            
    def refreshRemovePosition(self, iPlayer):
        for x in range(0,boardSize.X+1):
            for y in range(0,boardSize.Y+1):
                pass
                if self.board.getContent([x,y]) == cellStatus().getPlayer(iPlayer):
                    self.board.setContent([x,y],cellStatus.EMPTY)
            

    #Init step: Update the game with player positions
    def applyPosition(self):
        for position in self.playerPosition:
            self.board.setContent(position, cellStatus.PLAYER)

        self.board.setContent(self.myPosition, cellStatus.PLAYER)
        
    #Post run step: update the game with the light trail
    def applyRefresh(self,iPreviousAction=None):
        if iPreviousAction:
            self.previousAction = iPreviousAction
        otherPlayerCounter = 0
        for position in self.playerPosition:
            
            self.board.setContent(position, cellStatus().getPlayer(position[2]))
            otherPlayerCounter += 1
        del self.playerPosition[:]
        self.board.setContent(self.myPosition, cellStatus.LIGHT)

    #Apply a move to the current game and return a copy of the game
    def applyMove(self, iMove):
        # return a copy a the current game after the move is applied
        newGame = copy.deepcopy(self)
        newGame.board.setContent(newGame.myPosition, cellStatus.LIGHT)
        newGame.myPosition = iMove.getNewCoord(newGame.myPosition)
        newGame.previousAction = iMove
        return newGame
        
class miniMax:

    @classmethod
    def calcMax(iClass,iState,iCurrentLevel, iMaxLevel):
        #iState.display()
        cprint("CALCMAX LEVEL="+str(iCurrentLevel))
        #iState.printObject()
        if iCurrentLevel == iMaxLevel:
            cprint ("max prof =" + str(iCurrentLevel))
            return iCurrentLevel
        else:
            valueBestMove =-100000
            M = iState.getMoves()
            cprint("Possible moves in calcMax :"+str([getLabel(m.value) for m in M]))
            for m in M:
                cprint( "calcMax :Evaluating move"+' '+ getLabel(m.value)+' at level'+str(iCurrentLevel))
                temp = iClass.calcMax(iState.applyMove(m),iCurrentLevel+1,iMaxLevel)
                cprint( "calcMax :Result="+ str(temp))
                
                if temp > valueBestMove:
                    valueBestMove=temp
            if not M:
                cprint("leaf = " + str(iCurrentLevel))
                return iCurrentLevel
                
            return valueBestMove

    
    @classmethod
    def miniMax(iClass,iState,iMaxLevel):
        #iState.display()
        bestMove = None
        valueBestMove = -100000
        for m in iState.getMoves(True):
            print >> sys.stderr,"miniMax :Evaluating"+' '+ getLabel(m.value)
            temp = iClass.calcMax(iState.applyMove(m),1,iMaxLevel)
            #print "m is", temp, " best move is ", valueBestMove
            
            #Apply risk factor on temp
            if iClass.isRisky(iState,m):
                temp = round(temp / 2.0)
                print >> sys.stderr,"isRisky",getLabel(m.value)
            if temp > valueBestMove:
                valueBestMove=temp
                bestMove=m
        return bestMove

    @classmethod        
    def isRisky(iClass,iState,iMove):
        newPos = normalizePosition(iState.mState.myPosition, iMove)
        numPlayers = 0
        if iState.getPatchedContent(normalizePosition(newPos, actions.UP)) == cellStatus.PLAYER:
            numPlayers+=1
        if iState.getPatchedContent(normalizePosition(normalizePosition(newPos, actions.UP),actions.LEFT)) == cellStatus.PLAYER:
            numPlayers+=1
        if iState.getPatchedContent(normalizePosition(newPos, actions.DOWN)) == cellStatus.PLAYER:
            numPlayers+=1
        if iState.getPatchedContent(normalizePosition(normalizePosition(newPos, actions.DOWN),actions.RIGHT)) == cellStatus.PLAYER:
            numPlayers+=1
        if iState.getPatchedContent(normalizePosition(newPos, actions.RIGHT)) == cellStatus.PLAYER:
            numPlayers+=1
        if iState.getPatchedContent(normalizePosition(normalizePosition(newPos, actions.RIGHT),actions.UP)) == cellStatus.PLAYER:
            numPlayers+=1
        if iState.getPatchedContent(normalizePosition(newPos, actions.LEFT)) == cellStatus.PLAYER:
            numPlayers+=1
        if iState.getPatchedContent(normalizePosition(normalizePosition(newPos, actions.LEFT),actions.DOWN)) == cellStatus.PLAYER:
            numPlayers+=1
        return numPlayers > 2
        
        
    
    
class mutableState:
    def __init__(self):
        self.myPosition = [-1, -1]
        self.previousAction = None
        self.patchDict = {}

class gameProxy:
    def __init__(self,iGame):
        self.board = iGame.board
        self.mState = mutableState()
        self.mState.myPosition =iGame.myPosition
        self.mState.previousAction =iGame.previousAction
        
    def printObject(self):
        cprint ("Evaluating board")
        for i in range(0,15):
            line =''
            for j in range(0,30):
                line += str(self.getPatchedContent([j,i])).replace("0", ".")+' '
            cprint(line)

    def setStateFromGame(self,iGame):
        self.mState.myPosition = iGame.myPosition
        self.mState.previousAction = iGame.previousAction

    def setStateFromProxyGame(self,iMutableState):
        self.mState = iMutableState
    
    def getPatchedContent(self,iPos):
        #if iPos[0] < 0 or iPos[1] <0 or  iPos[0] > boardSize.X or iPos[1] > boardSize.Y:
        #    return cellStatus.OUT
        k = tuple(iPos)
        if k in self.mState.patchDict:
            return self.mState.patchDict[k]
        else:
            return self.board.getContent(iPos)

    #List the possible moves for the current player
    def getMoves(self,iLog=False):
        aList = []
        if self.getPatchedContent(normalizePosition(self.mState.myPosition, actions.UP)) == cellStatus.EMPTY:
            aList.append(move(actions.UP))

        if self.getPatchedContent(normalizePosition(self.mState.myPosition, actions.DOWN)) == cellStatus.EMPTY:
            aList.append(move(actions.DOWN))

        if self.getPatchedContent(normalizePosition(self.mState.myPosition, actions.RIGHT)) == cellStatus.EMPTY:
            aList.append(move(actions.RIGHT))

        if self.getPatchedContent(normalizePosition(self.mState.myPosition, actions.LEFT)) == cellStatus.EMPTY:
            aList.append(move(actions.LEFT))

        cprint("Possible moves :"+str([getLabel(m.value) for m in aList]))
        return aList


    #Apply a move to the current game and return a copy of the game
    def applyMove(self, iMove):
        # return a copy a the current game proxy after the move is applied
        mState = copy.copy(self.mState)
        newGame = copy.copy(self)
        newGame.setStateFromProxyGame(mState)
        #INVARIANT: newGame and self are light copies
        
        newGame.mState.patchDict[tuple(newGame.mState.myPosition)] = cellStatus.LIGHT
        newGame.mState.myPosition = iMove.getNewCoord(newGame.mState.myPosition)
        newGame.mState.previousAction = iMove
        
        #INVARIANT : position is update accordingly to move
        newGame.mState.patchDict[tuple(newGame.mState.myPosition)] = cellStatus.PLAYER
        #newGame.printObject()
        return newGame

    #Evaluate a game
    def evaluate(self,iProf):
        #print "prof",iProf
        return iProf

        
# game loop
myGame = game()
while 1:
     # n: total number of players (2 to 4).
     # p: your player number (0 to 3).
    player_count, my_player = [int(i) for i in raw_input().split()]
    print >> sys.stderr, "player_count, my_player: ", player_count, my_player
                
    for i in xrange(player_count):
         # x0: starting X coordinate of lightcycle (or -1)
         # y0: starting Y coordinate of lightcycle (or -1)
         # x1: starting X coordinate of lightcycle (can be the same as X0 if you play before this player)
         # y1: starting Y coordinate of lightcycle (can be the same as Y0 if you play before this player)
        x0, y0, x1, y1 = [int(j) for j in raw_input().split()]
        # real player have x,y > 0
        if i == my_player:
            myGame.setMyPosition(x1, y1)
            print >> sys.stderr, "my position: ", x1,y1
        else:
            myGame.refreshPosition(i,x1, y1)

            
    myGame.applyPosition()
        
    myGame.board.printObject()
    aGameProxy = gameProxy(myGame)
    aGameProxy.setStateFromGame(myGame)
    retour = miniMax.miniMax(aGameProxy,10000)
        
    # Write an action using print
    # To debug: print >> sys.stderr, "Debug messages..."

    # A single line with UP, DOWN, LEFT or RIGHT
    myGame.applyRefresh(retour)
    print(getLabel(retour.value))
