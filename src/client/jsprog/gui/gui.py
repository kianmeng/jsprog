
from joystick import Joystick
from common import *

from jsprog.const import dbusInterfaceName
from jsprog.util import getJSProg
from jsprog.profile import Profile

import StringIO

#--------------------------------------------------------------------------------

class GUI(object):
    """The main object."""
    def __init__(self, connection, profileDirectory):
        """Construct the GUI."""
        connection.add_match_string("interface='%s'" % (dbusInterfaceName,))
        connection.add_message_filter(self._filterMessage)

        self._jsprog = getJSProg(connection)

        self._profiles = Profile.loadFrom(profileDirectory)

        self._joysticks = {}

    def run(self):
        """Run the GUI."""
        if not pynotify.init("JSProg"):
            print >> sys.stderr, "Failed to initialize notifications"

        for joystickArgs in self._jsprog.getJoysticks():
            self._addJoystick(joystickArgs)

        gtk.main()
        # mainloop = MainLoop()
        # mainloop.run()

    def loadProfile(self, id, profile):
        """Load the given profile to the given joystick."""
        if id not in self._joysticks:
            return

        daemonXMLDocument = profile.getDaemonXMLDocument()
        daemonXML = StringIO.StringIO()
        daemonXMLDocument.writexml(daemonXML)

        try:
            joystick = self._joysticks[id]

            self._jsprog.loadProfile(id, daemonXML.getvalue())

            notifySend("Downloaded profile",
                       "Downloaded profile <b>%s</b> to <b>%s</b>" % \
                           (profile.name, joystick.identity.name))
        except Exception, e:
            notifySend("Profile download failed",
                       "Failed to downloaded profile <b>%s</b> to <b>%s</b>: %s" % \
                           (profile.name, joystick.identity.name), e)

    def quit(self):
        """Quit the main loop and the daemon as well."""
        try:
            self._jsprog.exit()
        except Exception, e:
            print >> sys.stderr, "Failed to stop the daemon:", e

        for joystick in self._joysticks.itervalues():
            joystick.destroy()

        gtk.main_quit()

    def _addJoystick(self, args):
        """Add a joystick from the given arguments."""
        id = int(args[0])
        joystick = self._joysticks[id] = Joystick.fromArgs(args)

        statusIcon = joystick.statusIcon

        loadCandidate = None
        loadCandidateMatch = 0
        for profile in self._profiles:
            score = profile.match(joystick.identity)
            if score>0:
                statusIcon.addProfile(self, profile)
                if profile.autoLoad and score>loadCandidateMatch:
                    loadCandidate = profile
                    loadCandidateMatch = score

        statusIcon.finalize(self)

        if loadCandidate is not None:
            statusIcon.setActive(loadCandidate)

    def _filterMessage(self, connection, message):
        """Handle notifications."""
        if message.get_interface()==dbusInterfaceName:
            args = message.get_args_list()
            if message.get_member()=="joystickAdded":
                id = args[0]
                if id not in self._joysticks:
                    self._addJoystick(args);
            elif message.get_member()=="joystickRemoved":
                id = args[0]
                print "Removed joystick:", id
                if id in self._joysticks:
                    self._joysticks[id].destroy()
                    del self._joysticks[id]
            else:
                print message
