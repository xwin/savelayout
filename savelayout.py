#!/usr/bin/env python
# This script is originated from
# https://askubuntu.com/questions/193569/is-there-a-way-to-store-the-current-desktop-layout

from __future__ import print_function
import subprocess
import os
import sys
import time
import shlex
import argparse

# calibration offsets, run me with -calibrate flag to print these
xof = -2
yof = -52
# configuration file
wfile = os.environ.get("HOME", "") + "/.windowlist"

def run_cmd(cmd):
    try:
        if isinstance(cmd, list):
            args = cmd
        else:
            args = shlex.split(cmd)
        return subprocess.check_output(args).decode("utf-8")
    except (subprocess.CalledProcessError, OSError):
        return ""

def check_window(w_id):
    w_type = run_cmd(["xprop", "-id", str(w_id), "_NET_WM_WINDOW_TYPE"])
    if " _NET_WM_WINDOW_TYPE_NORMAL" in w_type:
        return True
    w_class = run_cmd(["xprop", "-id", str(w_id), "WM_CLASS"])
    return "\"xterm\"" in w_class or "\"xterm\"" in w_type

def get_window_states(w_id):
    out = run_cmd(["xprop", "-id", str(w_id), "_NET_WM_STATE"])
    states = []
    if "_NET_WM_STATE_MAXIMIZED_VERT" in out:
        states.append("maximized_vert")
    if "_NET_WM_STATE_MAXIMIZED_HORZ" in out:
        states.append("maximized_horz")
    if "_NET_WM_STATE_FULLSCREEN" in out:
        states.append("fullscreen")
    return states

def get_viewport():
    lines = run_cmd(["wmctrl", "-d"]).splitlines()
    for line in lines:
        parts = line.split()
        if len(parts) >= 6 and parts[1] == "*":
            if parts[5] != "N/A":
                return [int(n) for n in parts[5].split(",")]
            break
    return [0, 0]

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
    global xof, yof
    w_list = [l.split() for l in run_cmd(["wmctrl", "-lpG"]).splitlines() if l.strip()]
    relevant = []
    for w in w_list:
        if len(w) >= 7 and check_window(w[0]):
            x = int(w[3]) + xof
            y = int(w[4]) + yof
            width = int(w[5])
            height = int(w[6])
            app_name = app(w[2])
            desktop = w[1]
            states = get_window_states(w[0])
            line = app_name + " " + desktop + " " + str(x) + " " + str(y) + " " + str(width) + " " + str(height)
            if states:
                line += " " + ",".join(states)
            relevant.append(line)
    return relevant

def read_calibration():
    global xof, yof
    try:
        with open(wfile, "r") as f:
            lines = [l.split() for l in f.read().splitlines() if l.strip()]
        if lines:
            calibr = lines.pop()
            if calibr[0] == 'calibration' and len(calibr) >= 3:
                xof = int(calibr[1])
                yof = int(calibr[2])
    except (IOError, OSError):
        pass

def save_positions(wfile, winlist):
    with open(wfile, "wt") as out:
        for l in winlist:
            out.write(l + "\n")
        l = "calibration " + str(xof) + " " + str(yof)
        out.write(l + "\n")

def read_window_ids():
    w_list = [l.split() for l in run_cmd(["wmctrl", "-lpG"]).splitlines() if l.strip()]
    relevant = [[w[2], w[0]] for w in w_list if len(w) >= 3 and check_window(w[0])]
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
        w_class = run_cmd(["xprop", "-id", str(w_id), "WM_CLASS"])
        if app_name.lower() in w_class.lower():
            return True
    except Exception:
        pass
    return False

def open_appwindow(app_name, loc, states=None):
    ws1 = set(l.split()[0] for l in run_cmd(["wmctrl", "-lp"]).splitlines() if l.strip())
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
        lines = [l.split() for l in run_cmd(["wmctrl", "-lp"]).splitlines() if l.strip()]
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
            reposition_window(matched_wid, loc, states)
            break

