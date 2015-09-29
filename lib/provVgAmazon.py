from provisioning import Provisioning
import rcExceptions as ex

class ProvisioningVg(Provisioning):
    def __init__(self, r):
        Provisioning.__init__(self, r)
        self.volumes_done = []

    def provisioner(self):
        for volume in self.r.volumes:
            self._provisioner(volume)
        self.r.svc.config.set(self.r.rid, "volumes", ' '.join(self.volumes_done))
        self.r.svc.write_config()
        self.r.log.info("provisioned")
        self.r.start()
        return True

    def _provisioner(self, volume):
        if not volume.startswith("<") and not volume.endswith(">"):
            self.r.log.info("volume %s already provisioned" % volume)
            self.volumes_done.append(volume)
            return

        s = volume.strip("<>")
        v = s.split(",")
        kwargs = {}
        for e in v:
            key, val = e.split("=")
            kwargs[key] = val
        cmd = ["ec2", "create-volume"]
        if "size" in kwargs:
            cmd += ["--size", kwargs["size"]]
        if "iops" in kwargs:
            cmd += ["--iops", kwargs["iops"]]
        if "availability-zone" in kwargs:
            cmd += ["--availability-zone", kwargs["availability-zone"]]
        else:
            node = self.r.get_instance_data()
            availability_zone = node["Placement"]["AvailabilityZone"]
            cmd += ["--availability-zone", availability_zone]
        data = self.r.aws(cmd)
        self.volumes_done.append(data["VolumeId"])


