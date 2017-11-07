from __future__ import print_function
import sys
import optparse

#
# add project lib to path
#
prog = "svcmon"

import rcExceptions as ex
import rcColor
from node import Node

try:
    from version import version
except:
    version = "dev"

__ver = prog + " version " + version
__usage = prog + " [ OPTIONS ]\n"
parser = optparse.OptionParser(version=__ver, usage=__usage)
parser.add_option("--color", default="auto", action="store", dest="color",
                  help="colorize output. possible values are : auto=guess based on tty presence, always|yes=always colorize, never|no=never colorize")
parser.add_option(
    "-s", "--service", default=None,
    action="store", dest="parm_svcs",
    help="A service selector expression ``[!]<expr>[<sep>[!]<expr>]`` where:\n\n"
         "- ``!`` is the expression negation operator\n\n"
         "- ``<sep>`` can be:\n\n"
         "  - ``,`` OR expressions\n\n"
         "  - ``+`` AND expressions\n\n"
         "- ``<expr>`` can be:\n\n"
         "  - a shell glob on service names\n\n"
         "  - ``<param><op><value>`` where:\n\n"
         "    - ``<param>`` can be:\n\n"
         "      - ``<rid>:``\n\n"
         "      - ``<group>:``\n\n"
         "      - ``<rid>.<key>``\n\n"
         "      - ``<group>.<key>``\n\n"
         "    - ``<op>`` can be:\n\n"
         "      - ``<``  ``>``  ``<=``  ``>=``  ``=``\n\n"
         "      - ``~`` with regexp value\n\n"
         "Examples:\n\n"
         "- ``*dns,ha*+app.timeout>1``\n\n"
         "- ``ip:+task:``\n\n"
         "- ``!*excluded``\n\n"
         "Note:\n\n"
         "- ``!`` usage requires single quoting the expression to prevent "
         "shell history expansion")

def _main(node, argv=None):
    (options, args) = parser.parse_args(argv)
    node.check_privs(argv)
    rcColor.use_color = options.color

    if options.parm_svcs:
        expanded_svcs = node.svcs_selector(options.parm_svcs)
    else:
        expanded_svcs = None

    node.options.update({
        "color": options.color,
    })
    node.daemon_status(svcnames=expanded_svcs)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        node = Node()
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        return _main(node, argv)
    except ex.excError as e:
        print(e, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("Keybord Interrupt\n")
        return 1
    finally:
        node.close()

    return 0

if __name__ == "__main__":
    ret = main()
    sys.exit(ret)

