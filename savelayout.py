#!/usr/bin/env python
# This script is originated from
# https://askubuntu.com/questions/193569/is-there-a-way-to-store-the-current-desktop-layout

from __future__ import print_function
import subprocess
import os
import sys
import time

# calibration offsets, run me with -calibrate flag to print these
xof = -2
yof = -52
# configuration file
wfile = os.environ["HOME"]+"/.windowlist"

def get(command):
    return subprocess.check_output(["/bin/bash", "-c", command]).decode("utf-8")

def check_window(w_id):
    w_type = get("xprop -id "+w_id)
    if " _NET_WM_WINDOW_TYPE_NORMAL" in w_type:
        return True
    elif "\"xterm\"" in w_type:
        return True
    else:
        return False

def get_res():
    # get resolution and the workspace correction (vector)
    xr = subprocess.check_output(["xrandr"]).decode("utf-8").split()
    pos = xr.index("current")
    res = [int(xr[pos+1]), int(xr[pos+3].replace(",", "") )]
    lines = subprocess.check_output(["wmctrl", "-d"]).decode("utf-8").splitlines()
    curr_vpdata = [0, 0]
    for line in lines:
        parts = line.split()
        if len(parts) >= 6 and parts[1] == "*":
            if parts[5] != "N/A":
                curr_vpdata = [int(n) for n in parts[5].split(",")]
            break
    return [res, curr_vpdata]

def app(pid):
    try:
        with open("/proc/" + str(pid) + "/comm", "r") as f:
            return f.read().strip()
    except (IOError, OSError):
        pass
    try:
        return subprocess.check_output(["ps", "-q", str(pid), "-o", "comm="]).decode("utf-8").strip()
    except Exception:
        return "unknown"

def read_windows():
    global xof,yof
    w_list =  [l.split() for l in get("wmctrl -lpG").splitlines()]
    relevant = [[w[2],w[1],[int(n) for n in w[3:7]]] for w in w_list if check_window(w[0]) == True]
    for i, r in enumerate(relevant):
        r[2][0] = r[2][0] + xof #adjust to account for WM
        r[2][1] = r[2][1] + yof #adjust to account for WM
        relevant[i] = app(r[0])+" "+r[1]+" "+str((" ").join([str(n) for n in r[2]]))
    return relevant

def read_calibration():
    global xof,yof
    # read saved calibration constants
    try:
        with open(wfile, "r") as f:
            lines = [l.split() for l in f.read().splitlines()]
        if lines:
            calibr = lines.pop()
            if (calibr[0] == 'calibration'):
                xof = int(calibr[1])
                yof = int(calibr[2])
            else:
                lines.append(calibr)
    except (IOError, OSError):
        pass
    
def save_positions(wfile, winlist):
    with open(wfile, "wt") as out:
        for l in winlist:
            out.write(l+"\n")
        l = "calibration " + str(xof) + " " + str(yof)
        out.write(l+"\n")
    
def read_window_ids():
    w_list =  [l.split() for l in get("wmctrl -lpG").splitlines()]
    relevant = [[w[2], w[0]] for w in w_list if check_window(w[0]) == True]
    for i, r in enumerate(relevant):
        relevant[i][0] = app(r[0])
    return relevant

def proc_matches(pid, app_name):
    if not pid or pid in ("0", "-1"):
        return False
    try:
        with open("/proc/" + str(pid) + "/comm", "r") as f:
            comm = f.read().strip()
            if app_name in comm or comm in app_name:
                return True
    except (IOError, OSError):
        pass
    try:
        with open("/proc/" + str(pid) + "/cmdline", "r") as f:
            cmdline = f.read().replace('\0', ' ')
            if app_name in cmdline:
                return True
    except (IOError, OSError):
        pass
    return False

def window_matches(w_id, app_name):
    try:
        w_class = get("xprop -id " + w_id + " WM_CLASS")
        if app_name.lower() in w_class.lower():
            return True
    except Exception:
        pass
    return False

