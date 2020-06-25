import spotipy
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import sys

from dotenv import load_dotenv
load_dotenv()

from PyQt5.QtWidgets import (QWidget, QSlider, QLineEdit, QLabel, QPushButton, QScrollArea, QApplication,
                             QHBoxLayout, QVBoxLayout, QGridLayout, QMainWindow, QLineEdit, QMessageBox, QSizePolicy, QFrame,
                             QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QInputDialog)
from PyQt5.QtCore import Qt, QSize, QEvent, pyqtSlot, QMimeData
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QIcon, QPixmap, QImage, QDrag, QFont

from PIL import Image
from PIL.ImageQt import ImageQt

from io import BytesIO
import requests

import json

import os

file = open("token.txt", "r")
client = file.readline()
secret = file.readline()

username = ''
scope = 'user-library-read playlist-modify-public playlist-read-collaborative playlist-read-private user-modify-playback-state user-read-playback-state'

token = util.prompt_for_user_token(username,
                                    scope,
                                    client_id = client[:-1],
                                    client_secret = secret[:-1],
                                    redirect_uri = 'http://127.0.0.1:8080'
                                   )

spotify = spotipy.Spotify(auth = token)

user_playlists = {}

def load_user_playlists(): #TO DO: MAKE SEPARATE FUNCTIONS FOR PLAYLISTS AND TRACKS PLEASE
    print("Loading playlists...")
    user_id = spotify.current_user()['id']
    results = spotify.user_playlists(user_id, limit = 50, offset = 0)
    increment = 0
    playlists = []
    tracks = []
    stop = False
    while True:
        for i in range(len(results['items'])):
            playlist = results['items'][i]
            playlist_name = playlist['name']
            playlist_description = playlist['description']
            playlist_id = playlist['id']
            playlist_art = playlist['images'][0]['url']
            playlist_info = (playlist_name, playlist_description, playlist_id, playlist_art)
            playlists.append(playlist_info)
        increment += 50
        results = spotify.user_playlists(user_id, limit = 50, offset = increment)
        if stop or len(results['items']) == 0:
            break
        elif len(results['items']) < 50:
            stop = True
    return playlists

user_playlists['playlists'] = load_user_playlists()
# print(user_playlists['playlists'])

def load_playlist_tracks():
    print("Loading playlist tracks...")
    playlist_tracks = {}
    for i in range(len(user_playlists['playlists'])):
        results = spotify.playlist_tracks(user_playlists['playlists'][i][2], limit = 50)
        increment = 0
        tracks = []
        stop = False
        while True:
            for j in range(len(results['items'])):
                track = results['items'][j]['track']
                track_name = track['name']
                track_id = track['id']
                track_info = (track_name, track_id)
                tracks.append(track_info)
            increment += 50
            results = spotify.playlist_tracks(user_playlists['playlists'][i][2], limit = 50, offset = increment)
            if stop or len(results['items']) == 0:
                playlist_tracks[user_playlists['playlists'][i][2]] = tracks
                break
            elif len(results['items']) < 50:
                stop = True
    return playlist_tracks

user_playlists['tracks'] = load_playlist_tracks()

def load_images():
    print("Loading images...")
    images = []
    for i in range(len(user_playlists['playlists'])):
        response = requests.get(user_playlists['playlists'][i][3])
        img = Image.open(BytesIO(response.content))
        img = img.convert("RGBA")
        basewidth = 250
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), Image.ANTIALIAS)
        images.append(img)
#        if i % 5 == 0:
        sys.stdout.flush()
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write(str(i+1) + "/" + str(len(user_playlists['playlists'])) + " images loaded")
    print("\nImages loaded\n")
    print("Launching program...")
    return images

user_playlists['images'] = load_images()
#print(user_playlists['images'])

#user_playlists CONTENTS: {'playlists': list of tuples containing playlist info, 'tracks': dictionary of lists of tuples containing track name and id, 'images': image files of playlist art}

save_data = {'folders': []}

def updateJSON():
    with open("data.json", "w") as outfile:
        json.dump(save_data, outfile)
def readJSON():
    with open("data.json") as json_file:
        try:
            data = json.load(json_file)
        except:
            return "empty"
        return data

