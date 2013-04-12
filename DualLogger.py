# -*- coding: utf-8 -*-
import serial
from time import sleep
import time
import re
import logging
import datetime
import pygtk
pygtk.require('2.0')
import gtk
import threading
import gobject
import time
gobject.threads_init()


#Todo: Setup monitor thread, connect checkbuttons

RATE=9600
LOCATIONS=['/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3',
'/dev/ttyS0','/dev/ttyS2','/dev/ttyS3', '/dev/ttyS4']

class scale(object):
    #Object to make the number of scales modular.  Includes the serial port, an id, and connection status
    def __init__(self, scaleId):
        self.logging=False
        self.connected=False
        self.scaleId=scaleId
        self.address=''
        self.weight='No Data'
    
    def connect(self,locations, rate):
        for address in locations:
            try:
                self.serial=serial.Serial(address, rate, timeout=1)
                self.serial.flushInput()
                self.serial.write('p' + '\r\n')
                buf=self.serial.readline() #blank
                #print 'wrote to' + address
                #print str(buf)
                if buf: #if you didn't time out, attempt to read the whole string
                    #print "didn't time out passed first if"
                    buf=self.serial.readline() #blank
                    buf=self.serial.readline() #date
                    buf=self.serial.readline() #time
                    buf=self.serial.readline() #blank
                    buf=self.serial.readline() #id
                    for text in buf.split():
                        try:
                           #print 'tried split'
                            scaleid=float(text)
                            if(scaleid==float(self.scaleId)):
                                self.address=address
                                self.connected=True
                                buf=self.serial.readline() #user id
                                buf=self.serial.readline() #blank
                                buf=self.serial.readline() #weight
                                buf=self.serial.readline() #blank
                                buf=self.serial.readline() #blank
                                buf=self.serial.readline() #blank
                                buf=self.serial.readline() #blank
                                break
                        except:
                            _=''
                    
            except:
                _=''
            if self.address:
                        break
                    
                
