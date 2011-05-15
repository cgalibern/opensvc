from rcUtilities import call

def check_ping(addr, timeout=5, count=1):
    if ':' in addr:
        ping = 'ping6'
    else:
        ping = 'ping'
    cmd = [ping, '-c', repr(count),
                 '-W', repr(timeout),
                 addr]
    (ret, out, err) = call(cmd)
    if ret == 0:
        return True
    return False
