#Extra Powerup by Esie-Eyen
import bs
import random
import bsPowerup
from bsPowerup import PowerupMessage, PowerupAcceptMessage, _TouchedMessage, PowerupFactory, Powerup

defaultPowerupInterval = 8000

class NewPowerupFactory(PowerupFactory):
    def __init__(self):
        self._lastPowerupType = None

        self.model = bs.getModel("powerup")
        self.modelSimple = bs.getModel("powerupSimple")

        self.texBomb = bs.getTexture("powerupBomb")
        self.texPunch = bs.getTexture("powerupPunch")
        self.texIceBombs = bs.getTexture("powerupIceBombs")
        self.texStickyBombs = bs.getTexture("powerupStickyBombs")
        self.texShield = bs.getTexture("powerupShield")
        self.texImpactBombs = bs.getTexture("powerupImpactBombs")
        self.texHealth = bs.getTexture("powerupHealth")
        self.texLandMines = bs.getTexture("powerupLandMines")
        self.texCurse = bs.getTexture("powerupCurse")
        self.texBlast = bs.getTexture("tnt")
        self.texMix = bs.getTexture("eggTex1")

        self.healthPowerupSound = bs.getSound("healthPowerup")
        self.powerupSound = bs.getSound("powerup01")
        self.powerdownSound = bs.getSound("powerdown01")
        self.dropSound = bs.getSound("boxDrop")

        self.powerupMaterial = bs.Material()

        self.powerupAcceptMaterial = bs.Material()

        self.powerupMaterial.addActions(
            conditions=(("theyHaveMaterial",self.powerupAcceptMaterial)),
            actions=(("modifyPartCollision","collide",True),
                     ("modifyPartCollision","physical",False),
                     ("message","ourNode","atConnect",_TouchedMessage())))

        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('pickupMaterial')),
            actions=( ("modifyPartCollision","collide",False)))

        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('footingMaterial')),
            actions=(("impactSound",self.dropSound,0.5,0.1)))

        self._powerupDist = []
        for p,freq in getDefaultPowerupDistribution():
            for i in range(int(freq)):
                self._powerupDist.append(p)

    def getRandomPowerupType(self,forceType=None,excludeTypes=[]):
        if forceType:
            t = forceType
        else:
            if self._lastPowerupType == 'curse':
                t = 'health'
            else:
                while True:
                    t = self._powerupDist[
                        random.randint(0, len(self._powerupDist)-1)]
                    if t not in excludeTypes:
                        break
        self._lastPowerupType = t
        return t

def getDefaultPowerupDistribution():
    return (('tripleBombs',2), #3
            ('iceBombs',2), #3
            ('punch',2), #3
            ('impactBombs',2), #3
            ('landMines',2), #3
            ('stickyBombs',2), #3
            ('shield',1), #2
            ('health',1),
            ('curse',1),
            ('blast',1),
            ('mix',3))