def reposition_window(w_id, loc, states=None):
    x, y, w, h, d = [str(n) for n in loc]
    subprocess.call(["wmctrl", "-ir", str(w_id), "-b", "remove,maximized_horz,maximized_vert"])
    subprocess.call(["wmctrl", "-ir", str(w_id), "-e", "0," + x + "," + y + "," + w + "," + h])
    subprocess.call(["wmctrl", "-ir", str(w_id), "-t", d])
    if states:
        for s in states:
            if s and s != "none":
                subprocess.call(["wmctrl", "-ir", str(w_id), "-b", "add," + s])

def run_remembered():
    global xof, yof
    res = get_viewport()
    running = read_window_ids()
    try:
        with open(wfile, "r") as f:
            lines = [l.split() for l in f.read().splitlines() if l.strip()]
        if lines:
            calibr = lines.pop()
            if calibr[0] == 'calibration' and len(calibr) >= 3:
                xof = int(calibr[1])
                yof = int(calibr[2])
            else:
                lines.append(calibr)            
            for l in lines:
                if len(l) < 6:
                    continue
                l[2] = str(int(l[2]) - res[0])
                l[3] = str(int(l[3]) - res[1])
                apps = [a[0] for a in running]
                location = l[2:6] + [l[1]]
                states = l[6].split(",") if len(l) > 6 and l[6] != "none" else []
                if l[0] in apps:
                    idx = apps.index(l[0])
                    reposition_window(running[idx][1], location, states)
                    running.pop(idx)
                else:
                    open_appwindow(l[0], location, states)
    except (IOError, OSError):
        pass

def start_calibration_window():
    calibw = subprocess.Popen(["xmessage", "-title", "savelayout_calib", "Calibration"])
    return calibw

def stop_calibration_window(calibw):
    try:
        calibw.terminate()
    except OSError:
        pass

def find_calib_window(wids=None):
    w_list = [l.split() for l in run_cmd(["wmctrl", "-lpG"]).splitlines() if l.strip()]
    for w in w_list:
        if len(w) >= 7:
            if wids and w[0] in wids:
                return w
            if len(w) >= 9 and "savelayout_calib" in " ".join(w[8:]):
                return w
            if len(w) >= 9 and w[8] == "xmessage":
                return w
    return None

def do_calibration():
    global xof, yof
    before_wids = set(l.split()[0] for l in run_cmd(["wmctrl", "-lpG"]).splitlines() if l.strip())
    calibw = start_calibration_window()
    time.sleep(1)

    lines = [l.split() for l in run_cmd(["wmctrl", "-lpG"]).splitlines() if l.strip()]
    new_wids = set(w[0] for w in lines) - before_wids

    calib_win = find_calib_window(new_wids)
    if not calib_win:
        stop_calibration_window(calibw)
        print("Error: Could not locate calibration window.")
        return

    wid = calib_win[0]
    pos = calib_win[3:7] + [u'0']
    reposition_window(wid, pos)
    time.sleep(0.2)

    after_win = find_calib_window(set([wid]))
    stop_calibration_window(calibw)
    if not after_win:
        print("Error: Calibration window lost after reposition.")
        return

    pos_after = after_win[3:7] + [u'0']
    xof = int(pos[0]) - int(pos_after[0])
    yof = int(pos[1]) - int(pos_after[1])
    print("xof=", xof)
    print("yof=", yof)    
    with open(wfile, "wt") as out:
        l = "calibration " + str(xof) + " " + str(yof)
        out.write(l + "\n")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Save and restore desktop window layout.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-save", "--save", action="store_true", help="record window positions")
    group.add_argument("-load", "--load", action="store_true", help="restore window positions (default)")
    group.add_argument("-calibrate", "--calibrate", action="store_true", help="display and set calibration offsets")
    return parser.parse_args()

def main():    
    args = parse_arguments()
    if args.save:
        read_calibration()
        wlist = read_windows()
        save_positions(wfile, wlist)
    elif args.calibrate:
        do_calibration()
    else:
        # Default behavior: load
        run_remembered()

if __name__ == '__main__':
    main()