class guiFramework(object):
    def __init__(self, locations, rate):
        self.window=gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Scale Measuring Program")
        self.window.connect("delete_event", self.delete_event)
        self.window.set_resizable(False)
        self.window.set_border_width(20)
        self.locations=locations
        self.rate=rate
        #self.initializeSerial(None, None)
        self.details='No details were entered for this run.'
        self.speed='No speed was entered for this run.'
        self.guiInitialization()
        self.window.show_all()
        date=datetime.date.today()
        self.filename=str(date.month) +'-'+ str(date.day)
        self.filenumber=0
        self.initializeLogger()
        self.logging=False
        self.scale1=scale(1)
        self.scale2=scale(2)
        self.width=12
        self.monitorThread=gtkThread(self)
        
    def guiInitialization(self):
        #Create the various boxes necessary for gtk windows
        self.bigVBox=gtk.VBox(False, 2)
        self.window.add(self.bigVBox)
        self.scalesbox=gtk.HBox(False, 2)
        self.runbox=gtk.VBox(False, 2)
        self.mainlogbox=gtk.HBox(False, 2)
        self.statusbox=gtk.HBox(False, 2)
        self.bigVBox.pack_start(self.scalesbox, False, False, 0)
        self.bigVBox.pack_start(self.runbox, False, False, 0)
        self.bigVBox.pack_start(self.mainlogbox, False, False, 0)
        self.bigVBox.pack_start(self.statusbox, False, False, 0)
        
        #Now set up the individual boxes, from the top down
        
        #First, create the sub boxes to house scales 1 and 2
        self.scale1box=gtk.VBox(False, 2)
        self.scale2box=gtk.VBox(False, 2)
        self.scalesbox.pack_start(self.scale1box, False, False, 0)
        self.scalesbox.pack_start(self.scale2box, False, False, 0)
        
        #Create scale box 1 elements
        #Name and include
        self.scale1labelbox=gtk.HBox(False, 2)
        self.scale1Label=gtk.Label('Scale 1')
        self.scale1Include=gtk.CheckButton('Include', False)
        self.scale1Include.connect('toggled',self.toggle_event, '1')
        self.scale1labelbox.pack_start(self.scale1Label, False, False, 0)
        self.scale1labelbox.pack_start(self.scale1Include, False, False, 0)
        #Disconnect/connect
        self.scale1buttonbox=gtk.HBox(False, 2)
        self.scale1ConnectButton=gtk.Button('Connect')
        self.scale1ConnectButton.connect('clicked', self.scaleConnect, '1')
        self.scale1DisconnectButton=gtk.Button('Disconnect')
        self.scale1DisconnectButton.connect('clicked',self.scaleDisconnect, '1')
        self.scale1buttonbox.pack_start(self.scale1ConnectButton, False, False, 0)
        self.scale1buttonbox.pack_start(self.scale1DisconnectButton, False, False, 0)
        #And status/weight
        self.scale1StatusBox=gtk.HBox(False, 2)
        self.scale1ConnectedFrame=gtk.Frame('Connected')
        self.scale1ConnectedLabel=gtk.Label('False')
        self.scale1WeightFrame=gtk.Frame('Weight')
        self.scale1WeightLabel=gtk.Label('No Data')
        self.scale1WeightFrame.add(self.scale1WeightLabel)
        self.scale1ConnectedFrame.add(self.scale1ConnectedLabel)
        self.scale1StatusBox.pack_start(self.scale1ConnectedFrame, False, False, 0)
        self.scale1StatusBox.pack_start(self.scale1WeightFrame, False, False, 0)
        #pack the box
        self.scale1box.pack_start(self.scale1labelbox, False, False, 0)
        self.scale1box.pack_start(self.scale1buttonbox, False, False, 0)
        self.scale1box.pack_start(self.scale1StatusBox, False, False, 0)
        
        #Create scale box 2 elements
        #Name and include
        self.scale2labelbox=gtk.HBox(False, 2)
        self.scale2Label=gtk.Label('Scale 2')
        self.scale2Include=gtk.CheckButton('Include', False)
        self.scale2Include.connect('toggled',self.toggle_event, '2')
        self.scale2labelbox.pack_start(self.scale2Label, False, False, 0)
        self.scale2labelbox.pack_start(self.scale2Include, False, False, 0)
        #Disconnect/connect
        self.scale2buttonbox=gtk.HBox(False, 2)
        self.scale2ConnectButton=gtk.Button('Connect')
        self.scale2ConnectButton.connect('clicked', self.scaleConnect, '2')
        self.scale2DisconnectButton=gtk.Button('Disconnect')
        self.scale2DisconnectButton.connect('clicked', self.scaleDisconnect, '2')
        self.scale2buttonbox.pack_start(self.scale2ConnectButton, False, False, 0)
        self.scale2buttonbox.pack_start(self.scale2DisconnectButton, False, False, 0)
        #And status/weight
        self.scale2StatusBox=gtk.HBox(False, 2)
        self.scale2ConnectedFrame=gtk.Frame('Connected')
        self.scale2ConnectedLabel=gtk.Label('False')
        self.scale2WeightFrame=gtk.Frame('Weight')
        self.scale2WeightLabel=gtk.Label('No Data')
        self.scale2WeightFrame.add(self.scale2WeightLabel)
        self.scale2ConnectedFrame.add(self.scale2ConnectedLabel)
        self.scale2StatusBox.pack_start(self.scale2ConnectedFrame, False, False, 0)
        self.scale2StatusBox.pack_start(self.scale2WeightFrame, False, False, 0)
        #pack the box
        self.scale2box.pack_start(self.scale2labelbox, False, False, 0)
        self.scale2box.pack_start(self.scale2buttonbox, False, False, 0)
        self.scale2box.pack_start(self.scale2StatusBox, False, False, 0)
             
             
        #Now move on to the run box (run data, speed, width)
        self.detailFrame=gtk.Frame('Run Details')
        self.detailEntry=gtk.Entry(200)
        self.detailEntry.connect('activate',self.getDetailText, '')
        self.detailFrame.add(self.detailEntry)
        self.widthAndSpeedBox=gtk.HBox(False, 0)
        self.speedFrame=gtk.Frame('Speed (FPM)')
        self.speedEntry=gtk.Entry(3)
        self.speedEntry.connect('activate', self.getSpeedText, '')
        self.speedFrame.add(self.speedEntry)
        self.widthFrame=gtk.Frame('Width (In.)')
        self.widthEntry=gtk.Entry(2)
        self.widthEntry.connect('activate',self.getWidthText, '')
        self.widthFrame.add(self.widthEntry)
        self.widthAndSpeedBox.pack_start(self.speedFrame, False, False, 0)
        self.widthAndSpeedBox.pack_start(self.widthFrame, False, False, 0)
        self.runbox.pack_start(self.detailFrame, False, False, 0)
        self.runbox.pack_start(self.widthAndSpeedBox, False, False, 0)
        
        #Finally (for now) the logging buttons
        self.loggingButton=gtk.Button('Start Logging')
        self.loggingButton.connect('clicked', self.startLogging, '')
        self.stopLoggingButton=gtk.Button('Stop Logging')
        self.stopLoggingButton.connect('clicked', self.stopLogging, '')
        self.newFileButton=gtk.Button('Use New File')
        self.newFileButton.connect('clicked', self.newFile, '')
        self.mainlogbox.pack_start(self.loggingButton, True, True, 0)
        self.mainlogbox.pack_start(self.stopLoggingButton, True, True, 0)
        self.mainlogbox.pack_start(self.newFileButton, True, True, 0)
        
        
        #OK, really finally, I promise.  Logging status stuff
        self.loggingFrame=gtk.Frame('Logging')
        self.loggingLabel=gtk.Label('False')
        self.loggingFrame.add(self.loggingLabel)
        self.statusbox.pack_start(self.loggingFrame, True, True, 0)
        self.timeLabel=gtk.Label('0')
        self.timeFrame=gtk.Frame('Run Duration')
        self.timeFrame.add(self.timeLabel)
        self.statusbox.pack_start(self.timeFrame, True, True, 0)
        
        
    def initializeLogger(self):
        """Sets up logging"""
        self.logger=logging.getLogger('data_logger' + str(self.filenumber))
        self.hdlr = logging.FileHandler(self.filename + '-' +str(self.filenumber) + '.txt')
        self.formatter = logging.Formatter('%(message)s')
        self.hdlr.setFormatter(self.formatter)
        self.logger.addHandler(self.hdlr)
        self.logger.setLevel(logging.WARNING)
        self.basetime=float(time.time())
        
    def scaleConnect(self, widget, data):
        if data=='1':
            self.scale1.connect(self.locations, self.rate)
            #print 'finished connection'
            #print self.scale1.connected
            if self.scale1.connected:
                #print 'succeeded connected if'
                self.locations.remove(self.scale1.address)
                self.scale1ConnectedLabel.set_text('True')
                if not self.monitorThread.started and not self.monitorThread.quit:
                    self.monitorThread.start()
                    self.monitorThread.started=True
                elif not self.monitorThread.started and self.monitorThread.quit:
                    self.monitorThread=gtkThread(self)
                    self.monitorThread.start()
                    
        elif data=='2':
            self.scale2.connect(self.locations, self.rate)
            if self.scale2.connected:
                #print 'succeeded connected if'
                self.locations.remove(self.scale2.address)
                self.scale2ConnectedLabel.set_text('True')    
                if not self.monitorThread.started and not self.monitorThread.quit:
                    self.monitorThread.start()
                    self.monitorThread.started=True
                elif not self.monitorThread.started and self.monitorThread.quit:
                    self.monitorThread=gtkThread(self)
                    self.monitorThread.start()
        
    def scaleDisconnect(self, widget, data):
        if data=='1':
            if self.scale1.connected:
                self.scale1.serial.close()
                self.locations.reverse()
                self.locations.append(self.scale1.address)
                self.locations.reverse()
                self.scale1.address=''
                self.scale1ConnectedLabel.set_text('False')
                self.scale1.connected=False
                self.scale1.weight='No Data'
        elif data=='2':
            if self.scale2.connected:
                self.scale2.serial.close()
                self.locations.reverse()
                self.locations.append(self.scale2.address)
                self.locations.reverse()
                self.scale2.address=''
                self.scale2ConnectedLabel.set_text('False')
                self.scale2.connected=False
                self.scale2.weight='No Data'
        if (not self.scale1.connected) and (not self.scale2.connected):
            self.monitorThread.quit=True
            self.monitorThread.started=False
                
    def toggle_event(self, widget, data):
        if data=='1':
            self.scale1.logging=widget.get_active()
        if data=='2':
            self.scale2.logging=widget.get_active()
    def delete_event(self, widget, data=None):
        for i in range(1,3):
            self.scaleDisconnect('', str(i))
        gtk.main_quit()
        
    def getDetailText(self, widget, data):
        self.details=self.detailEntry.get_text()
        if not self.details:
            self.details='No details were entered for this run.'
    
    def getSpeedText(self, widget, data):
        self.speed=self.speedEntry.get_text()
        if not self.speed:
            self.speed='No speed was entered for this run.'
        
    def getWidthText(self, widget, data):
        try:
            self.width=float(self.widthEntry.get_text())
        except:
            self.width=12.0
    
    def startLogging(self, widget, data):
        self.logger.setLevel(logging.INFO)
        self.getDetailText('','')
        self.getSpeedText('','')
        self.logger.info('Begin data segment')
        self.logger.info(str(datetime.datetime.now()))
        self.logger.info(self.details + ' ' + self.speed)
        self.basetime=float(time.time())
        self.logging=True
        self.loggingLabel.set_text("Logging")
    
    
    def stopLogging(self, widget, data):
        self.logger.info('End segment')
        self.logger.setLevel(logging.WARNING)
        self.logging=False
        self.loggingLabel.set_text("Not Logging")
    
    def newFile(self, widget, data):
        self.filenumber+=1
        self.initializeLogger()
        if self.logging==True:
            self.logger.setLevel(logging.INFO)



