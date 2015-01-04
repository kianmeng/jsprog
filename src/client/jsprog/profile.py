
from joystick import InputID, JoystickIdentity, Key
from action import Action, SimpleAction, MouseMove
from util import appendLinesIndented

from xml.sax.handler import ContentHandler
from xml.sax import SAXParseException, make_parser

from xml.dom.minidom import getDOMImplementation

import os
import sys

#------------------------------------------------------------------------------

## @package jsprog.profile
#
# The handling of the profiles

#------------------------------------------------------------------------------

class ProfileHandler(ContentHandler):
    """XML content handler for a profile file."""
    def __init__(self):
        """Construct the parser."""
        self._locator = None

        self._context = []
        self._characterContext = []

        self._profileName = None
        self._autoLoad = False

        self._profile = None

        self._inputID = None
        self._name = None
        self._phys = None
        self._uniq = None

        self._shiftLevel = None
        self._shiftState = None

        self._keyProfile = None
        self._shiftContext = []

        self._action = None
        self._leftShift = False
        self._rightShift = False
        self._leftControl = False
        self._rightControl = False
        self._leftAlt = False
        self._rightAlt = False

    @property
    def profile(self):
        """Get the profile parsed."""
        return self._profile

    @property
    def _parent(self):
        """Get the parent context."""
        return self._context[-1]

    def setDocumentLocator(self, locator):
        """Called to set the locator."""
        self._locator = locator

    def startDocument(self):
        """Called at the beginning of the document."""
        self._context = []
        self._characterContext = []
        self._shiftContext = []
        self._shiftState = None
        self._shiftLevel = None
        self._profile = None

    def startElement(self, name, attrs):
        """Called for each start tag."""
        if name=="joystickProfile":
            if self._context:
                self._fatal("'joystickProfile' should be the top-level element")
            self._startJoystickProfile(attrs)
        elif name=="identity":
            self._checkParent(name, "joystickProfile")
            self._startIdentity(attrs)
        elif name=="inputID":
            self._checkParent(name, "identity")
            self._startInputID(attrs)
        elif name=="name":
            self._checkParent(name, "identity")
            self._startName(attrs)
        elif name=="phys":
            self._checkParent(name, "identity")
            self._startPhys(attrs)
        elif name=="uniq":
            self._checkParent(name, "identity")
            self._startUniq(attrs)
        elif name=="shiftLevels":
            self._checkParent(name, "joystickProfile")
            self._startShiftLevels(attrs)
        elif name=="shiftLevel":
            self._checkParent(name, "shiftLevels")
            self._startShiftLevel(attrs)
        elif name=="shiftState":
            self._checkParent(name, "shiftLevel")
            self._startShiftState(attrs)
        elif name=="keys":
            self._checkParent(name, "joystickProfile")
            self._startKeys(attrs)
        elif name=="key":
            self._checkParent(name, "keys", "shiftState")
            self._startKey(attrs)
        elif name=="shift":
            self._checkParent(name, "key", "shift")
            self._startShift(attrs)
        elif name=="action":
            self._checkParent(name, "key", "shift")
            self._startAction(attrs)
        elif name=="keyCombination":
            self._checkParent(name, "action")
            self._startKeyCombination(attrs)
        else:
            self._fatal("unhandled tag")
        self._context.append(name)
        if len(self._characterContext)<len(self._context):
            self._characterContext.append(None)

    def endElement(self, name):
        """Called for each end tag."""
        del self._context[-1]
        if name=="joystickProfile":
            self._endJoystickProfile()
        elif name=="identity":
            self._endIdentity()
        elif name=="name":
            self._endName()
        elif name=="phys":
            self._endPhys()
        elif name=="uniq":
            self._endUniq()
        elif name=="shiftLevel":
            self._endShiftLevel()
        elif name=="shiftState":
            self._endShiftState()
        elif name=="key":
            self._endKey()
        elif name=="shift":
            self._endShift()
        elif name=="action":
            self._endAction()
        elif name=="keyCombination":
            self._endKeyCombination()

    def characters(self, content):
        """Called for character content."""
        if content.strip():
            self._appendCharacters(content)

    def endDocument(self):
        """Called at the end of the document."""

    @property
    def _shiftLevelIndex(self):
        """Determine the shift level index, i.e. the length of the shift
        context."""
        return len(self._shiftContext)

    @property
    def _handlerTree(self):
        """Get the current handler tree."""
        return self._shiftContext[-1] if self._shiftContext else self._keyProfile

    @property
    def _numExpectedShiftStates(self):
        """Determine the number of expected shift states at the
        current level."""
        shiftLevelIndex = self._shiftLevelIndex
        if shiftLevelIndex<self._profile.numShiftLevels:
            return self._profile.getShiftLevel(shiftLevelIndex).numStates
        else:
            return 0

    def _startJoystickProfile(self, attrs):
        """Handle the joystickProfile start tag."""
        if self._profile is not None:
            self._fatal("there should be only one 'joystickProfile' element")

        self._profileName = self._getAttribute(attrs, "name")
        if not self._profileName:
            self._fatal("the profile's name should not be empty")

        self._autoLoad = self._findBoolAttribute(attrs, "autoLoad")

    def _startIdentity(self, attrs):
        """Handle the identity start tag."""
        if self._profile is not None:
            self._fatal("there should be only one identity")

            self._inputID = None
            self._name = None
            self._phys = None
            self._uniq = None

    def _startInputID(self, attrs):
        """Handle the input ID start tag."""
        busName = self._getAttribute(attrs, "busType")
        busType = InputID.findBusTypeFor(busName)
        if busType is None:
            self._fatal("invalid bus type '%s'" % (busName,))

        vendor = self._getHexAttribute(attrs, "vendor")
        product = self._getHexAttribute(attrs, "product")
        version = self._getHexAttribute(attrs, "version")

        self._inputID = InputID(busType, vendor, product, version)

    def _startName(self, attrs):
        """Handle the name start tag."""
        self._startCollectingCharacters()

    def _endName(self):
        """Handle the name end tag."""
        self._name = self._getCollectedCharacters()

    def _startPhys(self, attrs):
        """Handle the phys start tag."""
        self._startCollectingCharacters()

    def _endPhys(self):
        """Handle the phys end tag."""
        self._phys = self._getCollectedCharacters()

    def _startUniq(self, attrs):
        """Handle the uniq start tag."""
        self._startCollectingCharacters()

    def _endUniq(self):
        """Handle the uniq end tag."""
        uniq = self._getCollectedCharacters()
        self._uniq = uniq if uniq else None

    def _endIdentity(self):
        """Handle the identity end tag."""
        if self._inputID is None:
            self._fatal("the input ID is missing from the identity")
        if self._name is None:
            self._fatal("the name is missing from the identity")
        if self._phys is None:
            self._fatal("the physical location is missing from the identity")
        identity = JoystickIdentity(self._inputID, self._name,
                                    self._phys, self._uniq)
        self._profile = Profile(self._profileName, identity,
                                autoLoad = self._autoLoad)

    def _startShiftLevels(self, attrs):
        """Handle the shiftLevels start tag."""
        if self._profile is None:
            self._fatal("the shift controls should be specified after the identity")
        if self._profile.hasControlProfiles:
            self._fatal("the shift controls should be specified before any control profiles")

    def _startShiftLevel(self, attrs):
        """Handle the shiftLevel start tag."""
        self._shiftLevel = ShiftLevel()

    def _startShiftState(self, attrs):
        """Handle the shiftState start tag."""
        self._shiftState = ShiftState()

    def _endShiftState(self):
        """Handle the shiftState end tag."""
        shiftState = self._shiftState
        if not shiftState.isValid:
            self._fatal("the shift state has conflicting controls")
        if not self._shiftLevel.addState(self._shiftState):
            self._fatal("the shift state is not unique on the level")
        self._shiftState = None

    def _endShiftLevel(self):
        """Handle the shiftLevel end tag."""
        if self._shiftLevel.numStates<2:
            self._fatal("a shift level should have at least two states")
        self._profile.addShiftLevel(self._shiftLevel)
        self._shiftLevel = None

    def _startKeys(self, attrs):
        """Handle the keys start tag."""
        if self._profile is None:
            self._fatal("keys should be specified after the identity")

    def _startKey(self, attrs):
        """Handle the key start tag."""
        code = None
        if "code" in attrs:
            code = self._getIntAttribute(attrs, "code")
        elif "name" in attrs:
            code = Key.findCodeFor(attrs["name"])

        if code is None:
            self._fatal("either a valid code or name is expected")

        if self._parent == "shiftState":
            value = self._getIntAttribute(attrs, "value")
            if value<0 or value>1:
                self._fatal("the value should be 0 or 1 for a key")
            self._shiftState.addControl(KeyShiftControl(code, value))
        else:
            if self._profile.findKeyProfile(code) is not None:
                self._fatal("a profile for the key is already defined")

            self._keyProfile = KeyProfile(code)

    def _startShift(self, attrs):
        """Start a shift handler."""
        shiftLevelIndex = self._shiftLevelIndex
        if shiftLevelIndex>=self._profile.numShiftLevels:
            self._fatal("too many shift handler levels")

        fromState = self._getIntAttribute(attrs, "fromState")
        toState = self._getIntAttribute(attrs, "toState")

        if toState<fromState:
            self._fatal("the to-state should not be less than the from-state")

        shiftLevel = self._profile.getShiftLevel(shiftLevelIndex)
        if (self._handlerTree.lastState+1)!=fromState:
            self._fatal("shift handler states are not contiguous")
        if toState>=shiftLevel.numStates:
            self._fatal("the to-state is too large")

        self._shiftContext.append(ShiftHandler(fromState, toState))

    def _startAction(self, attrs):
        if self._shiftLevelIndex!=self._profile.numShiftLevels:
            self._fatal("missing shift handler levels")

        if self._handlerTree.numChildren>0:
            self._fatal("a shift handler or a key profile can have only one action")

        type = Action.findTypeFor(self._getAttribute(attrs, "type"))
        if type is None:
            self._fatal("invalid type")

        if type==Action.TYPE_SIMPLE:
            self._action = SimpleAction(repeatDelay =
                                        self._findIntAttribute(attrs, "repeatDelay"))
        elif type==Action.TYPE_MOUSE_MOVE:
            direction = \
                MouseMove.findDirectionFor(self._getAttribute(attrs,
                                                              "direction"))
            if direction is None:
                self._fatal("invalid direction")
            self._action = MouseMove(direction = direction,
                                     a = self._findFloatAttribute(attrs, "a"),
                                     b = self._findFloatAttribute(attrs, "b"),
                                     c = self._findFloatAttribute(attrs, "c"),
                                     repeatDelay =
                                     self._findIntAttribute(attrs, "repeatDelay"))
        else:
            self._fatal("unhandled action type")

    def _startKeyCombination(self, attrs):
        """Handle the keyCombination start tag."""
        if self._action.type!=Action.TYPE_SIMPLE:
            self._fatal("a key combination is valid only for a simple action")

        self._leftShift = self._findBoolAttribute(attrs, "leftShift")
        self._rightShift = self._findBoolAttribute(attrs, "rightShift")
        self._leftControl = self._findBoolAttribute(attrs, "leftControl")
        self._rightControl = self._findBoolAttribute(attrs, "rightControl")
        self._leftAlt = self._findBoolAttribute(attrs, "leftAlt")
        self._rightAlt = self._findBoolAttribute(attrs, "rightAlt")
        self._startCollectingCharacters()

    def _endKeyCombination(self):
        """Handle the keyCombination end tag."""
        keyName = self._getCollectedCharacters()
        code = Key.findCodeFor(keyName)
        if code is None:
            self._fatal("no valid code given for the key combination")

        self._action.addKeyCombination(code,
                                       self._leftShift, self._rightShift,
                                       self._leftControl, self._rightControl,
                                       self._leftAlt, self._rightAlt)

    def _endAction(self):
        """End the current action."""
        if self._action.type == Action.TYPE_SIMPLE:
            if not self._action.valid:
                self._fatal("simple action has no key combinations")
        elif self._action.type == Action.TYPE_MOUSE_MOVE:
            pass
        else:
            self._fatal("unhandled action type")

        self._handlerTree.addChild(self._action)

        self._action = None

    def _endShift(self):
        """Handle the shift end tag."""
        shiftHandler = self._shiftContext[-1]

        if not shiftHandler.isComplete(self._numExpectedShiftStates):
            self._fatal("shift handler is missing either child shift level states or an action")

        del self._shiftContext[-1]

        self._handlerTree.addChild(shiftHandler)

    def _endKey(self):
        """Handle the key end tag."""

        if self._parent=="keys":
            if not self._keyProfile.isComplete(self._numExpectedShiftStates):
                self._fatal("the key profile is missing either child shift level states or an action")

            self._profile.addKeyProfile(self._keyProfile)
            self._keyProfile = None

    def _endJoystickProfile(self):
        """Handle the joystickProfile end tag."""
        if self._profile is None:
            self._fatal("empty 'joystickProfile' element")

    def _startCollectingCharacters(self):
        """Indicate that we can collect characters with the current
        tag."""
        self._characterContext.append("")

    def _getCollectedCharacters(self):
        """Get the collected characters, if any."""
        characters = self._characterContext[-1]
        assert characters is not None

        return characters.strip()

    def _appendCharacters(self, chars):
        """Append the given characters to the collected ones.

        If we are not allowed to callect, raise a fatal exception."""
        if self._characterContext[-1] is None:
            self._fatal("characters are not allowed here")
        self._characterContext[-1] += chars

    def _checkParent(self, element, *args):
        """Check if the last element of the context is the given
        one."""
        for parent in args:
            if self._context[-1]==parent:
                return

        self._fatal("tag '%s' should appear within any of %s" %
                    (element, ",".join(args)))

    def _findAttribute(self, attrs, name, default = None):
        """Find the attribute with the given name.

        If not found, return the given default value."""
        return attrs.get(name, default)

    def _getAttribute(self, attrs, name):
        """Get the attribute with the given name.

        If not found, raise a fatal error."""
        value = self._findAttribute(attrs, name)
        if value is None:
            self._fatal("expected attribute '%s'" % (name,))
        return value

    def _findParsableAttribute(self, attrs, name, parser, default = None):
        """Find the value of the given attribute if it should be
        parsed to produce a meaningful value.

        If the attribute is not found, return the given default
        value."""
        value = self._findAttribute(attrs, name)
        return default if value is None else parser(name, value)

    def _getParsableAttribute(self, attrs, name, parser):
        """Get the value of the given attribute if it should be
        parsed to produce a meaningful value.

        If the attribute is not found, raise a fatal error."""
        return parser(name, self._getAttribute(attrs, name))

    def _parseHexAttribute(self, name, value):
        """Parse the given hexadecimal value being the value of the
        attribute with the given name.

        If the parsing fails, raise a fatal error."""
        try:
            return int(value, 16)
        except:
            self._fatal("value of attribute '%s' should be a hexadecimal number" % (name,))

    def _findHexAttribute(self, attrs, name, default = None):
        """Find the value of the given attribute interpreted as a
        hexadecimal number."""
        return self._findParsableAttribute(attrs, name,
                                           self._parseHexAttribute,
                                           default = default)

    def _getHexAttribute(self, attrs, name):
        """Get the value of the given attribute interpreted as a
        hexadecimal number."""
        return self._getParsableAttribute(attrs, name,
                                          self._parseHexAttribute)

    def _parseIntAttribute(self, name, value):
        """Parse the given hexadecimal value being the value of the
        attribute with the given name.

        If the parsing fails, raise a fatal error."""
        try:
            if value.startswith("0x"):
                return int(value[2:], 16)
            elif value.startswith("0") and len(value)>1:
                return int(value[1:], 8)
            else:
                return int(value)
        except Exception, e:
            self._fatal("value of attribute '%s' should be an integer" % (name,))

    def _findIntAttribute(self, attrs, name, default = None):
        """Find the value of the given attribute interpreted as a
        decimal, octal or hexadecimal integer.

        If the attribute is not found, return the given default value."""
        return self._findParsableAttribute(attrs, name,
                                           self._parseIntAttribute,
                                           default = default)

    def _getIntAttribute(self, attrs, name):
        """Get the value of the given attribute interpreted as a
        decimal, octal or hexadecimal integer."""
        return self._getParsableAttribute(attrs, name, self._parseIntAttribute)

    def _parseBoolAttribute(self, name, value):
        """Parse the given boolean value being the value of the
        attribute with the given name.

        If the parsing fails, raise a fatal error."""
        value = value.lower()
        if value in ["yes", "true"]:
            return True
        elif value in ["no", "false"]:
            return False
        else:
            self._fatal("value of attribute '%s' should be a boolean" % (name,))

    def _findBoolAttribute(self, attrs, name, default = False):
        """Find the value of the given attribute interpreted as a
        boolean.

        If the attribute is not found, return the given default value."""
        return self._findParsableAttribute(attrs, name,
                                           self._parseBoolAttribute,
                                           default = default)

    def _getBoolAttribute(self, attrs, name):
        """Get the value of the given attribute interpreted as a boolean."""
        return self._getParsableAttribute(attrs, name, self._parseBoolAttribute)

    def _parseFloatAttribute(self, name, value):
        """Parse the given double value being the value of the
        attribute with the given name.

        If the parsing fails, raise a fatal error."""
        try:
            return float(value)
        except Exception, e:
            self._fatal("value of attribute '%s' should be a floating-point number" % (name,))

    def _findFloatAttribute(self, attrs, name, default = 0.0):
        """Find the value of the given attribute interpreted as a
        floating-point value.

        If the attribute is not found, return the given default value."""
        return self._findParsableAttribute(attrs, name,
                                           self._parseFloatAttribute,
                                           default = default)

    def _getFloatAttribute(self, attrs, name):
        """Get the value of the given attribute interpreted as a
        floating-point value."""
        return self._getParsableAttribute(attrs, name, self._parseFloatAttribute)

    def _fatal(self, msg, exception = None):
        """Raise a parse exception with the given message and the
        current location."""
        raise SAXParseException(msg, exception, self._locator)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftControl(object):
    """Base class for the shift controls."""
    ## Shift control type: a simple key
    TYPE_KEY = 1

    def __init__(self, type):
        """Construct the shift control with the given type."""
        self._type = type

    @property
    def type(self):
        """Get the type of the control."""
        return self._type

    def __cmp__(self, other):
        """Compare this control with the other one.

        This function checks only the type. Child classes should override it to
        refine the comparison if the types are found to be the same."""
        return cmp(self._type, other._type)

