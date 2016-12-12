"""
Helper module to handle optparser configuration.

Define a reference of supported keywords, their supported options, and methods
to format contextualized help messages.
"""

from __future__ import print_function
import os
import optparse
from textwrap import TextWrapper
import rcColor
from rcUtilities import term_width
import rcExceptions as ex

class OptParser(object):
    """
    A class wrapping the optparse module use, adding some features:
    * contextualized help depending on action prefix
    * colors
    * layout tweaks
    """

    def __init__(self, args=None, prog="", options=None, actions=None,
                 deprecated_actions=None, global_options=None,
                 svcmgr_options=None, colorize=True, width=None,
                 formatter=None, indent=6):
        self.args = args
        self.prog = prog
        self.options = options
        self.actions = actions
        self.deprecated_actions = deprecated_actions if deprecated_actions else []
        self.global_options = global_options if global_options else []
        self.svcmgr_options = svcmgr_options if svcmgr_options else []
        self.colorize = colorize
        self.width = term_width() if width is None else width

        self.usage = self.prog + " [ OPTIONS ] COMMAND\n\n"
        self.indent = indent
        self.subsequent_indent = " " * self.indent
        if formatter is None:
            self.formatter = optparse.TitledHelpFormatter(self.indent,
                                                          self.indent+2,
                                                          self.width)
        else:
            self.formatter = formatter
        self.formatter.format_heading = lambda x: "\n"
        self.get_parser()

    def get_valid_actions(self, section, action):
        """
        Given a section and an action prefix, return the list of
        valid actions
        """
        valid_actions = []
        for candidate_action in sorted(self.actions[section]):
            if isinstance(action, str) and \
               not candidate_action.startswith(action):
                continue
            if isinstance(action, list) and candidate_action not in action:
                continue
            valid_actions.append(candidate_action)
        return valid_actions

    def format_options(self, section, action):
        """
        Format the possible options for a spectific action.
        """
        desc = ""
        parser = optparse.OptionParser(formatter=self.formatter, add_help_option=False)
        for option in self.actions[section][action].get("options", []):
            if option is None:
                raise ex.excError("unkown option referenced by action %s" % action)
            parser.add_option(option)
        desc += self.subsequent_indent + parser.format_option_help()
        return desc

    def format_action(self, section, action, options=True):
        """
        Format an candidate action for the help message.
        The action message may or may include the possible options,
        dependendin on the value of the options parameter.
        """
        fancya = self.prog + " " + action.replace('_', ' ')
        if self.colorize:
            desc = "  " + rcColor.colorize(fancya, rcColor.color.BOLD)
        else:
            desc = "  " + fancya
        desc += '\n\n'
        wrapper = TextWrapper(subsequent_indent=self.subsequent_indent, width=self.width)
        text = self.subsequent_indent + self.actions[section][action]["msg"]
        desc += wrapper.fill(text)
        desc += '\n'

        if options:
            desc += self.format_options(section, action)

        desc += '\n'
        return desc

    def format_desc(self, svc=False, action=None, options=True):
        """
        Format and return a svcmgr parser help message, contextualized to display
        only actions matching the action argument.
        """
        desc = ""
        for section in sorted(self.actions):
            valid_actions = self.get_valid_actions(section, action)
            if len(valid_actions) == 0:
                continue

            desc += section + '\n'
            desc += '-' * len(section)
            desc += "\n\n"
            for valid_action in valid_actions:
                if svc and not hasattr(svc, valid_action):
                    continue
                desc += self.format_action(section, valid_action, options=options)
        return desc[0:-2]

    def supported_actions(self):
        """
        Return the list of actions supported by svcmgr.
        """
        actions = []
        for section in self.actions:
            actions += self.actions[section].keys()
        actions += self.deprecated_actions
        return actions

    @staticmethod
    def svclink():
        """
        Return True if the service link was used to call svcmgr,
        else return False
        """
        return os.environ.get("OSVC_SERVICE_LINK", False)

    def get_action_from_args(self, args, options):
        """
        Check if the parsed command args list has at least one element to be
        interpreted as an action. Raise if not, else return the action name
        formatted as a '_' joined string.

        Also raise if the action is not supported.
        """
        if len(args) is 0:
            if options.parm_help:
                self.print_full_help()
            else:
                self.print_short_help()

        action = '_'.join(args)

        if action.startswith("collector_cli"):
            action = "collector_cli"

        return action

    def get_parser(self):
        """
        Setup an optparse parser
        """
        try:
            from version import version
        except ImportError:
            version = "dev"

        __ver = self.prog + " version " + version

        # parse a first time with all possible options to never fail on
        # undefined option
        self.parser = optparse.OptionParser(
            version=__ver,
            usage=self.usage + self.format_desc(),
            add_help_option=False,
        )

        for option in self.options.values():
            if self.svclink() and option in self.svcmgr_options:
                continue
            self.parser.add_option(option)

        options, args = self.parser.parse_args(self.args)
        action = self.get_action_from_args(args, options)

        # now we know the action. parse a second time with only options
        # supported by the action
        self.parser = optparse.OptionParser(
            version=__ver,
            usage=self.usage + self.format_desc(),
            add_help_option=False,
        )

        for option in self.options.values():
            if self.svclink() and option in self.svcmgr_options:
                continue
            self.parser.add_option(option)

        options, args = self.parser.parse_args(self.args)
        usage = self.usage + self.format_desc(action=action,
                                              options=options.parm_help)
        self.parser.set_usage(usage)

        if options.parm_help or action not in self.supported_actions():
            self.print_context_help(action)

    def print_full_help(self):
        """
        Reset the parser usage to the full actions list and their options.
        Then trigger a parser error, which displays the help message.
        """
        usage = self.usage + \
                self.format_desc()
        self.parser.set_usage(usage)
        if self.args is None:
            self.parser.error("Missing action")

    def print_short_help(self):
        """
        Reset the parser usage to a short message presenting only the most
        currently used actions. Then trigger a parser error, which displays the
        help message.
        """
        highlight_actions = ["start", "stop", "print_status"]
        usage = self.usage + \
                self.format_desc(action=highlight_actions, options=False) + \
                "\n\nOptions:\n" + \
                "  -h, --help       Display more actions and options\n"
        self.parser.set_usage(usage)
        if self.args is None:
            self.parser.error("Missing action")

    def print_context_help(self, action):
        """
        Trigger a parser error, which displays the help message contextualized
        for the action prefix.
        """
        if self.args is None:
            self.parser.error("Invalid service action: %s" % str(action))
