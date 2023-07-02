#!/usr/bin/env python3

import pyall
import gpxpy
import pathlib
import tkinter as tk
from tkinter import filedialog as fd 
from tkinter import ttk

# Extract track from Kongsberg .all multibeam-data, save as GPX file
# Depends on pyall.py from https://github.com/guardiangeomatics/pyall

def process_multibeam_data(filename):
    reader = pyall.ALLReader(filename)
    reader.rewind() #rewind to the start of the file
    
    selectedPositioningSystem = None
    pingCount = 0

    positions = []
    
    start_time = None
    last_time = None

    while reader.moreData():
        TypeOfDatagram, datagram = reader.readDatagram()
        if TypeOfDatagram == 'D' or TypeOfDatagram == 'X':
            datagram.read()
            if len(datagram.Depth) == 0:
                continue

        if TypeOfDatagram == 'X': #XYZ 88 Datagram (Ping)
            datagram.read()

            nadirBeam = int(datagram.NBeams / 2)
            #print (("Nadir Depth: %.3f AcrossTrack %.3f TransducerDepth %.3f" % (datagram.Depth[nadirBeam], datagram.AcrossTrackDistance[nadirBeam], datagram.TransducerDepth)))
            ocean_depth = datagram.Depth[nadirBeam] + datagram.TransducerDepth
            #print(ocean_depth)
            pingCount += 1
            continue

        if (TypeOfDatagram == 'P'): # Position Datagram
            datagram.read()
            if (selectedPositioningSystem == None):
                selectedPositioningSystem = datagram.Descriptor
            if (selectedPositioningSystem == datagram.Descriptor):
                latitude = datagram.Latitude # Stored as 4S in datagram - Binary field is signed, stored as 4 bytes
                longitude = datagram.Longitude # Stored as 4S in datagram - Binary field is signed, stored as 4 bytes
                heading = datagram.Heading
                
                position_datetime = reader.currentRecordDateTime()
                #print(position_datetime)

                if start_time == None:
                    start_time = position_datetime
                    positions.append([position_datetime, latitude, longitude])
                    #print("Made starttime")
                else:
                    #if (position_datetime-start_time) < datetime.timedelta(seconds=10):
                    #print("At least 10 sec?", position_datetime)
                    positions.append([position_datetime, latitude, longitude])
                    last_time = position_datetime

                #print(f"{latitude}, {longitude}, {position_datetime}")
                

        if TypeOfDatagram == 'A': # Attitude Datagram
            datagram.read()
            if len(datagram.Attitude) > 0:
                roll = datagram.Attitude[0][3]
                pitch = datagram.Attitude[0][4]
                heave = datagram.Attitude[0][5]
        if TypeOfDatagram == 'R': # Runtime parameters datagram
            datagram.read()
            maximumPortCoverageDegrees = datagram.maximumPortCoverageDegrees
            maximumPortWidth = datagram.maximumPortWidth
            maximumStbdCoverageDegrees = datagram.maximumStbdCoverageDegrees
            maximumStbdWidth = datagram.maximumStbdWidth
            depthmode = datagram.DepthMode + "+" + datagram.TXPulseForm
            absorptioncoefficient = datagram.absorptionCoefficient
            pulselength = datagram.transmitPulseLength
            tvg = datagram.tvg
            dualswath = datagram.dualSwathMode
            spikefilter = datagram.filterSetting
            stabilisation = datagram.yawAndPitchStabilisationMode
            mindepthgate = datagram.minimumDepth
            maxdepthgate = datagram.maximumDepth
    
    print(pingCount)
    return positions

