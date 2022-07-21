## Save and restore window layout
This script is originated from this [askubuntu.com post](https://askubuntu.com/questions/193569/is-there-a-way-to-store-the-current-desktop-layout). Calibration function was added to determine offsets to correct for window manger elements. The offsets are applied when saving windows so the restored windows end up in the same position. The ability to save desktop number is also added although it is not yet restored.

### Requirements
This script is using python3 syntax so python3 is required to run it. The script is using **wmctrl** and **ps** utilities and these should installed by default on any system. If they are not installed, on Ubuntu or Debian use
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
Next change the lines at the top of the script to set them to the printed offsets. The utility is ready for use.  
To save window layouts first position your windows as you like them, then run

``` 
python3 savelayout.py -save
```
To restore layout, run with -load or without any parameters

```
python3 savelayout.py -load
```
