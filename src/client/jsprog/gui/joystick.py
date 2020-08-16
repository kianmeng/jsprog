
from .statusicon import StatusIcon
from .jswindow import JSWindow
from .scndpopover import JSSecondaryPopover
from .jsctxtmenu import JSContextMenu
from .common import *
from .common import _

import jsprog.joystick
import jsprog.device
import jsprog.parser
from jsprog.profile import Profile

import pathlib

#------------------------------------------------------------------------------

## @package jsprog.gui.joystick
#
# The GUI-specific representation of joysticks

#-----------------------------------------------------------------------------

class JoystickType(jsprog.device.JoystickType, GObject.Object):
    """A joystick type descriptor.

    This class maintains a registry for joystick types based on their input
    IDs. It also contains the profiles defined for that certain joystick
    type."""
    # The name of the joystick type descriptor file
    _typeDescriptorName = "type.xml"

    # A mapping of input IDs to joystick type instances
    _instances = {}

    @staticmethod
    def get(gui, identity, keys, axes):
        """Get the joystick type for the given identity."""
        inputID = identity.inputID
        if inputID not in JoystickType._instances:
            print("Creating a new joystick type for %s" % (identity,))
            joystickType = None
            for (path, directoryType) in JoystickType.getDeviceDirectories(gui,
                                                                           identity):
                typeDescriptorPath = os.path.join(path,
                                                  JoystickType._typeDescriptorName)
                if os.path.isfile(typeDescriptorPath):
                    joystickType = JoystickType.fromFile(typeDescriptorPath,
                                                         gui)
                    if joystickType is not None:
                        print("Loaded joystick type from", typeDescriptorPath)
                        joystickType.userDefined = directoryType=="user"
                        break

            if joystickType is None:
                joystickType = JoystickType(identity, gui)
                for key in keys:
                    joystickType.addKey(key.code)
                for axis in axes:
                    joystickType.addAxis(axis.code, axis.minimum, axis.maximum)

            joystickType._loadProfiles()

            JoystickType._instances[inputID] = joystickType
        else:
            print("Using existing joystick type for %s" % (identity,))

        return JoystickType._instances[inputID]

    @staticmethod
    def getDeviceSubdirectoryName(identity):
        """Get the name of device-specific subdirectory for a joystick with the
        given identity."""
        inputID = identity.inputID
        return "%sV%04xP%04x" % (inputID.busName, inputID.vendor,
                                 inputID.product)


    @staticmethod
    def getDeviceDirectoryFor(parentDirectory, identity):
        """Get the device directory for the given parent directory."""
        return os.path.join(parentDirectory, "devices",
                            JoystickType.getDeviceSubdirectoryName(identity))

    @staticmethod
    def getDeviceDirectories(gui, identity):
        """Get an iterator over the directories potentially containing files
        related to a device with the given identity.

        Each item is a tuple of:
        - the path of the directory
        - the type of the directory as a string (see GUI.dataDirectories)
        """
        for (path, directoryType) in gui.dataDirectories:
            yield (JoystickType.getDeviceDirectoryFor(path, identity),
                   directoryType)

    @staticmethod
    def getUserDeviceDirectory(gui, identity):
        """Get the user's device directory for the joystick type with the given
        identity."""
        return JoystickType.getDeviceDirectoryFor(gui.userDataDirectory,
                                                  identity)

    def __init__(self, identity, gui):
        """Construct a joystick type for the given identity."""
        super().__init__(identity)
        GObject.Object.__init__(self)

        self._gui = gui

        self.userDefined = False

        self._profiles = {}
        self._changed = False

    @property
    def profiles(self):
        """Get an iterator over the profiles in this joystick type."""
        return iter(self._profiles.values())

    @property
    def userDeviceDirectory(self):
        """Get the user's device directory for this joystick type."""
        return JoystickType.getUserDeviceDirectory(self._gui, self.identity)

    @property
    def deviceDirectories(self):
        """Get an iterator of the device directories for this joystick type."""
        for data in JoystickType.getDeviceDirectories(self._gui,
                                                      self.identity):
            yield data

    @property
    def changed(self):
        """Indicate if the joystick type has changed."""
        return self._changed

    def isDeviceDirectory(self, directory):
        """Determine if the given diretctory is a device directory for this
        joystick type."""
        for (deviceDirectory, _type) in self.deviceDirectories:
            if directory==deviceDirectory:
                return True

        return False

    def setKeyDisplayName(self, code, displayName):
        """Set the display name of the key with the given code.

        A key-display-name-changed signal will also be emitted, if the key
        indeed exists and the display name is different."""
        key = self.findKey(code)
        if key is not None and key.displayName!=displayName:
            key.displayName = displayName
            self._changed = True
            self.emit("key-display-name-changed", code, displayName)
            self.save()

    def setAxisDisplayName(self, code, displayName):
        """Set the display name of the axis with the given code.

        An axis-display-name-changed signal will also be emitted, if the axis
        indeed exists and the display name is different."""
        axis = self.findAxis(code)
        if axis is not None and axis.displayName!=displayName:
            axis.displayName = displayName
            self._changed = True
            self.emit("axis-display-name-changed", code, displayName)
            self.save()

    def newView(self, viewName, imageFileName):
        """Add a view to the joystick type with the given name and image file
        name.

        A view-added signal will also be emitted."""

        if self.findView(viewName) is None:
            view = jsprog.device.View(viewName, imageFileName)
            super().addView(view)
            self.emit("view-added", viewName)
            self._changed = True
            self.save()
            return view

    def changeViewName(self, origViewName, newViewName):
        """Change the name of the view with the given name to the given new
        name, if no other view with the same name exists.

        A view-name-changed signal will also be emitted."""
        if origViewName==newViewName:
            return False

        view = self.findView(origViewName)
        if view is None:
            return False

        if self.findView(newViewName) is not None:
            return False

        view.name = newViewName
        self.emit("view-name-changed", origViewName, newViewName)
        self._changed = True
        self.save()
        return True

    def getHotspotLabel(self, hotspot):
        """Get the label for the given hotspot, i.e. the name of the
        corresponding control."""
        if hotspot.controlType==jsprog.device.Hotspot.CONTROL_TYPE_KEY:
            return self.findKey(hotspot.controlCode).displayName
        elif hotspot.controlType==jsprog.device.Hotspot.CONTROL_TYPE_AXIS:
            return self.findAxis(hotspot.controlCode).displayName

    def addViewHotspot(self, view, hotspot):
        """Add the given hotspot to the given view.

        A hotspot-added signal will be emitted."""
        view.addHotspot(hotspot)
        self._changed = True
        self.emit("hotspot-added", view, hotspot)
        self.save()

    def modifyViewHotspot(self, view, origHotspot, newHotspot):
        """Modify the given original hotspot of the view by replacing it with
        the new hotspot.

        A hotspot-modified signal will be emitted."""
        view.modifyHotspot(origHotspot, newHotspot)
        self._changed = True
        self.emit("hotspot-modified", view, origHotspot, newHotspot)
        self.save()

    def removeViewHotspot(self, view, hotspot):
        """Delete the given hotspot from the given view.

        A hotspot-removed signal will be emitted."""
        view.removeHotspot(hotspot)
        self._changed = True
        self.emit("hotspot-removed", view, hotspot)
        self.save()

    def updateViewHotspotCoordinates(self, hotspot, x, y):
        """Update the coordinates of the hotspot from the given image-related
        ones.

        A hotspot-moved signal will be emitted."""
        hotspot.x = round(x)
        hotspot.y = round(y)
        self._changed = True
        self.emit("hotspot-moved", hotspot)
        self.save()

    def updateViewHotspotDotCoordinates(self, hotspot, x, y):
        """Update the coordinates of the hotspot's dot from the given
        image-related ones.

        A hotspot-moved signal will be emitted."""
        hotspot.dot.x = round(x)
        hotspot.dot.y = round(y)
        self._changed = True
        self.emit("hotspot-moved", hotspot)
        self.save()

    def deleteView(self, viewName):
        """Delete the view with the given name.

        A view-removed signal will also be emitted."""
        view = self.findView(viewName)
        if view is not None:
            super().removeView(view)
            self._changed = True
            self.save()
            self.emit("view-removed", viewName)

    def newVirtualControl(self, name, displayName,
                          baseControlType, baseControlCode):
        """Add a virtual control with the given name and display name.

        If the addition is successful, the virtualControl-added signal is
        emitted."""
        virtualControl = self.addVirtualControl(name, displayName)
        if virtualControl is not None:
            control = jsprog.parser.Control(baseControlType, baseControlCode)
            if baseControlType==jsprog.parser.Control.TYPE_KEY:
                state = jsprog.device.DisplayVirtualState("State 1")
                state.addConstraint(jsprog.parser.SingleValueConstraint(control, 0))
                virtualControl.addState(state)

                state = jsprog.device.DisplayVirtualState("State 2")
                state.addConstraint(jsprog.parser.SingleValueConstraint(control, 1))
                virtualControl.addState(state)
            elif baseControlType==jsprog.parser.Control.TYPE_AXIS:
                axis = self.findAxis(baseControlCode)
                middle = (axis.minimum + axis.maximum) // 2

                state = jsprog.device.DisplayVirtualState("State 1")
                state.addConstraint(
                    jsprog.parser.ValueRangeConstraint(control, axis.minimum,
                                                       middle) if
                    axis.minimum<middle else
                    jsprog.parser.SingleValueConstraint(control, axis.minimum))
                virtualControl.addState(state)

                middle += 1
                state = jsprog.device.DisplayVirtualState("State 2")
                state.addConstraint(
                    jsprog.parser.ValueRangeConstraint(control, middle,
                                                       axis.maximum) if
                    middle<axis.maximum else
                    jsprog.parser.SingleValueConstraint(control, axis.maximum))
                virtualControl.addState(state)

            else:
                assert False

            self._changed = True
            self.save()
            self.emit("virtualControl-added", virtualControl)

        return virtualControl

    def setVirtualControlName(self, virtualControl, newName):
        """Try to set the name of the given virtual control.

        It is checked if the name is correct, and if not, False is returned.
        It is then checked if another virtual control has the given name. If so,
        False is returned. Otherwise the change is performed and the
        virtualControl-name-changed signal is emitted."""
        if not jsprog.parser.VirtualControl.checkName(newName):
            return False

        vc = self.findVirtualControl(newName)
        if vc is None:
            virtualControl.name = newName
            self._changed = True
            self.save()
            self.emit("virtualControl-name-changed", virtualControl, newName)
            return True
        else:
            return vc is virtualControl

    def setVirtualControlDisplayName(self, virtualControl, newName):
        """Try to set the name of the given virtual control.

        It is checked if another virtual control has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualControl-display-name-changed signal is emitted."""
        if not newName:
            return False

        vc = self.findVirtualControlByDisplayName(newName)
        if vc is None:
            virtualControl.displayName = newName
            self._changed = True
            self.save()
            self.emit("virtualControl-display-name-changed",
                      virtualControl, newName)
            return True
        else:
            return vc is virtualControl

    def deleteVirtualControl(self, virtualControl):
        """Remove the given virtual control.

        The virtualControl-removed signal is emitted."""
        self.removeVirtualControl(virtualControl)
        self._changed = True
        self.save()
        self.emit("virtualControl-removed",
                  virtualControl.name)

    def getControlDisplayName(self, control):
        """Get the display name of the given control."""
        if control.isKey:
            key = self.findKey(control.code)
            if key is not None:
                return key.displayName
        elif control.isAxis:
            axis =  self.findAxis(control.code)
            if axis is not None:
                return axis.displayName
        elif control.isVirtual:
            vc = self.findVirtualControlByCode(control.code)
            if vc is not None:
                return vc.displayName

        return control.name

    def newVirtualState(self, virtualControl, virtualState):
        """Add the given virtual state to the given virtual control.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualState-added signal is emitted."""
        if virtualControl.findStateByDisplayName(virtualState.displayName) is not None:
            return False

        if not virtualControl.addState(virtualState):
            return False

        self._changed = True
        self.save()

        self.emit("virtualState-added", virtualControl, virtualState)

        return True

    def setVirtualStateDisplayName(self, virtualControl, virtualState, newName):
        """Set the display name of the given virtual state of the given virtual
        control.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualState-display-name-changed signal is emitted."""
        if not newName:
            return False

        state = virtualControl.findStateByDisplayName(newName)
        if state is None:
            virtualState.displayName = newName
            self._changed = True
            self.save()
            self.emit("virtualState-display-name-changed",
                      virtualControl, virtualState, newName)
            return True
        else:
            return state is virtualState

    def setVirtualStateConstraints(self, virtualControl, virtualState,
                                   newConstraints):
        """Set the constraints of the given virtual state of the given virtual
        control.

        The virtualState-constraints-changed signal is emitted."""
        # FIXME: implement a check for equivalence
        virtualState.clearConstraints()
        for constraint in newConstraints:
            virtualState.addConstraint(constraint)

        self._changed = True
        self.save()
        self.emit("virtualState-constraints-changed",
                  virtualControl, virtualState)

    def deleteVirtualState(self, virtualControl, virtualState):
        """Remove the given virtual state of the vien virtual control.

        The virtualState-removed signal is emitted."""
        virtualControl.removeState(virtualState)

        self._changed = True
        self.save()
        self.emit("virtualState-removed",
                  virtualControl, virtualState.displayName)

    def save(self):
        """Save the joystick type into the user's directory."""
        directoryPath = JoystickType.getUserDeviceDirectory(self._gui,
                                                            self._identity)


        pathlib.Path(directoryPath).mkdir(parents = True, exist_ok = True)

        try:
            self.saveInto(os.path.join(directoryPath, self._typeDescriptorName))
            self._changed = False
        except Exception as e:
            self.emit("save-failed", e)

    def getNextControl(self, lastControlType, lastControlCode):
        """Get the control coming after the given type and code pair.

        If either of them is None, the first control is returned."""
        controlType = None
        controlCode = None
        if lastControlType is not None and lastControlCode is not None:
            afterPrevious = False
            if lastControlType == jsprog.parser.Control.TYPE_KEY:
                for key in self.iterKeys:
                    if afterPrevious:
                        controlType = jsprog.parser.Control.TYPE_KEY
                        controlCode = key.code
                        afterPrevious = False
                        break
                    elif key.code==lastControlCode:
                        afterPrevious = True

            if controlType is None:
                for axis in self.iterAxes:
                    if afterPrevious:
                        controlType = jsprog.parser.Control.TYPE_AXIS
                        controlCode = axis.code
                        afterPrevious = False
                        break
                    elif axis.code==lastControlCode:
                        afterPrevious = True

        if controlType is None:
            firstKey = self.firstKey
            if firstKey is None:
                controlType = jsprog.parser.Control.TYPE_AXIS
                controlCode = self.firstAxis.code
            else:
                controlType = jsprog.parser.Control.TYPE_KEY
                controlCode = firstKey.code

        return (controlType, controlCode)

    def _loadProfiles(self):
        """Load the profiles for this joystick type."""
        self._profiles = {}

        for (path, directoryType) in self.getDeviceDirectories(self._gui,
                                                               self.identity):
            if os.path.isdir(path):
                for profile in Profile.loadFrom(path):
                    score = profile.match(self.identity)
                    if score>0:
                        name = profile.name
                        if name in self._profiles:
                            print("A profile with name '%s' already exists, ignoring the one from directory %s" % (name, path), file = sys.stderr)
                            continue
                        profile.directoryType = directoryType

                        self._profiles[name] = profile
                        profile.userDefined = directoryType=="user"