#------------------------------------------------------------------------------

class KeyShiftControl(ShiftControl):
    """A shift control which is a simple key."""

    def __init__(self, code, value = 1):
        """Construct the key shift control for the key with the given
        code."""
        super(KeyShiftControl, self).__init__(ShiftControl.TYPE_KEY)
        self._code = code
        self._value = value

    @property
    def code(self):
        """Get the code of the key this shift control represents."""
        return self._code

    @property
    def value(self):
        """Get the value that is expected by the shift state."""
        return self._value

    @property
    def isDefault(self):
        """Determine if this control matches the default value, i.e. 0"""
        return self._value == 0

    def doesConflict(self, other):
        """Determine if this control conflicts with the given other one.

        The two controls conflict if they are both keys but refer to different
        values."""
        return self._type==other._type and self._code==other._code and \
            self._value!=other._value

    def __cmp__(self, other):
        """Compare this control with the other one.

        If they are of the same type, the code and then the values are
        compared."""
        x = super(KeyShiftControl, self).__cmp__(other)
        if x==0:
            x = cmp(self._code, other._code)
        if x==0:
            x = cmp(self._value, other._value)
        return x

    def getXML(self, document):
        """Get an XML element describing this control."""
        element = document.createElement("key")
        element.setAttribute("name", Key.getNameFor(self._code))
        element.setAttribute("value", str(self._value))
        return element

    # def getStateLuaCode(self, variableName):
    #     """Get the Lua code acquiring the shift state into a local
    #     variable with the given name.

    #     Retuns the lines of code."""
    #     lines = []
    #     lines.append("local %s" % (variableName,))
    #     lines.append("local %s_pressed = jsprog_iskeypressed(%d)" %
    #                  (variableName, self._code))
    #     lines.append("if %s_pressed then %s=1 else %s=0 end" %
    #                  (variableName, variableName, variableName))
    #     return lines

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftState(object):
    """A shift state.

    A shift state corresponds to a certain values of one or more controls, such
    as keys (buttons). For example, a shift state can be if the pinkie button
    is pressed.

    There can be an empty shift state, meaning that the shift level is in that
    state if no other state is matched."""
    def __init__(self):
        """Construct the shift state."""
        self._controls = []

    @property
    def isValid(self):
        """Determine if the state is valid.

        A state is valid if it does not contain controls that refer to
        the same control but conflicting values."""
        numControls = len(self._controls)
        for i in range(0, numControls - 1):
            control = self._controls[i]
            for j in range(i+1, numControls):
                if control.doesConflict(self._controls[j]):
                    return False
        return True

    def addControl(self, shiftControl):
        """Add a shift control to the state."""
        self._controls.append(shiftControl)
        self._controls.sort()

    def getXML(self, document):
        """Get an XML element describing this shift state."""
        element = document.createElement("shiftState")

        for control in self._controls:
            element.appendChild(control.getXML(document))

        return element

    def __cmp__(self, other):
        """Compare this shift state with the other one.

        If this an empty state, it matches any other state that is also empty
        or contains only controls that match the default value."""
        if self._controls:
            if other._controls:
                x = cmp(len(self._controls), len(other._controls))
                if x==0:
                    for index in range(0, len(self._controls)):
                        x = cmp(self._controls[index], other._controls[index])
                        if x!=0: break
                return x
            else:
                return -cmp(other, self)
        else:
            for control in other._controls:
                if not control.isDefault:
                    return -1
            return 0

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftLevel(object):
    """A level in the shift tree.

    A shift level consists of a number of shift states corresponding to certain
    states of certain controls on the joystick."""
    def __init__(self):
        """Construct the shift level."""
        self._states = []

    @property
    def numStates(self):
        """Get the number of states."""
        return len(self._states)

    def addState(self, shiftState):
        """Try to add a shift state to the level.

        It first checks if the shift state is different from every other state.
        If not, False is returned. Otherwise the new state is added and True is
        returned."""
        for state in self._states:
            if shiftState==state:
                return False

        self._states.append(shiftState)
        return True

    def getXML(self, document):
        """Get an XML element describing this shift level."""
        element = document.createElement("shiftLevel")

        for state in self._states:
            element.appendChild(state.getXML(document))

        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class HandlerTree(object):
    """The root of a tree of shift handlers and actions."""
    def __init__(self):
        """Construct an empty tree."""
        self._children = []

    @property
    def children(self):
        """Get the list of child handlers of the shift handler."""
        return self._children

    @property
    def numChildren(self):
        """Get the number of children."""
        return len(self._children)

    @property
    def lastState(self):
        """Get the last state handled by the children, if they are
        shift handlers.

        If there are no children, -1 is returned."""
        return self._children[-1]._toState if self._children else -1

    @property
    def needCancelThreadOnRelease(self):
        """Determine if a thread created when a control was activated
        needs to be cancelled when releasing the control."""
        for child in self._children:
            if child.needCancelThreadOnRelease:
                return True

        return False

    def addChild(self, handler):
        """Add a child handler."""
        assert \
            (isinstance(handler, Action) and not
             self._children) or \
            (isinstance(handler, ShiftHandler) and
             handler._fromState == (self.lastState+1))

        self._children.append(handler)

    def isComplete(self, numStates = 0):
        """Determine if the tree is complete.

        numStates is the number of states expected at the tree's
        level. If the tree contains a clear handler, numStates is 0,
        and the tree is complete if there is one key
        handler. Otherwise the last state should equal to the number
        of states - 1."""
        return len(self._children)==1 if numStates==0 \
            else (self.lastState+1)==numStates

    def getLuaCode(self, profile, shiftLevel = 0):
        """Get the Lua code for this handler tree.

        profile is the joystick profile and shiftLevel is the level in
        the shift tree.

        Return the lines of code."""
        if shiftLevel<profile.numShiftControls:
            numChildren = self.numChildren
            if numChildren==1:
                return self._children[0].getLuaCode(profile,
                                                    shiftLevel + 1)
            else:
                shiftControl = profile.getShiftControl(shiftLevel)
                shiftStateName = "_jsprog_shift_%d" % (shiftLevel,)
                lines = shiftControl.getStateLuaCode(shiftStateName)
                index = 0
                for index in range(0, numChildren):
                    shiftHandler = self._children[index]
                    ifStatement = "if" if index==0 else "elseif"
                    if index==(numChildren-1):
                        lines.append("else")
                    elif shiftHandler.fromState==shiftHandler.toState:
                        lines.append("%s %s==%d then" % (ifStatement,
                                                         shiftStateName,
                                                         shiftHandler.fromState))
                    else:
                        lines.append("%s %s>=%d and %s<=%d then" %
                                     (ifStatement,
                                      shiftStateName, shiftHandler.fromState,
                                      shiftStateName, shiftHandler.toState))

                    handlerCode = shiftHandler.getLuaCode(profile,
                                                          shiftLevel + 1)
                    appendLinesIndented(lines, handlerCode)

                lines.append("end")

                return lines
        else:
            return self._children[0].getLuaCode()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftHandler(HandlerTree):
    """Handler for a certain value or set of values for a shift
    control.

    Zero or more shift controls can be specified each having a value
    from 0 to a certain positive value (e.g. 1 in case of a key (i.e. button) -
    0=not pressed, 1=pressed). The shift controls are specified in a
    certain order and thus they form a hierarchy.

    For each key or other control the actual handlers should be
    specified in the context of the shift state. This context is
    defined by a hierarchy of shift handlers corresponding to the
    hierarchy of shift controls.

    Let's assume, that button A is the first shift control in the
    list, and button B is the second. Then for each key we have one
    ore more shift handlers describing one or more states
    (i.e. released and/or pressed) for button A. Each such shift
    handler contains one or more similar shift handlers for button
    B. The shift handlers for button B contain the actual key
    handlers.

    A shift handler may specify more than one possible states for the
    shift control, and it may specify all states, making the shift
    control irrelevant for the key as only the other shift controls,
    if any, determine what the key does. Thus, by carefully ordering
    the shift controls, it is possible to eliminate repetitions of key
    handlers.

    It should be noted, that in the XML profile, the shift handlers
    for one level should follow each other in the order of the states,
    and all states should be covered at each level. Otherwise the
    profile is rejected by the parser."""
    def __init__(self, fromState, toState):
        """Construct the shift handler to handle the states between
        the given ones (both inclusive)."""
        assert toState >= fromState

        super(ShiftHandler, self).__init__()

        self._fromState = fromState
        self._toState = toState

    @property
    def fromState(self):
        """Get the starting state for the shift handler."""
        return self._fromState

    @property
    def toState(self):
        """Get the ending state for the shift handler."""
        return self._toState


    def getXML(self, document):
        """Get the XML element describing this shift handler."""
        element = document.createElement("shift")
        element.setAttribute("fromState", str(self._fromState))
        element.setAttribute("toState", str(self._toState))

        for child in self._children:
            element.appendChild(child.getXML(document))

        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class KeyProfile(HandlerTree):
    """The profile for a key.

    It maintains a tree of handlers the leaves of which are key
    handlers, and the other nodes (if any) are shift handlers each
    level of them corresponding to a shift control."""
    def __init__(self, code):
        """Construct the key profile for the given key code."""
        super(KeyProfile, self).__init__()

        self._code = code

    @property
    def code(self):
        """Get the code of the key."""
        return self._code

    def getXML(self, document):
        """Get the XML element describing the key profile."""
        element = document.createElement("key")
        element.setAttribute("name", Key.getNameFor(self._code))

        for child in self._children:
            element.appendChild(child.getXML(document))

        return element

    def getDaemonXML(self, document, profile):
        """Get the XML element for the XML document to be sent to the
        daemon."""
        element = document.createElement("key")

        element.setAttribute("name", Key.getNameFor(self.code))

        luaCode = appendLinesIndented([], self.getLuaCode(profile),
                                      indentation = "    ")
        luaText = "\n" + "\n".join(luaCode) + "\n"

        element.appendChild(document.createTextNode(luaText))

        return element

    def getLuaCode(self, profile):
        """Get the Lua code for the key."""
        lines = []
        lines.append("if value~=0 then")

        appendLinesIndented(lines,
                            super(KeyProfile, self).getLuaCode(profile))

        if self.needCancelThreadOnRelease:
            lines.append("else")
            lines.append("  jsprog_cancelprevious()")

        lines.append("end")

        return lines