class gtkThread(threading.Thread):
    def __init__(self, gui):
        super(gtkThread, self).__init__()
        self.gui=gui
        #self.label=gui.weightLabel
        self.quit=False
        self.started=False
        
    def update_labels(self):
        if self.gui.logging:    
            self.gui.timeLabel.set_text(str(self.elapsed)[:4])
        self.gui.scale1WeightLabel.set_text(str(self.gui.scale1.weight))
        self.gui.scale2WeightLabel.set_text(str(self.gui.scale2.weight))
        return False   
    def sendCommand(self, port):
        port.flushInput()
        port.write('p' + '\r\n')
        
    def weightExtraction(self, port):
        weight=''
        buf=''
        for i in range(9):
            try:
                buf=port.readline()
            except:
                _=''
            #print str(i) + '  ' + buf
        for text in buf.split():
            try:
                #print buf
                weight=float(text)
                break
            except:
                _=''
        for i in range(4):
            buf=port.readline()
        return weight
        
    def run(self):
        scale1Weights=[]
        scale2Weights=[]
        while not self.quit:
            #Write print commands to currently logging scales
            if (self.gui.scale1.connected):
                self.sendCommand(self.gui.scale1.serial)
            if (self.gui.scale2.connected):
                self.sendCommand(self.gui.scale2.serial)
            time.sleep(.05)
            if (self.gui.scale1.connected):
                weight=self.weightExtraction(self.gui.scale1.serial)
                if not weight=='':
                    scale1Weights.append(weight)
            if (self.gui.scale2.connected):
                weight=self.weightExtraction(self.gui.scale2.serial)
                if not weight=='':
                    scale2Weights.append(weight)
            
            if(self.gui.scale1.connected and self.gui.scale2.connected):
                if ((len(scale1Weights)>4) and (len(scale2Weights)>4)):
                    self.elapsed=float(time.time())-self.gui.basetime
                    average1=0
                    average2=0
                    for num in scale1Weights:
                        average1=average1+float(num)
                    for num in scale2Weights:
                        average2=average2+float(num)
                        
                    average1=average1/len(scale1Weights)
                    average2=average2/len(scale2Weights)    
                    
                    self.gui.scale1.weight=str(average1)      
                    self.gui.scale2.weight=str(average2) 
                    
                    
                    scale1Weights=[]
                    scale2Weights=[]
                    if self.gui.logging:
                        if gui.scale1.logging and gui.scale2.logging:
                            self.gui.logger.info(str(self.elapsed)[:4] + ' ' + str(average1) + ' ' + str(average2))
                        elif gui.scale1.logging:
                            self.gui.logger.info(str(self.elapsed)[:4] + ' ' + str(average1) + ' Not_Logged')
                        elif self.gui.scale2.logging:
                            self.gui.logger.info(str(self.elapsed)[:4] + ' NotLogged ' + str(average2))
                    gobject.idle_add(self.update_labels)
            elif(self.gui.scale1.connected):
                if(len(scale1Weights)>4):
                    self.elapsed=float(time.time())-self.gui.basetime
                    average1=0
                    for num in scale1Weights:
                        #print scale1Weights
                        average1=average1+float(num)
                    average1=average1/len(scale1Weights)
                    self.gui.scale1.weight=str(average1)
                    scale1Weights=[]
                    scale2Weights=[]
                    if self.gui.logging:
                        if self.gui.scale1.logging:
                            self.gui.logger.info(str(self.elapsed)[:4] + ' ' + str(average1) + ' Not_Logged')
                    gobject.idle_add(self.update_labels)
            elif(self.gui.scale2.connected):
                if(len(scale2Weights)>4):
                    self.elapsed=float(time.time())-self.gui.basetime
                    average2=0
                    for num in scale2Weights:
                        average2=average2+float(num)
                    average2=average2/len(scale2Weights)
                    self.gui.scale2.weight=str(average2)
                    scale1Weights=[]
                    scale2Weights=[]
                    if self.gui.logging and self.gui.scale2.logging:
                        self.gui.logger.info(str(self.elapsed)[:4] + ' NotLogged ' + str(average2))
                    gobject.idle_add(self.update_labels)
                    print 'called update labels'
            #self.average=average
            
            
if __name__=='__main__':
    gui=guiFramework(LOCATIONS, RATE)
    gtk.main()