def open_appwindow(app_name, loc):
    ws1 = set(l.split()[0] for l in get("wmctrl -lp").splitlines() if l.strip())
    # fix command for certain apps that open in new tab by default
    option = " --new-window" if app_name == "gedit" else ""
    # fix command if process name and command to run are different
    cmd_app = app_name
    if "gnome-terminal" in app_name:
        cmd_app = "gnome-terminal"
    elif "chrome" in app_name:
        cmd_app = "/usr/bin/google-chrome-stable"

    subprocess.Popen(["/bin/bash", "-c", cmd_app + option])
    match_app = "chrome" if "chrome" in app_name else app_name

    t = 0
    while t < 30:
        time.sleep(0.5)
        t += 1
        lines = [l.split() for l in get("wmctrl -lp").splitlines() if l.strip()]
        new_windows = [w for w in lines if len(w) >= 3 and w[0] not in ws1]

        matched_wid = None
        for w in new_windows:
            w_id, pid = w[0], w[2]
            if proc_matches(pid, match_app) or window_matches(w_id, match_app):
                if check_window(w_id):
                    matched_wid = w_id
                    break

        if matched_wid:
            time.sleep(0.5)
            reposition_window(matched_wid, loc)
            break

def reposition_window(w_id, loc):
    x, y, w, h, d = [str(n) for n in loc]
    subprocess.call(["wmctrl", "-ir", w_id, "-b", "remove,maximized_horz,maximized_vert"])
    subprocess.call(["wmctrl", "-ir", w_id, "-e", "0," + x + "," + y + "," + w + "," + h])
    subprocess.call(["wmctrl", "-ir", w_id, "-t", d])

def run_remembered():
    global xof, yof
    res = get_res()[1]
    running = read_window_ids()
    try:
        with open(wfile, "r") as f:
            lines = [l.split() for l in f.read().splitlines()]
        if lines:
            calibr = lines.pop()
            if (calibr[0] == 'calibration'):
                xof = int(calibr[1])
                yof = int(calibr[2])
            else:
                lines.append(calibr)            
            for l in lines:
                l[2] = str(int(l[2]) - res[0]); l[3] = str(int(l[3]) - res[1])
                apps = [a[0] for a in running]
                location = l[2:6] + [l[1]]
                if l[0] in apps :
                    idx = apps.index(l[0])
                    reposition_window(running[idx][1], location)
                    running.pop(idx)
                else :
                    open_appwindow(l[0], location)
    except (IOError, OSError):
        pass

def show_help():
    print("usage: python3 savelayout.py -save|-load|-calibrate")
    print("       -save : record window positions")
    print("       -load : restore window positions")
    print("       -calibrate : display calibration offsets")

def start_calibration_window():
    calibw = subprocess.Popen(["xmessage", "Calibration"])
    return calibw

def stop_calibration_window(calibw):
    calibw.terminate()

def do_calbration():
    global xof, yof
    calibw = start_calibration_window()
    time.sleep(1)
    w_list =  [l.split() for l in get("wmctrl -lpG").splitlines()]
    w_info = [[w[0],w[2],w[1],[n for n in w[3:7]]] for w in w_list if (w[8] == "xmessage")]
    pos = w_info[0][3] + [u'0']
    reposition_window(w_info[0][0], pos)
    w_list =  [l.split() for l in get("wmctrl -lpG").splitlines()]
    w_after = [[w[0],w[2],w[1],[n for n in w[3:7]]] for w in w_list if (w[8] == "xmessage")]
    stop_calibration_window(calibw)
    pos_after = w_after[0][3] + [u'0']
    xof = int(pos[0])-int(pos_after[0])
    yof = int(pos[1])-int(pos_after[1])
    print("xof=", xof)
    print("yof=", yof)    
    with open(wfile, "wt") as out:
        l = "calibration " + str(xof) + " " + str(yof)
        out.write(l+"\n")

def main():    
    if (len(sys.argv) < 1) :
        show_help()
        sys.exit(0)

    if (len(sys.argv) == 1) :
        run_remembered()
        sys.exit(0)    
    arg = sys.argv[1]
    if (arg == "-load") :
        run_remembered()
    elif arg == "-save":
        read_calibration()
        wlist = read_windows()
        save_positions(wfile, wlist)
    elif arg == "-calibrate":
        do_calbration()
    else :
        show_help()


if __name__ == '__main__':
    main()
