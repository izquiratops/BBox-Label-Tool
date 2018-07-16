#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
#-------------------------------------------------------------------------------
from __future__ import division
from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("Yet Another Label Tool :)")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.entry.insert(0,'001')
        self.ldBtn = Button(self.frame, text = "Load", width = 10, command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.mainPanel.grid(row = 1, column = 1, rowspan = 6, sticky = W+N)
        self.parent.bind("<Escape>", self.cancelBBox)
        self.parent.bind("<Control-d>", self.nextImage)
        self.parent.bind("<Control-a>", self.prevImage)
        self.parent.bind("<Control-s>", self.saveImage)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes')
        self.lb1.grid(row = 1, column = 2)
        self.listbox = Listbox(self.frame, width = 40, height = 12)
        self.listbox.grid(row = 2, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', width = 10, command = self.delBBox)
        self.btnDel.grid(row = 3, column = 2, padx = 45, pady = 3, sticky = W)
        self.btnClear = Button(self.frame, text = 'Clear All', width = 10, command = self.clearBBox)
        self.btnClear.grid(row = 3, column = 2, padx = 45, pady = 3, sticky = E)
        self.itemLabel = Label(self.frame, text = "Item")
        self.itemLabel.grid(row = 4, column = 2, sticky = N)
        self.itembox = Listbox(self.frame, width = 40, height = 12)
        self.itembox.grid(row = 4, column = 2, padx = 10, sticky = N+S)
        self.itembox.bind('<<ListboxSelect>>', self.itemselected)
        self.itemEntry = Entry(self.frame)
        self.itemEntry.grid(row = 5, column = 2, padx = 10, sticky = W+E+N)
        self.itemEntry.insert(0,'cat')

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 7, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev (CTRL-D)', width = 15, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next (CTRL-A) >>', width = 15, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel)
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'

        # get image list
        self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        if len(self.imageList) == 0:
            print 'No .jpg images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        self.outDir = os.path.join(r'./Images', '%03d' %(self.category))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        # load predefined_classes from labels used before
        if os.path.exists('./Images/predefined_classes.txt'):
            with open('./Images/predefined_classes.txt') as f:
                self.itembox.delete(0,'end')
                print 'predefined_classes load: '
                for line in f:
                    print line.split()[0]
                    self.itembox.insert(END,line.split()[0])

        self.loadImage()
        print '%d images loaded from %s' %(self.total, s)

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.tmpLabel.config(text=imagepath)
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                print 'Labels from: ' + labelname
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    tmp = [t.strip() for t in line.split()]
                    print tmp
                    self.bboxList.append(tuple(tmp))
                    tmpId = self.mainPanel.create_rectangle(tmp[0], tmp[1], \
                                                            tmp[2], tmp[3], \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '(%d, %d) -> (%d, %d) : %s' %(int(tmp[0]), int(tmp[1]), int(tmp[2]), int(tmp[3]), tmp[4]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
                    # Add item to history log
                    if tmp[4] not in self.itembox.get(0, END):
                        print tmp[4]
                        self.itembox.insert(END, tmp[4])

    def saveImage(self):
        file = os.path.splitext(self.labelfilename)[0]
        im = Image.open(file + '.jpg')
        width, height = im.size

        # Save XML
        with open(file + '.xml', 'a') as exported:
            exported.truncate(0)
            exported.write('<?xml version="1.0" encoding="utf-8"?>\n')
            exported.write('<annotation>\n')
            for bbox in self.bboxList:
                exported.write('\t<object>\n')
                exported.write('\t\t<name>' + bbox[4] + '</name>\n')
                exported.write('\t\t<bndbox>\n')
                exported.write('\t\t\t<xmin>' + str(bbox[0]) + '</xmin>\n')
                exported.write('\t\t\t<ymin>' + str(bbox[1]) + '</ymin>\n')
                exported.write('\t\t\t<xmax>' + str(bbox[2]) + '</xmax>\n')
                exported.write('\t\t\t<ymax>' + str(bbox[3]) + '</ymax>\n')
                exported.write('\t\t</bndbox>\n')
                exported.write('\t</object>\n')
            exported.write('\t<folder>Annotations</folder>\n')
            exported.write('\t<filename>' + str(os.path.basename(file)) + '.jpg' + '</filename>\n')
            exported.write('\t<size>\n')
            exported.write('\t\t<width>' + str(width) + '</width>\n')
            exported.write('\t\t<height>' + str(height) + '</height>\n')
            exported.write('\t\t<depth>3</depth>\n')
            exported.write('\t</size>\n')
            exported.write('</annotation>\n')

        # Save TXT
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')

        # Save Labels TXT
        with open('./Images/predefined_classes.txt', 'w') as f:
            for actual_item in self.itembox.get(0, END):
                f.write(''.join(map(str, actual_item)) + '\n')

        print 'Image No. %d saved' %(self.cur)

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            actual_item = self.itemEntry.get()
            self.bboxList.append((x1, y1, x2, y2, actual_item))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d) : %s' %(x1, y1, x2, y2, self.itemEntry.get()))
            print 'ACTUAL ITEM HIST LIST: ' + str(self.itembox.get(0, END))
            if actual_item not in self.itembox.get(0, END):
                self.itembox.insert(END, actual_item)
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def itemselected(self, event):
        index = int(self.itembox.curselection()[0])
        value = self.itembox.get(index)
        self.itemEntry.delete(0, "end")
        self.itemEntry.insert(0,value)
        print 'You selected item %d: "%s"' % (index, value)

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width = True, height = True)
    root.mainloop()
