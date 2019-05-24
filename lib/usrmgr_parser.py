"""
secmgr command line actions and options
"""
import svc
import mgr_parser as mp
from rcOptParser import OptParser
from optparse import Option

PROG = "usrmgr"

OPT = mp.OPT
OPT.update({
    "key": Option(
        "--key", default=None,
        action="store", dest="key",
        help="The secret key name."),
    "value_from": Option(
        "--from", default=None,
        action="store", dest="value_from",
        help="Read the secret value from a file or a directory. If set to '-' or '/dev/stdin', the value is read from stdin, and the --key is mandatory. If set to a file path, the key name is the file basename. If set to a directory, one key per file is added, and the keyname is the relative path, the --key value being used as the relative path prefix."),
    "path": Option(
        "--path", default=None,
        action="store", dest="path",
        help="The path where to install secret keys."),
    "value": Option(
        "--value", default=None,
        action="store", dest="value",
        help="The secret value."),
})

ACTIONS = mp.ACTIONS
ACTIONS.update({
    "User actions": {
        "add": {
            "msg": "Add a secret key/value to the secret object.",
            "options": mp.ACTION_OPTS + [
                OPT.value_from,
                OPT.key,
                OPT.value,
            ],
        },
        "keys": {
            "msg": "Show all keys available in this secret.",
        },
        "gen_cert": {
            "msg": "Create a x509 certificate using information in the secret configuration.",
        },
        "decode": {
            "msg": "Decode a secret key from the secret object.",
            "options": mp.ACTION_OPTS + [
                OPT.key,
            ],
        },
        "install": {
            "msg": "Install or update secret key or secret tree in consuming volumes.",
            "options": mp.ACTION_OPTS + [
                OPT.key,
            ],
        },
    },
})

DEPRECATED_OPTIONS = [
]

DEPRECATED_ACTIONS = [
]

ACTIONS_TRANSLATIONS = {
}

class UsrmgrOptParser(OptParser):
    """
    The usrmgr-specific options parser class
    """
    def __init__(self, args=None, colorize=True, width=None, formatter=None,
                 indent=6):
        OptParser.__init__(self, args=args, prog=PROG, options=OPT,
                           actions=ACTIONS,
                           deprecated_options=DEPRECATED_OPTIONS,
                           deprecated_actions=DEPRECATED_ACTIONS,
                           actions_translations=ACTIONS_TRANSLATIONS,
                           global_options=mp.GLOBAL_OPTS,
                           svc_select_options=mp.SVC_SELECT_OPTS,
                           colorize=colorize, width=width,
                           formatter=formatter, indent=indent, async_actions=svc.ACTION_ASYNC)