#------------------------------------------------------------------------------

class Profile(object):
    """A joystick profile."""
    @staticmethod
    def loadFrom(directory):
        """Load the profiles in the given directory.

        Returns a list of the loaded profiles."""
        profiles = []

        parser = make_parser()

        handler = ProfileHandler()
        parser.setContentHandler(handler)

        for entry in os.listdir(directory):
            path = os.path.join(directory, entry)
            if entry.endswith(".profile") and os.path.isfile(path):
                try:
                    parser.parse(path)
                    profiles.append(handler.profile)
                except Exception, e:
                    print >> sys.stderr, e

        return profiles

    @staticmethod
    def getTextXML(document, name, text):
        """Create a tag with the given name containing the given
        text."""
        element = document.createElement(name)
        value = document.createTextNode(text)
        element.appendChild(value)
        return element

    @staticmethod
    def getInputIDXML(document, inputID):
        """Get the XML representation of the given input ID."""
        inputIDElement = document.createElement("inputID")

        inputIDElement.setAttribute("busType", inputID.busName)
        inputIDElement.setAttribute("vendor", "%04x" % (inputID.vendor,))
        inputIDElement.setAttribute("product", "%04x" % (inputID.product,))
        inputIDElement.setAttribute("version", "%04x" % (inputID.version,))

        return inputIDElement

    @staticmethod
    def getIdentityXML(document, identity):
        """Get the XML representation of the given identity."""
        identityElement = document.createElement("identity")

        inputIDElement = Profile.getInputIDXML(document, identity.inputID)
        identityElement.appendChild(inputIDElement)

        identityElement.appendChild(Profile.getTextXML(document,
                                                       "name",
                                                       identity.name))

        identityElement.appendChild(Profile.getTextXML(document,
                                                       "phys",
                                                       identity.phys))

        if identity.uniq is not None:
            identityElement.appendChild(Profile.getTextXML(document,
                                                           "uniq",
                                                           identity.uniq))

        return identityElement

    def __init__(self, name, identity, autoLoad = False):
        """Construct an empty profile for the joystick with the given
        identity."""
        self.name = name
        self.identity = identity
        self.autoLoad = autoLoad

        self._shiftLevels = []

        self._keyProfiles = []
        self._keyProfileMap = {}

    @property
    def hasControlProfiles(self):
        """Determine if we have control (key or axis) profiles or not."""
        return bool(self._keyProfiles)

    @property
    def numShiftLevels(self):
        """Determine the number of shift levels."""
        return len(self._shiftLevels)

    def match(self, identity):
        """Get the match level for the given joystick identity."""
        return self.identity.match(identity)

    def addShiftLevel(self, shiftLevel):
        """Add the given shift level to the profile."""
        self._shiftLevels.append(shiftLevel)

    def getShiftLevel(self, index):
        """Get the shift level at the given index."""
        return self._shiftLevels[index]

    def addKeyProfile(self, keyProfile):
        """Add the given key profile to the list of key profiles."""
        self._keyProfiles.append(keyProfile)
        self._keyProfileMap[keyProfile.code] = keyProfile

    def findKeyProfile(self, code):
        """Find the key profile for the given code.

        Returns the key profile or None if, not found."""
        return self._keyProfileMap.get(code)

    def getXMLDocument(self):
        """Get the XML document describing the profile."""
        document = getDOMImplementation().createDocument(None,
                                                         "joystickProfile",
                                                         None)
        topElement = document.documentElement
        topElement.setAttribute("name", self.name)
        topElement.setAttribute("autoLoad",
                                "yes" if self.autoLoad else "no")

        identityElement = Profile.getIdentityXML(document, self.identity)
        topElement.appendChild(identityElement)

        if self._shiftLevels:
            shiftLevelsElement = document.createElement("shiftLevels")
            for shiftLevel in self._shiftLevels:
                shiftLevelsElement.appendChild(shiftLevel.getXML(document))
            topElement.appendChild(shiftLevelsElement)

        if self._keyProfiles:
            keysElement = document.createElement("keys")
            for keyProfile in self._keyProfiles:
                keysElement.appendChild(keyProfile.getXML(document))
            topElement.appendChild(keysElement)

        return document

    def getDaemonXMLDocument(self):
        """Get the XML document to be downloaded to the daemon."""
        document = getDOMImplementation().createDocument(None,
                                                         "jsprogProfile",
                                                         None)
        topElement = document.documentElement

        prologueElement = document.createElement("prologue")
        topElement.appendChild(prologueElement)

        for keyProfile in self._keyProfiles:
            topElement.appendChild(keyProfile.getDaemonXML(document, self))

        epilogueElement = document.createElement("epilogue")
        topElement.appendChild(epilogueElement)

        return document

#------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = make_parser()

    handler = ProfileHandler()
    parser.setContentHandler(handler)

    parser.parse(sys.argv[1])

    profile = handler.profile

    document = profile.getXMLDocument()
    #document = profile.getDaemonXMLDocument()

    with open("profile.xml", "wt") as f:
        document.writexml(f, addindent = "  ", newl = "\n")

#------------------------------------------------------------------------------
