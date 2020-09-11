def get_action_args_from_parser(parser, action, options):
    """
    Return cmd for action handlers
    :param parser:
    :param action:
    :param options:
    :return: cmd array
    """
    def find_opt(local_parser, searched_opt):
        for k, o in local_parser.items():
            if o.dest == searched_opt:
                return o
            if o.dest == "parm_" + searched_opt:
                return o

    cmd = [action]
    for opt, val in options.options.items():
        po = find_opt(parser, opt)
        if po is None:
            continue
        if val == po.default:
            continue
        if val is None:
            continue
        opt = po.get_opt_string()
        if po.action == "append":
            cmd += [opt + "=" + str(v) for v in val]
        elif po.action == "store_true" and val:
            cmd.append(opt)
        elif po.action == "store_false" and not val:
            cmd.append(opt)
        elif po.type == "string":
            opt += "=" + val
            cmd.append(opt)
        elif po.type == "integer":
            opt += "=" + str(val)
            cmd.append(opt)
    return cmd
