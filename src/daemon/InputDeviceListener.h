// Copyright (c) 2012 by Istv�n V�radi

// This file is part of JSProg, a joystick programming utility

// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#ifndef INPUTDEVICELISTENER_H
#define INPUTDEVICELISTENER_H
//------------------------------------------------------------------------------

#include <lwt/Thread.h>

#include <map>
#include <string>

//------------------------------------------------------------------------------

class INotify;
class Joystick;

//------------------------------------------------------------------------------

/**
 * A thread that listens to events on the /dev/input directory.
 */
class InputDeviceListener : public lwt::Thread
{
private:
    /**
     * Type of a mapping from device names to joysticks.
     */
    typedef std::map<std::string, Joystick*> name2joystick_t;
    
    /**
     * The directory to watch.
     */
    static const char* const inputDirectory;

    /**
     * The inotify file descriptor.
     */
    INotify* inotify;

    /**
     * A mapping from device file names to joysticks.
     */
    name2joystick_t joysticks;

public:
    /**
     * Construct the thread.
     */
    InputDeviceListener();

    /**
     * Destroy the thread.
     */
    ~InputDeviceListener();

    /**
     * Perform the thread's operation.
     */
    virtual void run();

private:
    /**
     * Scan the devices.
     */
    void scanDevices();

    /**
     * Check the input device with the given file name (relative to
     * /dev/input). 
     */
    void checkDevice(const std::string& fileName);
};

//------------------------------------------------------------------------------
#endif // INPUTDEVICELISTENER_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

