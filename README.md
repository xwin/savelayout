## Save and restore window layout
This script is originated from this [askubuntu.com post](https://askubuntu.com/questions/193569/is-there-a-way-to-store-the-current-desktop-layout). Calibration function was added to determine offsets to correct for window manger elements. The offsets are applied when saving windows so the restored windows end up in the same position. Added the ability to save and restore desktop placement for each window.

### Requirements
This script is compatible with python2.7 and python3.x and should run without changes on either of versions. The script is using **wmctrl** and **ps** utilities and these should installed by default on any system. If they are not installed, on Ubuntu or Debian use
```
sudo apt-get install wmctrl procps
```
The script is also using **xmessage** utility to perform calibration. The **xmessage** is located in x11-utils package on Ubuntu and should be installed by default.
### How to use
First run with -calibrate flag
```
python3 savelayout.py -calibrate
xof= -2
yof= -52
```
This will perform calibration run and save calibration string into the configuration file. All of the saved window positions will be erased from the configuration file.<br>
To save window placements first position your windows as you like them, then run

``` 
python3 savelayout.py -save
```
To restore layout, run with -load or without any parameters

```
python3 savelayout.py -load
```
The utility should be able to read the configuration file without the calibration string. To save the calibration string run:

```
python3 savelayout.py -load
python3 savelayout.py -calibrate
python3 savelayout.py -save
```

