from pkg_resources import Requirement
from mosec import utils


class ReqDist(Requirement):

    def __init__(self, req, dist=None):
        super(ReqDist, self).__init__(str(req))
        self.dist = dist

    @property
    def version(self):
        if not self.dist:
            return utils.guess_version(self.key)
        return self.dist.version
