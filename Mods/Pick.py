# Pick Mod by Esie-Eyen
import bs
import random
import bsUtils

def bsGetAPIVersion(): return 4

def bsGetGames(): return [PickGame]

class PickGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return 'Pick'

    @classmethod
    def getDescription(cls,sessionType):
        return ('You need to pick the right flag.')

    @classmethod
    def supportsSessionType(cls,sessionType): return True if (issubclass(sessionType,bs.TeamsSession) or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Rampage']

    @classmethod
    def getSettings(cls,sessionType):
        return [("Scores to Win",{'minValue':1,'default':5,'increment':1}),
                ("Time Limit",{'choices':[('None',0),('1 Minute',60),('2 Minutes',120),('5 Minutes',300),('10 Minutes',600),('20 Minutes',1200)],'default':0})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self._scoreBoard = bs.ScoreBoard()

    def getInstanceDescription(self):
        return ('Pick ${ARG1} right flags to win.',self._scoreToWin)

    def getInstanceScoreBoardDescription(self):
        return ('Pick ${ARG1} right flags to win.',self._scoreToWin)

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='GrandRomp')

    def onTeamJoin(self,team):
        team.gameData['score'] = 0
        if self.hasBegun(): self._updateScoreBoard()

    def spawnPlayer(self,player):
        spaz = self.spawnPlayerSpaz(player)
        spaz.connectControlsToPlayer(enablePunch=False,enableBomb=False,enablePickUp=True)

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])   
        if len(self.teams) > 0: self._scoreToWin = self.settings['Scores to Win'] * max(1,max(len(t.players) for t in self.teams))          
        else: self._scoreToWin = self.settings['Scores to Win']
        self._updateScoreBoard()
        self._dingSound = bs.getSound('dingSmall')
        self.pickFlag()
        self.redFlag()

    def pickFlag(self):
    	self._red = False
        self._green = False
        self._blue = False
    	pick = random.randint(1,3)
        if pick == 1:
            bsUtils.ZoomText("Pick Red Flag",lifespan=3000,jitter=3.5,position=(0,-270),scale=0.35,maxWidth=700,trail=False,color=(2,0.7,0.7)).autoRetain()                    
            self._red = True           
        if pick == 2:
            bsUtils.ZoomText("Pick Green Flag",lifespan=3000,jitter=3.5,position=(0,-270),scale=0.35,maxWidth=700,trail=False,color=(0.7,2,0.7)).autoRetain()
            self._green = True 	
        if pick == 3:
            bsUtils.ZoomText("Pick Blue Flag",lifespan=3000,jitter=3.5,position=(0,-270),scale=0.35,maxWidth=700,trail=False,color=(0.7,0.7,2)).autoRetain()
            self._blue = True    
  	
    def redFlag(self):
        self.red = bs.Flag(position=(0.3,5,-4.3),touchable=True,color=(2,0.5,0.5))
        bs.gameTimer(100,self.greenFlag)
        
    def greenFlag(self):
    	self.red = None
        self.green = bs.Flag(position=(0.3,5,-4.3),touchable=True,color=(0.5,2,0.5))
        bs.gameTimer(100,self.blueFlag)   
    
    def blueFlag(self):
    	self.green = None
        self.blue = bs.Flag(position=(0.3,5,-4.3),touchable=True,color=(0.5,0.5,2))
        bs.gameTimer(100,self.loopFlag)   
     
    def loopFlag(self):
        self.blue = None
        self.redFlag()

    def handleMessage(self,m):   
        if isinstance(m,bs.PlayerSpazDeathMessage):
            player = m.spaz.getPlayer()
            self.respawnPlayer(player)
        if isinstance(m,bs.FlagPickedUpMessage):
            if m.flag is self.red: 
            	if self._red:
                    self.pickFlag()
                    self._score() 
                    m.node.handleMessage(bs.DieMessage())
                if not self._red: m.node.handleMessage(bs.FreezeMessage())
            elif m.flag is self.green:
            	if self._green:
                    self.pickFlag()   
                    self._score()
                    m.node.handleMessage(bs.DieMessage())
                if not self._green: m.node.handleMessage(bs.FreezeMessage())                    
            elif m.flag is self.blue:
            	if self._blue:
                    self.pickFlag()   
                    self._score()   
                    m.node.handleMessage(bs.DieMessage())
                if not self._blue: m.node.handleMessage(bs.FreezeMessage())                    
            if any(team.gameData['score'] >= self._scoreToWin for team in self.teams): bs.gameTimer(500,self.endGame)                 
    def _score(self):
    	for team in self.teams:
    	    team.gameData['score'] += 1
        self._updateScoreBoard()
        bs.playSound(self._dingSound)         
        def dark(): bs.getSharedObject('globals').tint = 0.0,0.0,0.0
        def normal(): bs.getSharedObject('globals').tint = 1.25,1.15,0.95    
        dark()
        bs.gameTimer(3000,normal)  
        
    def _updateScoreBoard(self):
        for team in self.teams: self._scoreBoard.setTeamValue(team,team.gameData['score'],self._scoreToWin)

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t,t.gameData['score'])
        self.end(results=results)