class TreeWidget(QTreeWidget):
    def __init__(self):
        super(TreeWidget, self).__init__()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        e.accept()

    def dragMoveEvent(self, e):
#        e.setDropAction(Qt.MoveAction)
        e.accept()

    def mouseMoveEvent(self, e):
#        super(TreeWidget, self).mouseMoveEvent(e)
        mime_data = QMimeData()
        if self.itemAt(e.pos()) == None:
            return
        elif self.itemAt(e.pos()).parent() == None:
            return
        else:
            mime_data.setText(self.itemAt(e.pos()).text(0))
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.MoveAction)

    def dropEvent(self, e):
        # if e.source() == self:
        #     ev.setDropAction(QtCore.Qt.MoveAction)
        #     super().dropEvent(e)
        # elif isinstance(e.source(), ListWidget):
        item = self.itemAt(e.pos())
        if item == None:
            return
        if e.source() == self:
            if item.parent() == None:
                for i in range(item.childCount()):
                    if e.mimeData().text() == item.child(i).text(0):
                        return
            else:
                for i in range(item.parent().childCount()):
                    if e.mimeData().text() == item.parent().child(i).text(0):
                        return

        topLevelItems = []
        for i in range(self.topLevelItemCount()):
            topLevelItems.append(self.topLevelItem(i))
        if item in topLevelItems:
            if item.childCount() > 0:
                for i in range(item.childCount()):
                    if e.mimeData().text() == item.child(i).text(0):
                        return
            child = QTreeWidgetItem(item)
        else:
            for i in range(item.parent().childCount()):
                if e.mimeData().text() == item.parent().child(i).text(0):
                    return
            child = QTreeWidgetItem(item.parent())
        child.setText(0, e.mimeData().text())
        for i in range(len(save_data['folders'])):
            if child.text(0) == "":
                break
            folder_name = save_data['folders'][i][0]
            if child.parent().text(0) == folder_name:
                save_data['folders'][i].append(child.text(0)) #Add child to save data
                break
        updateJSON()

class ListWidget(QListWidget):
    def __init__(self):
        super(ListWidget, self).__init__()
        self.setDragEnabled(True)

    def mouseMoveEvent(self, e):
        super(ListWidget, self).mouseMoveEvent(e)
        mime_data = QMimeData()
        if self.itemAt(e.pos()) == None:
            return
        else:
            mime_data.setText(self.itemAt(e.pos()).text())
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)