#-----------------------------------------------------------------------------

GObject.signal_new("key-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (int, str))

GObject.signal_new("axis-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (int, str))

GObject.signal_new("view-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

GObject.signal_new("view-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str, str))

GObject.signal_new("hotspot-moved", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("hotspot-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("hotspot-modified", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, object))

GObject.signal_new("hotspot-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("view-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

GObject.signal_new("virtualControl-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("virtualControl-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str))

GObject.signal_new("virtualControl-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str))

GObject.signal_new("virtualControl-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

GObject.signal_new("virtualState-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object,))

GObject.signal_new("virtualState-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, str))

GObject.signal_new("virtualState-constraints-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("virtualState-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str,))

GObject.signal_new("save-failed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

#-----------------------------------------------------------------------------

class Joystick(object):
    """A joystick on the GUI."""
    def __init__(self, id, identity, type, gui):
        """Construct the joystick with the given attributes."""
        self._id = id
        self._identity = identity
        self._type = type
        self._gui = gui

        self._statusIcon = StatusIcon(id, self, gui)

        iconTheme = Gtk.IconTheme.get_default()
        icon = iconTheme.load_icon("gtk-preferences", 64, 0)
        self._iconRef = JSWindow.get().addJoystick(self, icon, identity.name)

        self._profiles = []
        self._autoLoadProfile = None

        self._popover = JSSecondaryPopover(self)

        self._contextMenu = JSContextMenu(self)

        self._setupProfiles()

        if self._autoLoadProfile is None:
            notifyMessage = None
        else:
            notifyMessage = _("Profile: '{0}'").\
                format(self._autoLoadProfile.name)

        self._notifySend(_("Added"), notifyMessage)

    @property
    def id(self):
        """Get the identifier of this joystick."""
        return self._id

    @property
    def identity(self):
        """Get the identity of this joystick."""
        return self._identity

    @property
    def type(self):
        """Get the type descriptor for this joystick."""
        return self._type

    @property
    def statusIcon(self):
        """Get the status icon of the joystick."""
        return self._statusIcon

    @property
    def autoLoadProfile(self):
        """Get the profile to load automatically."""
        return self._autoLoadProfile

    @property
    def popover(self):
        """Get the popover for the secondary menu."""
        return self._popover

    @property
    def contextMenu(self):
        """Get the context menu for the joystick."""
        return self._contextMenu

    @property
    def gui(self):
        """Get the GUI object the joystick belongs to."""
        return self._gui

    def extendDisplayedNames(self):
        """Extend the displayed names so that they are unique."""
        identity = self.identity

        self._setDisplayedNames(identity.name + " (" + identity.phys + ")")

    def simplifyDisplayedNames(self):
        """Simpify the displayed names so that they are unique."""
        self._setDisplayedNames(self.identity.name)

    def setActiveProfile(self, profile, notify = True):
        """Make the given profile active."""
        if notify:
            # FIXME: use the joystick's icon, if any
            self._notifySend(_("Downloaded profile"),
                             _("Profile: '{0}'").format(profile.name))

        self._statusIcon.setActive(profile)
        self._popover.setActive(profile)
        self._contextMenu.setActive(profile)

    def profileDownloadFailed(self, profile, exc):
        """Called when downloading the profile has failed with the given
        exception."""
        self._notifySend(_("Profile download failed"),
                         _("{0}").format(str(exc)))

    def destroy(self, notify = True):
        """Destroy the joystick."""
        if notify:
            self._notifySend(_("Removed"))

        self._statusIcon.destroy()
        JSWindow.get().removeJoystick(self._iconRef)

    def _setupProfiles(self):
        """Select the profiles matching this joystick and add them to the
        various menus."""
        self._autoLoadProfile = None
        autoLoadCandidateScore = 0

        for profile in self._type.profiles:
            score = profile.match(self.identity)
            if score>0:
                self._statusIcon.addProfile(profile)
                self._popover.addProfile(profile)
                self._contextMenu.addProfile(profile)

                if profile.autoLoad and score>autoLoadCandidateScore:
                    self._autoLoadProfile = profile
                    autoLoadCandidateScore = score

    def _setDisplayedNames(self, name):
        """Set the displayed names to the given one."""
        self._statusIcon.setName(name)
        JSWindow.get().setJoystickName(self._iconRef, name)
        self._popover.setTitle(name)

    def _notifySend(self, summary, body = None):
        """Send (update) the notification associated with this joystick with
        the given summary and body"""
        identity = self.identity
        summary = "%s: %s (%s)" % (summary, identity.name, identity.phys)
        self._gui.sendNotify(summary, body)
