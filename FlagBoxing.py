#Flag Boxing by Esie-Eyen
import bs

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [FlagBoxingGame]

class FlagBoxingGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Flag Boxing'

    @classmethod
    def getDescription(cls,sessionType):
        return ('Mr. Flag will help you, maybe.')

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Courtyard']

    @classmethod
    def getSettings(cls,sessionType):
        return [("KOs to Win Per Player",{'minValue':1,'default':5,'increment':1}),
                ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                        ('2 Minutes',120),('5 Minutes',300),
                                        ('10 Minutes',600),('20 Minutes',1200)],'default':0}),
                ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                ("Epic Mode",{'default':False})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True
        self.announcePlayerDeaths = True      
        self._scoreBoard = bs.ScoreBoard()

    def getInstanceDescription(self):
        return ('KO ${ARG1} of your enemies with Mr. Flag.',self._scoreToWin)

    def getInstanceScoreBoardDescription(self):
        return ('KO ${ARG1} enemies with Mr. Flag.',self._scoreToWin)

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'GrandRomp')

    def onTeamJoin(self,team):
        team.gameData['score'] = 0
        if self.hasBegun(): self._updateScoreBoard()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        
        if len(self.teams) > 0:
            self._scoreToWin = self.settings['KOs to Win Per Player'] * max(1,max(len(t.players) for t in self.teams))
            
        else: self._scoreToWin = self.settings['KOs to Win Per Player']
        self._updateScoreBoard()
        self._dingSound = bs.getSound('dingSmall')
        self.bgFlag()

    def spawnPlayer(self,player):

        spaz = self.spawnPlayerSpaz(player)
        spaz.connectControlsToPlayer(enablePunch=True,
                                     enableBomb=False,
                                     enablePickUp=True)
                                     
    def bgFlag(self):
    	self.bgf = bs.Flag(position=(0,2.7,-1.5),touchable=True,color=(10,10,10))
        bs.gameTimer(100,self.curseFlag)
        
    def curseFlag(self):
    	self.cf = bs.Flag(position=(0,2.7,-1.5),touchable=True,color=(0,0,0))
        self.bgf = None
        bs.gameTimer(100,self.bg2Flag)
        
    def bg2Flag(self):
    	self.bgf2 = bs.Flag(position=(0,2.7,-1.5),touchable=True,color=(10,10,10))
        self.cf = None
        bs.gameTimer(100,self.freezeFlag)
        
    def freezeFlag(self):
    	self.ff = bs.Flag(position=(0,2.7,-1.5),touchable=True,color=(0,0,0))
        self.bgf2 = None
        bs.gameTimer(100,self.bg3Flag)
        
    def bg3Flag(self):
    	self.bgf3 = bs.Flag(position=(0,2.7,-1.5),touchable=True,color=(10,10,10))
        self.ff = None
        bs.gameTimer(100,self.loopFlag)
      
    def loopFlag(self):
    	self.bgf3 = None
        self.bgFlag()

    def handleMessage(self,m):   
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior

            player = m.spaz.getPlayer()
            self.respawnPlayer(player)

            killer = m.killerPlayer
            if killer is None: return

            if killer.getTeam() is player.getTeam():

                if isinstance(self.getSession(),bs.FreeForAllSession):
                    player.getTeam().gameData['score'] = max(0,player.getTeam().gameData['score']-1)

                else:
                    bs.playSound(self._dingSound)
                    for team in self.teams:
                        if team is not killer.getTeam():
                            team.gameData['score'] += 1
                            
            else:
                killer.getTeam().gameData['score'] += 1
                bs.playSound(self._dingSound)
                try: killer.actor.setScoreText(str(killer.getTeam().gameData['score'])+'/'+str(self._scoreToWin),color=killer.getTeam().color,flash=True)
                except Exception: pass

            self._updateScoreBoard()

            if any(team.gameData['score'] >= self._scoreToWin for team in self.teams):
                bs.gameTimer(500,self.endGame)

        else: bs.TeamGameActivity.handleMessage(self,m)
        
        if isinstance(m,bs.FlagPickedUpMessage):
            if m.flag is self.bgf:
                bs.screenMessage("Boxing Gloves")
                m.node.boxingGloves = True
            elif m.flag is self.cf:
                bs.screenMessage("Curse")
                m.node.getDelegate().curse() 
            elif m.flag is self.bgf2:
            	bs.screenMessage("Boxing Gloves")
                m.node.boxingGloves= True
            elif m.flag is self.ff:
            	bs.screenMessage("Freeze")
                m.node.frozen = True
            elif m.flag is self.bgf3:
            	bs.screenMessage("Boxing Gloves")
                m.node.boxingGloves= True        

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['score'],self._scoreToWin)

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t,t.gameData['score'])
        self.end(results=results)