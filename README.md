# laser-companion
### v1.0 / March 20, 2021 / *by* melyux

A companion script to communicate with Wainlux (or related) laser engravers and cutters over Wi-Fi. Motivated by the Wainlux app removing the ability to connect the engraver to Wi-Fi networks. To use this script, connect the computer running it to the same network/hotspot as the engraver.

In Terminal or command line, `cd` to the directory with the script, and run `python laser-companion.py`

Currently supports:

1. Setting the Wi-Fi name and password for the engraver to connect to
2. Resetting the Wi-Fi to connect to a hotspot (usually causes the engraver to search for Wi-Fi networks around it and try connecting to them with the password *aaaabbbb*).