helper = {'widgets': []}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.widget = QWidget()
        self.grid = QGridLayout()

        self.widget.setLayout(self.grid)

        self.setCentralWidget(self.widget)
        self.manageWidgets()

    def manageWidgets(self):
        global save_data

        self.playlists = ListWidget()
        self.folders = TreeWidget()

        self.playlists.setMaximumWidth(425)
        self.folders.setMaximumWidth(425)

        self.folders.setHeaderLabels(["Drag playlists from above into the folders"])
        self.folders.setStyleSheet("")

        self.playlists.setSpacing(5)
        self.playlists.setDragEnabled(True)

        playlists = []
        for i in range(len(user_playlists['playlists'])): #Show user playlists
            item = QListWidgetItem(user_playlists['playlists'][i][0], self.playlists)
            item.setTextAlignment(Qt.AlignCenter)
            self.playlists.addItem(item)
            playlists.append(item)

        #Load saved data
        data = readJSON()
        if data != "empty":
            for i in range(len(data['folders'])):
                folder = QTreeWidgetItem(self.folders)
                folder.setText(0, data['folders'][i][0])
                self.folders.addTopLevelItem(folder)
                for j in range(1, len(data['folders'][i])):
                    playlist = QTreeWidgetItem(folder)
                    playlist.setText(0, data['folders'][i][j])
            save_data = data

        self.playlists.itemClicked.connect(self.make_display_playlist_info(0))

        self.folders.itemDoubleClicked.connect(self.make_display_playlist_info(1))

        playlists_header = QLabel("My Playlists:")
        folders_header = QLabel("My Folders:")

        add_folder = QPushButton("New Folder")
        delete_folder = QPushButton("Remove Item")
        rename_folder = QPushButton("Rename Folder")

        add_folder.clicked.connect(self.addFolder)
        delete_folder.clicked.connect(self.removeItem)
        rename_folder.clicked.connect(self.renameFolder)

        self.hbox = QHBoxLayout()

        self.grid.addWidget(playlists_header, 1, 1)
        self.grid.addWidget(self.playlists, 2, 1)
        self.grid.addWidget(folders_header, 3, 1)
        self.grid.addWidget(self.folders, 4, 1)
    #    self.grid.addWidget(add_folder, 5, 1, alignment = Qt.AlignCenter)
        self.grid.addLayout(self.hbox, 5, 1)
        self.hbox.addWidget(add_folder)
        self.hbox.addWidget(delete_folder)
        self.hbox.addWidget(rename_folder)

        # edit = QLineEdit('', self)
        # edit.setDragEnabled(True)
        # edit.move(30, 65)
        #
        # button = Button("Button", self)
        # button.move(190, 65)

        self.setWindowTitle('Spotify Playlist Folders')
        self.setGeometry(90, 50, 1100, 800)

    def removeWidgets(self, widgets):
        for i in range(len(widgets)):
            widgets[i].setParent(None)

    def make_display_playlist_info(self, num):
        def display_playlist_info():
            if num == 1:
                for i in range(self.folders.topLevelItemCount()):
                    if self.folders.currentItem() == self.folders.topLevelItem(i):
                        return
            ix = -1
            if num == 0:
                ix = self.playlists.currentRow()
            elif num == 1:
                name = self.folders.currentItem().text(0)
                for i in range(len(user_playlists['playlists'])):
                    playlist = user_playlists['playlists'][i]
                    if name == playlist[0]:
                        ix = i
                        break
            if ix == -1:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.setText("This playlist was deleted from your account or is otherwise inaccessible.")
                msgBox.exec_()
                return
            widgets = helper['widgets']
            if len(widgets) > 0:
                self.removeWidgets(widgets)
            widgets = []

            playlist = user_playlists['playlists'][ix]
            image = user_playlists['images'][ix]
            title = QLabel(playlist[0])
            title.setFont(QFont('Arial', 24))
            self.desc_text = ""
            for i in range(len(list(playlist[1]))):
                self.desc_text += list(playlist[1])[i]
                if i > 0 and i % 45 == 0:
                    self.desc_text += "\n"
            if len(self.desc_text) < 70:
                desc = QLabel(self.desc_text)
            else:
                desc = QLabel(self.desc_text[:70] + "...")
                desc.installEventFilter(self)
            desc.setAlignment(Qt.AlignCenter)
            desc.setFont(QFont('Arial', 12))
            img = QLabel(self)
            q_img = ImageQt(image)
            pixmap = QPixmap.fromImage(q_img)
            img.setPixmap(pixmap)
            play = QPushButton("►   Play Playlist")
            play.clicked.connect(self.make_play_playlist(playlist))

            self.tracks = QListWidget()
            self.tracks.setMaximumWidth(425)
            self.tracks.setSpacing(5)

            self.grid.addWidget(title, 0, 0, alignment = Qt.AlignCenter)
            self.grid.addWidget(desc, 1, 0, alignment = Qt.AlignCenter)
            self.grid.addWidget(img, 2, 0, alignment = Qt.AlignCenter)
            self.grid.addWidget(play, 3, 0, alignment = Qt.AlignCenter)
            self.grid.addWidget(self.tracks, 4, 0)

            for i in range(len(user_playlists['tracks'][playlist[2]])):
                track = user_playlists['tracks'][playlist[2]][i]
                track_name = "►  " + track[0]
                track_id = track[1]
                item = QListWidgetItem(track_name, self.tracks)
                self.tracks.addItem(item)

            self.tracks.itemDoubleClicked.connect(self.make_play_from_playlist(playlist))

            helper['widgets'].append(title)
            helper['widgets'].append(desc)
            helper['widgets'].append(img)
            helper['widgets'].append(play)
        return display_playlist_info

    def eventFilter(self, source, e):
        if e.type() == QEvent.Enter:
            source.setText(self.desc_text)
        elif e.type() == QEvent.Leave:
            source.setText(self.desc_text[:70] + "...")
        return False

    @pyqtSlot()
    def make_play_playlist(self, playlist):
        def play_playlist():
            id = playlist[2]
            spotify.start_playback(spotify.devices()['devices'][0]['id'], "spotify:playlist:" + id)
        return play_playlist

    @pyqtSlot()
    def make_play_from_playlist(self, playlist):
        def play_from_playlist():
            track_num = self.tracks.currentRow()
            id = playlist[2]
            spotify.start_playback(spotify.devices()['devices'][0]['id'], "spotify:playlist:" + id, offset = {"position": track_num})
        return play_from_playlist

    def checkDuplicate(self, name):
        for i in range(self.folders.topLevelItemCount()):
            if name == self.folders.topLevelItem(i).text(0):
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.setText("Folder \'" + name + "\' already exists!")
                msgBox.exec_()
                return True
        return False

    @pyqtSlot()
    def addFolder(self):
        text, ok = QInputDialog.getText(self, "Add Folder", "Name of new folder:")
        if ok:
            folder_name = str(text)
            if self.checkDuplicate(folder_name):
                return
            new_folder = QTreeWidgetItem(self.folders)
            self.folders.addTopLevelItem(new_folder)
            new_folder.setText(0, folder_name)
            new_folder.setExpanded(True)
            save_data['folders'].append([new_folder.text(0)])
            updateJSON()


    @pyqtSlot()
    def removeItem(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setText("Please select a folder or playlist to remove.")
        if len(self.folders.selectedItems()) != 1:
            msgBox.exec_()
        else:
            item = self.folders.selectedItems()[0]
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("Are you sure you want to remove \'" + item.text(0) + "\'?")
            msgBox.setInformativeText("This action cannot be undone.")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

            isTopLevel = False
            for i in range(self.folders.topLevelItemCount()):
                if item == self.folders.topLevelItem(i):
                    isTopLevel = True
                    break
            if not isTopLevel:
                msgBox.setText("Are you sure you want to remove \'" + item.text(0) + "\' from \'" + item.parent().text(0) + "\'?")
                retval = msgBox.exec_()
                if retval == 1024:
                    for i in range(len(save_data['folders'])):
                        folder_name = save_data['folders'][i][0]
                        if item.parent().text(0) == folder_name:
                            save_data['folders'][i].remove(item.text(0))
                            break
                    item.parent().takeChild(item.parent().indexOfChild(item))
                    updateJSON()
                elif retval == 4194304:
                    return
            else:
                retval = msgBox.exec_()
                if retval == 1024: #Pressed OK
                    item.takeChildren()
                    self.folders.takeTopLevelItem(self.folders.indexOfTopLevelItem(item))
                    for i in range(len(save_data['folders'])):
                        folder_name = save_data['folders'][i][0]
                        if item.text(0) == folder_name:
                            save_data['folders'].pop(i)
                            break
                    updateJSON()
                elif retval == 4194304:
                    return
    @pyqtSlot()
    def renameFolder(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setText("Please select a folder to rename.")
        if len(self.folders.selectedItems()) != 1:
            msgBox.exec_()
        else:
            folder = self.folders.selectedItems()[0]
            oldName = folder.text(0)
            isTopLevel = False
            for i in range(self.folders.topLevelItemCount()):
                if folder == self.folders.topLevelItem(i):
                    isTopLevel = True
                    break
            if not isTopLevel:
                msgBox.setText("Please select a folder to rename.")
                msgBox.exec_()
                return
            else:
                text, ok = QInputDialog.getText(self, "Rename Folder", "New name for folder:")
                if ok:
                    name = str(text)
                    for i in range(len(save_data['folders'])):
                        folder_name = save_data['folders'][i][0]
                        msgBox.setText("Folder with that name already exists!")
                        if name == folder_name:
                            msgBox.exec_()
                            return
                        if oldName == folder_name:
                            for j in range(i, len(save_data['folders'])):
                                check_duplicate_folder_name = save_data['folders'][j][0]
                                if name == check_duplicate_folder_name:
                                    msgBox.exec_()
                                    return
                            save_data['folders'][i][0] = name
                            break
                    folder.setText(0, name)
                    updateJSON()
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
app = QtWidgets.QApplication(sys.argv)
mainWin = MainWindow()
mainWin.show()
sys.exit(app.exec_())
