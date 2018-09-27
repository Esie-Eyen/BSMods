# Hide Mod by Esie-Eyen
import bs
import random
import bsUtils

def bsGetAPIVersion(): return 4

def bsGetGames(): return [HideGame]

class HideGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls): return 'Hide'

    @classmethod
    def getDescription(cls, sessionType): return 'Hide and kill a set number of enemies to win.'

    @classmethod
    def supportsSessionType(cls, sessionType): return True if(issubclass(sessionType, bs.TeamsSession)or issubclass(sessionType, bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls, sessionType): return ['Football Stadium']

    @classmethod
    def getSettings(cls, sessionType):
        settings = [("Kills to Win Per Player",{'minValue': 1, 'default': 10, 'increment': 1}),
            ("Time Limit",{'choices':[('None', 0),('1 Minute', 60),('2 Minutes', 120),('5 Minutes', 300),('10 Minutes', 600),('20 Minutes', 1200)],'default': 0}),
            ("Respawn Times",{'choices':[('Shorter', 0.25),('Short', 0.5),('Normal', 1.0),('Long', 2.0),('Longer', 4.0)],'default': 1.0})]              
        if issubclass(sessionType, bs.FreeForAllSession): settings.append(("Allow Negative Scores", {'default': False}))
        return settings

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)          
        self.announcePlayerDeaths = True
        self._scoreBoard = bs.ScoreBoard()

    def getInstanceDescription(self): return ('Hide and kill ${ARG1} of your enemies.', self._scoreToWin)

    def getInstanceScoreBoardDescription(self): return ('Hide and kill ${ARG1} enemies.', self._scoreToWin)

    def onTransitionIn(self): bs.TeamGameActivity.onTransitionIn(self, music='ToTheDeath')

    def onTeamJoin(self, team):
        team.gameData['score'] = 0
        if self.hasBegun(): self._updateScoreBoard()

    def spawnPlayer(self, player):
        pos = random.choice([(0,0,-4),(0,0,4),(0,0,0),(-9,0,0),(9,0,0)])
        spaz = self.spawnPlayerSpaz(player,position=pos)
        spaz.node.name = ' '
        hide = random.randint(0,1)	
        if hide == 0:  
            bsUtils.ZoomText(player.getName()+" is visible.",lifespan=3000,jitter=3.5,position=random.choice([(0,-270),(0,270)]),scale=0.35,maxWidth=700,trail=False,color=random.choice([(1,0.7,0.7),(0.7,1,0.7),(0.7,0.7,1)])).autoRetain()              
            self._shield = bs.newNode('shield',owner=spaz.node,attrs={'color':(1.4, 1.7, 2.0),'radius':1.5})
            spaz.node.connectAttr('positionCenter',self._shield,'position') 
            spaz.node.name = player.getName()  
        if hide == 1:
            def nameV():
                spaz.node.name = player.getName()
                bs.gameTimer(3000,nameH)
            def nameH(): spaz.node.name = ' '
            bs.gameTimer(7000,nameV,repeat=3000)

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()
        if len(self.teams) > 0: self._scoreToWin = self.settings['Kills to Win Per Player'] * max(1, max(len(t.players) for t in self.teams))
        else: self._scoreToWin = self.settings['Kills to Win Per Player']
        self._updateScoreBoard()
        self._dingSound = bs.getSound('dingSmall')
        bs.getSharedObject('globals').tint = 0.15,0.15,0.15

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self, m)
            player = m.spaz.getPlayer()
            self.respawnPlayer(player)
            killer = m.killerPlayer            
            if killer is None: return
            if killer.getTeam() is player.getTeam():
                if isinstance(self.getSession(), bs.FreeForAllSession):
                    newScore = player.getTeam().gameData['score'] - 1
                    if not self.settings['Allow Negative Scores']: newScore = max(0, newScore)
                    player.getTeam().gameData['score'] = newScore
                else:
                    bs.playSound(self._dingSound)
                    for team in self.teams:
                        if team is not killer.getTeam(): team.gameData['score'] += 1
            else:
                killer.getTeam().gameData['score'] += 1
                bs.playSound(self._dingSound)
                try: killer.actor.setScoreText(str(killer.getTeam().gameData['score']) + '/' +str(self._scoreToWin),color=killer.getTeam().color, flash=True)
                except Exception: pass
            self._updateScoreBoard()
            if any(team.gameData['score'] >= self._scoreToWin for team in self.teams): bs.gameTimer(500, self.endGame)
        else: bs.TeamGameActivity.handleMessage(self, m)

    def _updateScoreBoard(self):
        for team in self.teams: self._scoreBoard.setTeamValue(team, team.gameData['score'],self._scoreToWin)

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t, t.gameData['score'])
        self.end(results=results)       