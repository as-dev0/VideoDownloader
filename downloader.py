import gi
import yt_dlp
import threading
import ctypes
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk 

class DownloaderWindow(Gtk.Window):

    def __init__(self):

        super().__init__(title="Video Downloader")
        self.set_size_request(500,300)
        self.set_hexpand(False)
        self.set_border_width(20)
        self.connect("destroy", Gtk.main_quit)

        self.progressBars = []
        self.isBarUpdated = []
        self.titles = []
        self.downloadThreads = []

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        header = Gtk.Label()
        header.set_label("Enter URL here:")
        self.vbox.add(header)

        self.url = Gtk.Entry()
        self.vbox.add(self.url)

        downloadButton = Gtk.Button(label="Download")
        downloadButton.connect("clicked", self.download)
        self.vbox.add(downloadButton)

        self.add(self.vbox)

    def terminateThread(self, widget, threadNumber):

        print("Attempting to terminate thread " + str(threadNumber))
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.downloadThreads[threadNumber].ident), ctypes.py_object(SystemExit))
    
    def add_progress_bar(self, title, numberProgressBars):

        print("Adding progress bar")

        nestedBox = Gtk.Box(spacing=20)
        progressBar = Gtk.ProgressBar()
        progressBar.set_text(title)
        progressBar.set_show_text(title)
        nestedBox.add(progressBar)

        cancelButton = Gtk.Button(label="Cancel")
        cancelButton.connect("clicked", self.terminateThread, numberProgressBars)
        nestedBox.add(cancelButton)

        self.titles.append(title)
        self.progressBars.append(progressBar)
        self.isBarUpdated.append(False)

        self.vbox.add(nestedBox)
        self.show_all()

    def updateProgress(self, d):

        p = d['_percent_str']
        p = p.replace('%','')

        self.progressBars[0].set_fraction(float(p[7:11])/100)
        self.progressBars[0].set_text(self.titles[0] + "  " + str(float(p[7:11])) + "%")
        self.progressBars[0].set_show_text(self.titles[0] + "  " + str(float(p[7:11])) + "%")

    def download(self, widget):

        def downloadVideo():
            
            print("URL is " + self.url.get_text())
            infoDict = yt_dlp.YoutubeDL().extract_info(self.url.get_text(), download=False)
            print("Title is " + infoDict["title"])
            self.add_progress_bar(infoDict["title"], len(self.progressBars))
            yt_dlp.YoutubeDL({'progress_hooks':[self.updateProgress]}).download([self.url.get_text()])

        p = threading.Thread(target=downloadVideo)
        self.downloadThreads.append(p)
        p.start()

win = DownloaderWindow()
win.show_all()
Gtk.main()