def process_single_file(tkui, filepath):
    print("Process single file")
    path = pathlib.Path(filepath)
    
    tkui.progressBar["value"] = 0
    tkui.progressBar['maximum'] = 1
    tkui.statusLabel['text'] = f"Processing file {path.name}..."
    tkui.update()

    positions = process_multibeam_data(path)

    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = path.name
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    for item in positions:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(item[1], item[2], elevation=None))

    xml_string = gpx.to_xml()
    
    tkui.progressBar["value"] = 1
    tkui.statusLabel['text'] = f"Finished!"
    tkui.update()

    #print('Created GPX:', xml_string)
    print("Trackpoints made:", len(positions))
    
    selectable_filetypes = [('GPX', '*.gpx')]
    saveas_file = fd.asksaveasfile(mode='w', initialfile=path.stem, filetypes = selectable_filetypes, defaultextension = selectable_filetypes)
    if saveas_file is None: # asksaveasfile return `None` if dialog closed with "cancel".
        return

    saveas_file.write(xml_string)
    saveas_file.close()
    print("File saved", saveas_file.name)
    tkui.progressBar["value"] = 0
    tkui.statusLabel['text'] = f"Waiting for user input..."
    tkui.update()

def process_folder(tkui, directorypath):
    print("Process all .all files in folder")
    path = pathlib.Path(directorypath).glob('**/*.all')
    files = [x for x in path if x.is_file()]
    print(files)

    tkui.progressBar["value"] = 0
    tkui.progressBar['maximum'] = len(files)

    gpx = gpxpy.gpx.GPX()

    total_positions = 0

    for idx, file in enumerate(files):
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = file.name
        gpx.tracks.append(gpx_track)
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        positions = process_multibeam_data(file)
        for item in positions:
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(item[1], item[2], elevation=None))
            total_positions = total_positions + 1
        
        tkui.statusLabel['text'] = f"Processing file {file.name}..."
        tkui.progressBar["value"] = idx+1
        tkui.update()
    
    print(total_positions)
    xml_string = gpx.to_xml()
    #print('Created GPX:', xml_string)

    tkui.progressBar["value"] = tkui.progressBar["maximum"]
    tkui.statusLabel['text'] = f"Finished!"
    tkui.update()

    selectable_filetypes = [('GPX', '*.gpx')]
    saveas_file = fd.asksaveasfile(mode='w', initialfile="all_to_gpx", filetypes = selectable_filetypes, defaultextension = selectable_filetypes)
    if saveas_file is None: # asksaveasfile return `None` if dialog closed with "cancel".
        return
    saveas_file.write(xml_string)
    saveas_file.close()
    tkui.progressBar["value"] = 0
    tkui.statusLabel['text'] = f"Waiting for user input..."
    tkui.update()

class Main(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        errmsg = 'Error!'
        self.geometry('400x160')
        self.resizable(False, False)
        self.title('.all to .gpx')

        tk.Label(self, text="Extract track from multibeam files,\nKongsberg .all and save the GPS track as .gpx.").pack(fill=tk.X)
        self.btn_open_file = tk.Button(self, text='Click to open File', command=self.callback_file).pack(fill=tk.X)
        self.btn_open_dir = tk.Button(self, text='Click to open Directory', command=self.callback_directory).pack(fill=tk.X)
        self.progressBar = ttk.Progressbar(self, orient="horizontal", length=200,mode="determinate")
        self.progressBar.pack(fill=tk.X)
        tk.Label(self, text="Status:").pack(fill=tk.X)
        self.statusLabel = tk.Label(self, text="Waiting for user input...")
        self.statusLabel.pack(fill=tk.X)

    def callback_file(self):
        selectable_filetypes = (('Kongsberg .all','*.all'),)
        filepath = fd.askopenfilename(title="Select one .all file", filetypes=selectable_filetypes)
        if filepath is None or filepath == "": # asksaveasfile return `None` if dialog closed with "cancel".
            return
        process_single_file(self, filepath)

    def callback_directory(self):
        directorypath= fd.askdirectory(title="Select directory with .all") 
        if directorypath is None or directorypath == "": # askdirectory return `None` if dialog closed with "cancel".
            return
        process_folder(self, directorypath)


def main():
    app = Main()
    app.mainloop()
    

if __name__ == "__main__":
    main()
