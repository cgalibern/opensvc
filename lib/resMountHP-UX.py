#
# Copyright (c) 2009 Christophe Varoqui <christophe.varoqui@free.fr>'
# Copyright (c) 2009 Cyril Galibern <cyril.galibern@free.fr>'
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
# To change this template, choose Tools | Templates
# and open the template in the editor.

import os

import rcStatus
from rcGlobalEnv import rcEnv
rcMounts = __import__('rcMounts'+rcEnv.sysname)
import resMount as Res
from rcUtilities import qcall, protected_mount
import rcExceptions as ex

def try_umount(self):
    cmd = ['umount', self.mountPoint]
    (ret, out) = self.vcall(cmd)
    if ret == 0:
        return 0

    """ don't try to kill process using the source of a
        protected bind mount
    """
    if protected_mount(dev):
        return 1

    """ best effort kill of all processes that might block
        the umount operation. The priority is given to mass
        action reliability, ie don't contest oprator's will
    """
    cmd = ['sync']
    (ret, out) = self.vcall(cmd)

    for i in range(4):
        cmd = ['fuser', '-kc', self.mountPoint]
        (ret, out) = self.vcall(cmd)
        self.log.info('umount %s'%self.mountPoint)
        cmd = ['umount', self.mountPoint]
        ret = qcall(cmd)
        if ret == 0:
            break

    return ret


class Mount(Res.Mount):
    """ define HP-UX mount/umount doAction """
    def __init__(self, rid, mountPoint, device, fsType, mntOpt):
        self.Mounts = rcMounts.Mounts()
        Res.Mount.__init__(self, rid, mountPoint, device, fsType, mntOpt)

    def is_up(self):
        return self.Mounts.has_mount(self.device, self.mountPoint)

    def status(self):
        if self.is_up(): return rcStatus.UP
        else: return rcStatus.DOWN

    def start(self):
        Res.Mount.start(self)
        if self.is_up() is True:
            self.log.info("fs(%s %s) is already mounted"%
                (self.device, self.mountPoint))
            return 0
        if not os.path.exists(self.mountPoint):
            os.makedirs(self.mountPoint, 0755)
        if self.fsType != "":
            fstype = ['-F', self.fsType]
        else:
            fstype = []
        if self.mntOpt != "":
            mntopt = ['-o', self.mntOpt]
        else:
            mntopt = []
        cmd = ['mount']+fstype+mntopt+[self.device, self.mountPoint]
        (ret, out) = self.vcall(cmd)
        if ret != 0:
            raise ex.excError

    def stop(self):
        if self.is_up() is False:
            self.log.info("fs(%s %s) is already umounted"%
                    (self.device, self.mountPoint))
            return 0
        for i in range(3):
            ret = try_umount(self)
            if ret == 0: break
        if ret != 0:
            self.log.error('failed to umount %s'%self.mountPoint)
            raise ex.excError

if __name__ == "__main__":
    for c in (Mount,) :
        help(c)