class NewPowerup(Powerup):
    def __init__(self,position=(0,1,0),powerupType='tripleBombs',expire=True):
        
        bs.Actor.__init__(self)

        factory = self.getFactory()
        self.powerupType = powerupType;
        self._powersGiven = False

        if powerupType == 'tripleBombs': tex = factory.texBomb
        elif powerupType == 'punch': tex = factory.texPunch
        elif powerupType == 'iceBombs': tex = factory.texIceBombs
        elif powerupType == 'impactBombs': tex = factory.texImpactBombs
        elif powerupType == 'landMines': tex = factory.texLandMines
        elif powerupType == 'stickyBombs': tex = factory.texStickyBombs
        elif powerupType == 'shield': tex = factory.texShield
        elif powerupType == 'health': tex = factory.texHealth
        elif powerupType == 'curse': tex = factory.texCurse
        elif powerupType == 'blast': tex = factory.texBlast
        elif powerupType == 'mix': tex = factory.texMix
        else: raise Exception("invalid powerupType: "+str(powerupType))

        if len(position) != 3: raise Exception("expected 3 floats for position")
        
        self.node = bs.newNode(
            'prop',
            delegate=self,
            attrs={'body':'box',
                   'position':position,
                   'model':factory.model,
                   'lightModel':factory.modelSimple,
                   'shadowSize':0.5,
                   'colorTexture':tex,
                   'reflection':'powerup',
                   'reflectionScale':[1.0],
                   'materials':(factory.powerupMaterial,
                                bs.getSharedObject('objectMaterial'))})

        curve = bs.animate(self.node,"modelScale",{0:0,140:1.6,200:1})
        bs.gameTimer(200,curve.delete)

        if expire:
            bs.gameTimer(defaultPowerupInterval-2500,
                         bs.WeakCall(self._startFlashing))
            bs.gameTimer(defaultPowerupInterval-1000,
                         bs.WeakCall(self.handleMessage, bs.DieMessage()))

    @classmethod
    def getFactory(cls):
        activity = bs.getActivity()
        if activity is None: raise Exception("no current activity")
        try: return activity._sharedPowerupFactory
        except Exception:
            f = activity._sharedPowerupFactory = PowerupFactory()
            return f
            
    def _startFlashing(self):
        if self.node.exists(): self.node.flashing = True
 
    def handleMessage(self, msg):
        self._handleMessageSanityCheck()

        if isinstance(msg, PowerupAcceptMessage):
            factory = self.getFactory()
            if self.powerupType == 'health':
                bs.playSound(factory.healthPowerupSound, 3,
                             position=self.node.position)
            bs.playSound(factory.powerupSound, 3, position=self.node.position)
            self._powersGiven = True
            self.handleMessage(bs.DieMessage())
            
            if self.powerupType == 'blast':
            	radius = random.choice([0.5,1.0,1.5,2.0])
            	type = random.choice(['ice','normal','sticky','tnt'])           
            	pos = self.node.position
            	bs.Blast(position=(pos[0],pos[1],pos[2]),blastRadius=radius,blastType=type).autoRetain()
                self._blast = True
                if self._blast == True:
                    if type == 'ice': bs.screenMessage("Type: Ice")
                    if type == 'normal': bs.screenMessage("Type: Normal")
                    if type == 'sticky': bs.screenMessage("Type: Sticky")
                    if type == 'tnt': bs.screenMessage("Type: Tnt")
                    if radius == 0.5: bs.screenMessage("Radius: 0.5")
                    if radius == 1.0: bs.screenMessage("Radius: 1.0")
                    if radius == 1.5: bs.screenMessage("Radius: 1.5")
                    if radius == 2.0: bs.screenMessage("Radius: 2.0")

            if self.powerupType == 'mix':
            	pow = random.choice(['tripleBombs','iceBombs','punch','impactBombs','landMines','stickyBombs','shield','health','curse'])
                pos = self.node.position
                bs.Powerup(position=(pos[0],pos[1],pos[2]),powerupType=pow).autoRetain()
                self._mix = True
                if self._mix == True:
                    if pow == 'tripleBombs': bs.screenMessage("Triple Bombs")
                    if pow == 'iceBombs': bs.screenMessage("Ice Bombs")
                    if pow == 'punch': bs.screenMessage("Boxing Gloves")
                    if pow == 'impactBombs': bs.screenMessage("Impact Bombs")
                    if pow == 'landMines': bs.screenMessage("Land Mines")
                    if pow == 'stickyBombs': bs.screenMessage("Sticky Bombs")
                    if pow == 'shield': bs.screenMessage("Energy Shield")
                    if pow == 'health': bs.screenMessage("Health Kit")
                    if pow == 'curse': bs.screenMessage("Curse")
                    
        elif isinstance(msg, _TouchedMessage):
            if not self._powersGiven:
                node = bs.getCollisionInfo("opposingNode")
                if node is not None and node.exists():
                    node.handleMessage(PowerupMessage(self.powerupType,
                                                      sourceNode=self.node))
            
        elif isinstance(msg, bs.DieMessage):
            if self.node.exists():
                if (msg.immediate):
                    self.node.delete()
                else:
                    curve = bs.animate(self.node, "modelScale", {0:1,100:0})
                    bs.gameTimer(100, self.node.delete)

        elif isinstance(msg ,bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())

        elif isinstance(msg, bs.HitMessage):
            if msg.hitType != 'punch':
                self.handleMessage(bs.DieMessage())
        else:
            bs.Actor.handleMessage(self, msg)
            
bsPowerup.PowerupFactory = NewPowerupFactory
bsPowerup.Powerup = NewPowerup