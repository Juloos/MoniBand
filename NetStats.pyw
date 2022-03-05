import subprocess as sp
import tkinter as tk
import threading as th
import time

from SysTrayIcon import *


def get_netstats_bytes():
    rtn = []
    for line in sp.check_output("NetStat -e", shell=True, universal_newlines=True).split("\n"):
        if line.startswith("Bytes"):
            for element in line.replace("Bytes", "").strip().split(" "):
                if element.isnumeric():
                    rtn.append(int(element))
    return tuple(rtn)

def pup(num: float) -> tuple:
    return pretty_unity_print(num)

def pretty_unity_print(num: float) -> tuple:
    unites = {10**-12: "", 10**-9: "n", 10**-6: "μ", 10**-3: "m", 10**3: "k", 10**6: "M", 10**9: "G", 10**12: "T"}
    for ent in unites:
        if 10**0 <= num / ent < 10**3:
            return num / ent, unites[ent]
    return num, ""

class Tray(th.Thread):
    def __init__(self, icon, hover_text, menu_options, on_quit, default_menu_index=0):
        th.Thread.__init__(self)
        self.icon = icon
        self.hover = hover_text
        self.opts = menu_options
        self.on_quit = on_quit
        self.dmi = default_menu_index
        self.start()
    
    def run(self):
        SysTrayIcon(self.icon, self.hover, self.opts, on_quit=self.on_quit, default_menu_index=self.dmi)

class WinSystemTray(th.Thread):
    def __init__(self):
        th.Thread.__init__(self)
        self._dataset = {}
        self.exiting = False

        self.win = tk.Tk()
        self.win.withdraw()
        self.win.title("Internet Consumption")
        self.win.iconbitmap("Internet Logo.ico")
        self.win.protocol("WM_DELETE_WINDOW", self.win.withdraw)
        self.win.resizable(height = False, width = False)
        self._tkrdata = tk.StringVar(self.win)
        self._tksdata = tk.StringVar(self.win)
        self._tktdata = tk.StringVar(self.win)
        self._tkrdataspeed = tk.StringVar(self.win)
        self._tksdataspeed = tk.StringVar(self.win)
        self._tktdataspeed = tk.StringVar(self.win)
        rframe = tk.LabelFrame(self.win, text = "Recieved data", width = 160, height = 90, font=("Calibri", 12))
        sframe = tk.LabelFrame(self.win, text = "Sent data", width = 160, height = 90, font=("Calibri", 12))
        tframe = tk.LabelFrame(self.win, text = "Total transfers", width = 160, height = 90, font=("Calibri", 12))
        rframe.grid(row = 1, column= 1, padx = 10, pady = 10)
        sframe.grid(row = 1, column= 2, padx = 10, pady = 10)
        tframe.grid(row = 1, column= 3, padx = 10, pady = 10)
        rframe.pack_propagate(0)
        sframe.pack_propagate(0)
        tframe.pack_propagate(0)
        tk.Label(rframe, textvariable = self._tkrdata, font=("Calibri", 16)).pack(side = tk.TOP)
        tk.Label(sframe, textvariable = self._tksdata, font=("Calibri", 16)).pack(side = tk.TOP)
        tk.Label(tframe, textvariable = self._tktdata, font=("Calibri", 16)).pack(side = tk.TOP)
        tk.Label(rframe, textvariable = self._tkrdataspeed, font=("Calibri", 16)).pack(side = tk.TOP)
        tk.Label(sframe, textvariable = self._tksdataspeed, font=("Calibri", 16)).pack(side = tk.TOP)
        tk.Label(tframe, textvariable = self._tktdataspeed, font=("Calibri", 16)).pack(side = tk.TOP)

        self.start()
        Tray("Internet Logo.ico", "Internet Consumption", (("Open", "Internet Logo.ico", self.show_win),
                                                           ), on_quit=self.quit)
        self.win.mainloop()

    def show_win(self, sysTrayIcon):
        self.win.deiconify()

    def quit(self, sysTrayIcon):
        self.exiting = True

    def run(self):
        rdata, sdata = 0, 0
        rdataspeed, sdataspeed = 0, 0
        last_data = get_netstats_bytes()
        last_rdata, last_sdata = 0, 0
        timer = 0
        while not self.exiting:
            wait = time.time()
            data = get_netstats_bytes()
            addrsdata = (data[0] - last_data[0]) / 8, (data[1] - last_data[1]) / 8
            if all([addrsdata[i] >= 0 for i in range(2)]):
                rdata += addrsdata[0]
                sdata += addrsdata[1]
            r, s, t = pup(rdata), pup(sdata), pup(rdata + sdata)
            r, s, t = f"{r[0]:3.3f} {r[1]}o", f"{s[0]:3.3f} {s[1]}o", f"{t[0]:3.3f} {t[1]}o"
            self._tkrdata.set(r)
            self._tksdata.set(s)
            self._tktdata.set(t)
            if timer == 0:
                dataspeed = rdata - last_rdata, sdata - last_sdata
                self._dataset[wait] = dataspeed
                rs, ss, ts = pup(dataspeed[0]), pup(dataspeed[1]), pup(dataspeed[0] + dataspeed[1])
                rs, ss, ts = f"{rs[0]:3.1f} {rs[1]}o/s", f"{ss[0]:3.1f} {ss[1]}o/s", f"{ts[0]:3.1f} {ts[1]}o/s"
                self._tkrdataspeed.set(rs)
                self._tksdataspeed.set(ss)
                self._tktdataspeed.set(ts)
                last_rdata, last_sdata = rdata, sdata

            timer = (timer + 1) % 10
            last_data = data
            while time.time() - wait < 0.1:
                pass


if __name__ == "__main__":
    app = WinSystemTray()