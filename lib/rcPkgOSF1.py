#
# Copyright (c) 2012 Christophe Varoqui <christophe.varoqui@opensvc.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
from rcUtilities import justcall
from rcGlobalEnv import rcEnv

"""
Subset               Status                 Description
------               ------                 -----------
IOSFRBASE540         installed              French Base System (French Support - Operating System)
IOSFRCDEHLP540       not installed          French CDE Online Help (French Support - Windowing Environment)
IOSFRCDEMIN540       installed              French CDE Minimum Runtime Environment(French Support - Windowing Environment)
IOSFRX11540          installed              French Basic X Environment (French Support - Windowing Environment)
"""

def _list():
    cmd = ['setld', '-i']
    out, err, ret = justcall(cmd)
    pkg = []
    patch = []
    pkgarch = ""
    pkgvers = ""
    if ret != 0:
        return []
    lines = out.split('\n')
    if len(lines) < 3:
        return []
    for line in lines[2:]:
        if "installed" not in line or "not installed" in line:
            continue
        name = line.split()[0]
        if "Patch:" in line:
            x = [rcEnv.nodename, name, pkgvers]
            patch.append(x)
        else:
            x = [rcEnv.nodename, name, pkgvers, pkgarch]
            pkg.append(x)
    return pkg, patch

def listpkg():
    return _list()[0]

def listpatch():
    return _list()[1]
