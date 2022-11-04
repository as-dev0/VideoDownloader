import gi
import yt_dlp
import ctypes
import threading
import asyncio
import time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class DownloaderWindow(Gtk.Window):

    def __init__(self):

        # Create Gtk window
        super().__init__(title="Video Downloader")
        self.set_size_request(800,500)
        self.set_border_width(20)
        self.connect("destroy", Gtk.main_quit)

        self.downloadLocation = ""
        self.titleLabels = []
        self.progressLabels = []
        self.downloadThreads = {}       # This dictionary is of the form { videoNumber1 : downloadThread1 , videoNumber2 : downloadThread2 , ...  }
        self.progressPercentages = {}   # This dictionary is of the form { videoNumber1 : percentageProgressOfVideo1 , videoNumber2: percentageProgressOfVideo2 , ...  }
        self.titlesToAdd = {}           # This dictionary is of the form { videoNumber1 : titleOfVideo1 , videoNumber2 : titleOfVideo2 , ...}
        self.idToN = {}                 # This dictionary links video IDs to its number in the program = {  id1: videoNumber1, id2: videoNumber2self.idToN }
        self.lock = threading.Lock()

        scrollWindow = Gtk.ScrolledWindow()
        scrollWindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # self.vbox will contain all the Gtk widgets
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)

        header = Gtk.Label()
        header.set_label("Enter URL here:")
        self.vbox.add(header)

        self.url = Gtk.Entry()
        self.vbox.add(self.url)

        self.hbox = Gtk.Box(spacing = 20)

        downloadButton = Gtk.Button(label="Download")
        downloadButton.connect("clicked", self.download)
        self.hbox.pack_start(downloadButton, False, False, 0)

        changeDownloadLocation = Gtk.Button(label="Change download location")
        changeDownloadLocation.connect("clicked", self.selectDownloadLocation)
        self.hbox.pack_end(changeDownloadLocation, False, True, 0)

        self.vbox.add(self.hbox)

        scrollWindow.add(self.vbox)

        self.add(scrollWindow)

        GLib.timeout_add(500, self.autoRun)

    # This function is called by the GLib loop every 500ms
    def autoRun(self):

        self.autoUpdateProgress()
        self.autoAddTitles()
        return True

    # This function is run automatically every 500 ms and updates all progress bars
    def autoUpdateProgress(self):

        for i in range(len(self.titleLabels)):
            if i in self.progressPercentages:
                self.progressLabels[i].set_label(str(round(self.progressPercentages[i]*100)) + " %" )

        return True

    # This function is run automatically every 500ms and adds titles to the progress
    # bars after they are fetched
    def autoAddTitles(self):

        if len(self.titlesToAdd.keys()) != 0:

            keysToRemove = []

            for k in self.titlesToAdd:

                self.titleLabels[k].set_label(self.titlesToAdd[k])
                keysToRemove.append(k)
            
            for k in keysToRemove:
                del self.titlesToAdd[k]

        return True

    # Terminate thread at position threadNumber in self.downloadThreads
    def terminateThread(self, widget, threadNumber):

        print("\nTerminating thread " + str(threadNumber))
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.downloadThreads[threadNumber].ident), ctypes.py_object(SystemExit))
    
    # Adds a progress bar for a video
    def addProgressBar(self, title, numberProgressBars):

        nestedBox = Gtk.Box(spacing=20)

        titleLabel = Gtk.Label()
        titleLabel.set_label(title)
        nestedBox.add(titleLabel)

        cancelButton = Gtk.Button(label="Cancel")
        cancelButton.connect("clicked", self.terminateThread, numberProgressBars)
        nestedBox.pack_end(cancelButton, False, True, 10)

        percentageLabel = Gtk.Label()
        percentageLabel.set_label("0 %")
        nestedBox.pack_end(percentageLabel, False, True, 10)

        self.titleLabels.append(titleLabel)
        self.progressLabels.append(percentageLabel)
        self.vbox.add(nestedBox)
        self.show_all()

    # A progress hook that updates the download progress in self.progressPercentages
    # The parameter d is a dictionary of information supplied by yt_dlp
    def progressHook(self, d):

        p = d['_percent_str']
        p = p.replace('%','')
    
        for id in self.idToN:

            if id == d['info_dict']['id']:
                
                self.progressPercentages[self.idToN[id]] = float(p[7:10])/100
                break

    # This function is run in a separate thread and obtains the video title and downloads
    # the video at the specified url
    def downloadVideo(self, url, videoNumber):

        if url == "" :
            self.lock.acquire()
            self.titlesToAdd[videoNumber] = "Empty url"
            self.lock.release()
            
            return
            
        try:
            print("URL = " + url)
            infoDict = yt_dlp.YoutubeDL().extract_info(url, download=False)
            print("Title = " + infoDict["title"])

            self.lock.acquire()
            self.titlesToAdd[videoNumber] = infoDict["title"]
            self.idToN[infoDict["id"]] = videoNumber
            self.lock.release()

            if self.downloadLocation == "":
                yt_dlp.YoutubeDL({'progress_hooks':[self.progressHook]}).download([url])
            else:
                yt_dlp.YoutubeDL({'outtmpl':self.downloadLocation+"/%(title)s.%(ext)s", 'progress_hooks':[self.progressHook]}).download([url])

        except Exception as e:
            print("Error " + str(e))
            self.lock.acquire()
            self.titlesToAdd[videoNumber] = "Error: " + str(e)
            self.lock.release()

    # Downloads a video and selects the highest quality available.
    # This function runs when the user clicks on the Download button.
    def download(self, widget):

        url = self.url.get_text()
        videoNumber = len(self.titleLabels)
        self.addProgressBar("Obtaining title...", videoNumber)

        downloadThread = threading.Thread(target=self.downloadVideo, args=(url, videoNumber))
        self.downloadThreads[videoNumber] = downloadThread
        downloadThread.start()

    # Opens a dialog that allows the user to select a folder to be used
    # as the download location. This function is run when the user clicks
    # on the change download location button
    def selectDownloadLocation(self, widget):

        dialog = Gtk.FileChooserDialog(title="Choose a file", action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN,Gtk.ResponseType.OK)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:

            filename = dialog.get_filename()
            self.downloadLocation = filename
            print("Selected download location: " + filename)

        dialog.destroy()


if __name__ == "__main__":

    win = DownloaderWindow()
    win.show_all()

    Gtk.main()
