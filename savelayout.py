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
    vp_data = subprocess.check_output(["wmctrl", "-d"]).decode("utf-8").split()
    curr_vpdata = [int(n) for n in vp_data[5].split(",")]
    return [res, curr_vpdata]

app = lambda pid: subprocess.check_output(["ps", "-q",  pid, "-o", "comm="]).decode("utf-8").strip()

def read_windows():
    res = get_res()
    w_list =  [l.split() for l in get("wmctrl -lpG").splitlines()]
    relevant = [[w[2],w[1],[int(n) for n in w[3:7]]] for w in w_list if check_window(w[0]) == True]
    for i, r in enumerate(relevant):
        r[2][0] = r[2][0] + xof #adjust to account for WM
        r[2][1] = r[2][1] + yof #adjust to account for WM
        relevant[i] = app(r[0])+" "+r[1]+" "+str((" ").join([str(n) for n in r[2]]))
    with open(wfile, "wt") as out:
        for l in relevant:
            out.write(l+"\n")

def read_window_ids():
    w_list =  [l.split() for l in get("wmctrl -lpG").splitlines()]
    relevant = [[w[2], w[0]] for w in w_list if check_window(w[0]) == True]
    for i, r in enumerate(relevant):
        relevant[i][0] = app(r[0])
    return relevant

def open_appwindow(app, loc):
    ws1 = get("wmctrl -lp"); t = 0
    # fix command for certain apps that open in new tab by default
    if app == "gedit":
        option = " --new-window"
    else:
        option = ""
    # fix command if process name and command to run are different
    if "gnome-terminal" in app:
        app = "gnome-terminal"
    elif "chrome" in app:
        app = "/usr/bin/google-chrome-stable"

    subprocess.Popen(["/bin/bash", "-c", app+option])
    # fix exception for Chrome (command = google-chrome-stable, but processname = chrome)
    app = "chrome" if "chrome" in app else app
    while t < 30:
        ws2 = [w.split()[0:3] for w in get("wmctrl -lp").splitlines() if not w in ws1]
        procs = [[(p, w[0]) for p in get("ps -e ww").splitlines() \
                  if app in p and w[2] in p] for w in ws2]
        if len(procs) > 0:
            time.sleep(0.5)
            w_id = procs[0][0][1]
            reposition_window(w_id, loc)
            break
        time.sleep(0.5)
        t = t+1

def reposition_window(w_id, loc):
    x,y,w,h,d = loc
    cmd1 = "wmctrl -ir "+w_id+" -b remove,maximized_horz"
    cmd2 = "wmctrl -ir "+w_id+" -b remove,maximized_vert"
    cmd3 = "wmctrl -ir "+w_id+" -e 0,"+x+","+y+","+w+","+h
    cmd4 = "wmctrl -ir "+w_id+" -t "+d
    for cmd in [cmd1, cmd2, cmd3, cmd4]:
        subprocess.call(["/bin/bash", "-c", cmd])

def run_remembered():
    res = get_res()[1]
    running = read_window_ids()
    try:
        lines = [l.split() for l in open(wfile).read().splitlines()]
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
    except FileNotFoundError:
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
    print("xof=", int(pos[0])-int(pos_after[0]))
    print("yof=", int(pos[1])-int(pos_after[1]))    

def main():    
    if (len(sys.argv) < 1) :
        show_help()
        exit(0)

    if (len(sys.argv) == 1) :
        run_remembered()
        exit(0)    
    arg = sys.argv[1]
    if (arg == "-load") :
        run_remembered()
    elif arg == "-save":
        read_windows()
    elif arg == "-calibrate":
        do_calbration()
    else :
        show_help()


if __name__ == '__main__':
    main()
