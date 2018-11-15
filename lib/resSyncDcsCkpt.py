import os
import rcExceptions as ex
import rcStatus
import datetime
import resSync
import resSyncDcs
from rcGlobalEnv import rcEnv
from rcUtilities import justcall

class syncDcsCkpt(resSyncDcs.SyncDcs):
    def can_sync(self, target=None):
        return True

    def checkpoint(self):
        cmd = ""
        vars = ""
        for i, d in enumerate(self.pairs):
            cmd += '$v%d=Get-DcsVirtualDisk -VirtualDisk %s -connection %s;'%(i, d['src'], self.conn)
            vars += '$v%d '%i

        cmd += "echo %s|Set-DcsReplicationCheckPoint -connection %s"%(vars, self.conn)
        self.dcscmd(cmd, verbose=True)
        self.update_tsfile()

    def get_snap(self, snap):
        if snap in self._info:
            return self._info[snap]

        cmd = 'get-dcssnapshot -snapshot %s -connection %s;'%(snap, self.conn)
        try:
            ret, out, err = self.dcscmd(cmd)
        except:
            return None

        info = {}
        lines = out.split('\n')
        for line in lines:
            l = line.split(': ')
            if len(l) != 2:
                continue
            var = l[0].strip()
            val = l[1].strip()
            if var == 'TimeStamp':
                info['TimeStamp'] = datetime.datetime.strptime(val, "%d/%m/%Y %H:%M:%S")
            elif var in ['Type', 'State', 'ActiveOperation', 'Failure']:
                info[var] = val
        if len(info) > 0:
            self._info[snap] = info
        return info

    def drpnodes_status(self, verbose=False, skip_prereq=False):
        err = False
        errlog = []
        log = []
        try:
            self.get_auth()
        except ex.excError as e:
            self.status_log(str(e))
            return rcStatus.WARN
        for snap in [p['dst_ckpt'] for p in self.pairs]:
            info = self.get_snap(snap)
            if info is None:
                errlog.append("checkpoint snapshot %s does not exists"%snap)
                err |= True
                continue
            if info['State'] not in ['Healthy']:
                errlog.append("checkpoint snapshot %s state is %s"%(snap, info['State']))
                err |= True
            if info['Failure'] not in ['NoFailure']:
                errlog.append("checkpoint snapshot %s failure state is %s"%(snap, info['Failure']))
                err |= True
            if info['TimeStamp'] < datetime.datetime.now() - datetime.timedelta(seconds=self.sync_max_delay):
                errlog.append("checkpoint snapshot %s too old"%snap)
                err |= True
            log.append("last update on %s"%info['TimeStamp'])
        if err:
            self.status_log('\n'.join(errlog))
            return rcStatus.WARN
        self.status_log('\n'.join(log))
        return rcStatus.UP

    def nodes_status(self, verbose=False, skip_prereq=False):
        err = False
        ts = self.read_tsfile()
        if ts < datetime.datetime.now() - datetime.timedelta(seconds=self.sync_max_delay):
            self.status_log("checkpoint too old")
            err |= True
        self.status_log("last update on %s"%str(ts))
        if err:
            return rcStatus.WARN
        return rcStatus.UP

    def sync_status(self, verbose=False, skip_prereq=False):
        if rcEnv.nodename in self.svc.nodes:
            return self.nodes_status(verbose, skip_prereq)
        else:
            return self.drpnodes_status(verbose, skip_prereq)

    def pause_checkpoint(self):
        cmd = ""
        for d in self.pairs:
            cmd += 'Disable-DcsTask -Task %s -connection %s ; '%(self.task_name(d['dst_ckpt']), self.conn)
        self.dcscmd(cmd, verbose=True)

    def create_task(self):
        cmd = "Get-DcsTask -connection %s"%self.conn
        tasks = []
        ret, out, err = self.dcscmd(cmd, verbose=False)
        for line in out.split('\n'):
             if line.startswith("Caption"):
                 tasks.append(line.split(':')[-1].strip())

        cmd = ""
        for d in self.pairs:
            if self.task_name(d['dst_ckpt']) in tasks:
                continue
            cmd += "Add-DcsTask -Disabled -Name %s -connection %s; "%(self.task_name(d['dst_ckpt']), self.conn)
            cmd += 'Add-DcsTrigger -Task %s -VirtualDisk "%s" -connection %s; '%(self.task_name(d['dst_ckpt']), d['dst'], self.conn)
            cmd += 'Add-DcsAction -Task %s -MethodActionType UpdateSnapshot -connection %s -TargetId (Get-DcsSnapshot -snapshot "%s" -connection %s).Id ; '%(self.task_name(d['dst_ckpt']), self.conn, d['dst_ckpt'], self.conn)
        self.dcscmd(cmd, verbose=True)

    def resume_checkpoint(self):
        self.create_task()
        cmd = ""
        for d in self.pairs:
            cmd += 'Enable-DcsTask -Task %s -connection %s; '%(self.task_name(d['dst_ckpt']), self.conn)
        self.dcscmd(cmd, verbose=True)

    def task_name(self, id):
        return '-'.join((self.svc.svcname, self.rid, id))

    def sync_break(self):
        self.pause_checkpoint()

    def start(self):
        if rcEnv.nodename not in self.svc.drpnodes:
            return
        self.pause_checkpoint()

    def sync_resume(self):
        self.resume_checkpoint()

    @resSync.notify
    def sync_update(self):
        self.checkpoint()

    def refresh_svcstatus(self):
        self.svcstatus = self.svc.group_status(excluded_groups=set(["app", "sync", "task", "disk.scsireserv"]))

    def get_svcstatus(self):
        if len(self.svcstatus) == 0:
            self.refresh_svcstatus()

    def __init__(self,
                 rid=None,
                 pairs=[],
                 manager=set(),
                 dcs=set(),
                 **kwargs):
        resSyncDcs.SyncDcs.__init__(self,
                                    rid=rid, type="sync.dcsckpt",
                                    manager=manager,
                                    dcs=dcs,
                                    **kwargs)

        self.label = "DCS checkpoint snapshot of %s"%' ,'.join(map(lambda x: x['src'], pairs))
        self.pairs = pairs
        self._info = {}

    def tsfile(self):
        return os.path.join(self.var_d, 'ts')

    def update_tsfile(self):
        import datetime
        now = datetime.datetime.now()
        with open(self.tsfile(), 'w') as f:
            f.write(str(now)+'\n')

    def read_tsfile(self):
        import datetime
        try:
            with open(self.tsfile(), 'r') as f:
                ts = datetime.datetime.strptime(f.read(),"%Y-%m-%d %H:%M:%S.%f\n")
        except:
            ts = datetime.datetime.fromtimestamp(0)
        return ts

