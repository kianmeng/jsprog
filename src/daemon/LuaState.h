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

#ifndef LUASTATE_H
#define LUASTATE_H
//------------------------------------------------------------------------------

#include <string>

extern "C" {
#include <lua.h>
}

//------------------------------------------------------------------------------

class Joystick;

//------------------------------------------------------------------------------

/**
 * An independent Lua state belonging to a Joystick instance. It
 * contains some global functions and variables, some of which are
 * specific to that joystick.
 */
class LuaState
{
private:
    /**
     * The global name for the lua state.
     */
    static const char* const GLOBAL_LUASTATE;

    /**
     * The global name for the table of the threads.
     */
    static const char* const GLOBAL_THREADS;

    /**
     * Global name: iskeypressed
     */
    static const char* const GLOBAL_ISKEYPRESSED;

    /**
     * Global name: getabs
     */
    static const char* const GLOBAL_GETABS;

    /**
     * Global name: getabsmin
     */
    static const char* const GLOBAL_GETABSMIN;

    /**
     * Global name: getabsmax
     */
    static const char* const GLOBAL_GETABSMAX;

    /**
     * Global name: delay
     */
    static const char* const GLOBAL_DELAY;

    /**
     * Global name: presskey
     */
    static const char* const GLOBAL_PRESSKEY;

    /**
     * Global name: releasekey
     */
    static const char* const GLOBAL_RELEASEKEY;

    /**
     * Global name: moverel
     */
    static const char* const GLOBAL_MOVEREL;

    /**
     * Global name: cancelprevious
     */
    static const char* const GLOBAL_CANCELPREVIOUS;

    /**
     * Global name: cancelpreviousof
     */
    static const char* const GLOBAL_CANCELPREVIOUSOFKEY;

    /**
     * Global name: cancelall
     */
    static const char* const GLOBAL_CANCELALL;

    /**
     * Global name: cancelallofkey
     */
    static const char* const GLOBAL_CANCELALLOFKEY;

    /**
     * Global name: cancelalljoystick
     */
    static const char* const GLOBAL_CANCELALLOFJOYSTICK;

private:
    /**
     * Get the LuaState object from the given state.
     */
    static LuaState& get(lua_State* L);

    /**
     * A function that causes a delay in the thread's execution
     */
    static int delay(lua_State* L);

    /**
     * A function that returns whether a key is pressed or not.
     */
    static int iskeypressed(lua_State* L);

    /**
     * A function that returns the current value of an absolute axis.
     */
    static int getabs(lua_State* L);

    /**
     * A function that returns the minimal value of an absolute axis.
     */
    static int getabsmin(lua_State* L);

    /**
     * A function that returns the maximal value of an absolute axis.
     */
    static int getabsmax(lua_State* L);

    /**
     * A function that sends a key press event.
     */
    static int presskey(lua_State* L);

    /**
     * A function that sends a key release event.
     */
    static int releasekey(lua_State* L);

    /**
     * A function that sends a relative move event.
     */
    static int moverel(lua_State* L);

    /**
     * A function that cancels the previously started thread of the
     * current control.
     */
    static int cancelprevious(lua_State* L);

    /**
     * A function that cancels the previously started thread of a
     * given key.
     */
    static int cancelpreviousofkey(lua_State* L);

    /**
     * A function that cancels all threads of the current control.
     */
    static int cancelall(lua_State* L);

    /**
     * A function that cancels all threads of a given key.
     */
    static int cancelallofkey(lua_State* L);

    /**
     * A function that cancels all threads of the joystick the current
     * control belongs to.
     */
    static int cancelallofjoystick(lua_State* L);

    /**
     * The joystick that this state belongs to.
     */
    Joystick& joystick;

    /**
     * The actual Lua state.
     */
    lua_State* L;

public:
    /**
     * Construct the Lua state.
     */
    LuaState(Joystick& joystick);

    /**
     * Destroy the Lua state. It destroy's the real Lua state as well.
     */
    ~LuaState();

    /**
     * Create a new Lua thread. The thread will be added to a global
     * table as a key to avoid its removal.
     */
    lua_State* newThread();

    /**
     * Delete a Lua thread. It will be removed from the global table.
     */
    void deleteThread(lua_State* thread);

    /**
     * Load the given string as the profile code. It resets the state
     * and loads and runs the given code.
     *
     * @return if the script could be run
     */
    bool loadProfile(const std::string& profileCode);

private:
    /**
     * Reset the Lua state. The old one will be closed and a new one
     * will be created and initialized.
     */
    void reset();

    /**
     * Initialize the Lua state by creating the default global stuff.
     */
    void initialize();
};

//------------------------------------------------------------------------------
#endif // LUASTATE_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
