import gi
import yt_dlp
import ctypes
import threading
import asyncio
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class DownloaderWindow(Gtk.Window):

    def __init__(self):

        # Create Gtk window
        super().__init__(title="Video Downloader")
        self.set_size_request(500,300)
        self.set_border_width(20)
        self.connect("destroy", Gtk.main_quit)

        self.downloadLocation = ""
        self.progressBars = []
        self.titles = []
        self.downloadThreads = []
        self.filenames = {}
        self.progressPercentages = []
        
        # self.vbox will contain all the Gtk widgets
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        header = Gtk.Label()
        header.set_label("Enter URL here:")
        self.vbox.add(header)

        self.url = Gtk.Entry()
        self.vbox.add(self.url)

        downloadButton = Gtk.Button(label="Download")
        downloadButton.connect("clicked", self.download)
        self.vbox.add(downloadButton)

        changeDownloadLocation = Gtk.Button(label="Change download location")
        changeDownloadLocation.connect("clicked", self.selectDownloadLocation)
        self.vbox.add(changeDownloadLocation)

        self.add(self.vbox)

        GLib.timeout_add(300, self.autoUpdateProgress)

    # This function is run automatically every 300 ms and updates all progress bars
    def autoUpdateProgress(self):

        if len(self.progressBars) != len(self.progressPercentages):
            return True

        for i in range(len(self.progressBars)):
            self.progressBars[i].set_fraction(self.progressPercentages[i])
        
        return True

    # Terminate thread at position threadNumber in self.downloadThreads
    def terminateThread(self, widget, threadNumber):

        print("\nTerminating thread " + str(threadNumber))
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.downloadThreads[threadNumber].ident), ctypes.py_object(SystemExit))
    
    # Adds a progress bar for a video
    def add_progress_bar(self, title, numberProgressBars):

        print("\nAdding progress bar")

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

        self.vbox.add(nestedBox)
        self.show_all()

    # A progress hook that updates the download progress in self.progressPercentages
    def updateProgress(self, d):

        p = d['_percent_str']
        p = p.replace('%','')
        
        if d['filename'] not in self.filenames:
            self.filenames[d['filename']] = len(self.titles) - 1
            n = len(self.titles) - 1
        else:
            n = self.filenames[d['filename']]

        try:
            self.progressPercentages[n] = float(p[7:11])/100
        except:
            self.progressPercentages.append(float(p[7:11])/100)

    # Downloads a video and selects the highest quality available.
    # This function runs when the user clicks on the Download button.
    def download(self, widget):

        def downloadVideo(title, url):

            if self.downloadLocation == "":
                yt_dlp.YoutubeDL({'progress_hooks':[self.updateProgress]}).download([self.url.get_text()])
            else:
                yt_dlp.YoutubeDL({ 'outtmpl':self.downloadLocation+"/%(title)s.%(ext)s", 'progress_hooks':[self.updateProgress]}).download([self.url.get_text()])

        try:
            print("URL = " + self.url.get_text())
            infoDict = yt_dlp.YoutubeDL().extract_info(self.url.get_text(), download=False)
            print("Title = " + infoDict["title"])
        except:
            print("Please enter valid url")
            return

        self.add_progress_bar(infoDict["title"], len(self.progressBars))

        downloadThread = threading.Thread(target=downloadVideo, args=(infoDict["title"], self.url.get_text()))
        self.downloadThreads.append(downloadThread)
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
            
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()


win = DownloaderWindow()
win.show_all()

Gtk.main()
