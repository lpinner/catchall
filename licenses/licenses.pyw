# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------------------
# Name:        licenses
# Purpose:
#
# Author:      Luke
#
# Created:     21/05/2014
# Copyright:   (c) 2014
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import os,sys,re,subprocess,json
from collections import OrderedDict
from datetime import datetime

#PyQt4/PySide compat
try:
    from PyQt4 import QtCore, QtGui, uic
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    def uiloader(uifile, instance):
        return uic.loadUi(uifile, instance)
except:
    from PySide import QtCore, QtGui, QtUiTools
    def uiloader(uifile, instance):
        return QtUiTools.QUiLoader().load(uifile, instance)

try:import licenses_qrc
except:pass

class SettingsDialog(QtGui.QDialog):
    def __init__(self, parent=None, defaults={}):
        QtGui.QDialog.__init__(self, parent)
        self.ui = uiloader(os.path.join(os.path.dirname(__file__),'settings.ui'), self)
        self.defaults=defaults
        self.cache=[]

    def get_values(self):
        retval={}

        tbl=self.ui.tblManagers
        retlist=[]
        for i in range(tbl.rowCount()):
            server=tbl.item(i,0).text()
            port=tbl.item(i,1).text()
            name=tbl.item(i,2).text()
            retlist.append([str(server),int(port),str(name)])
        retval['managers']=retlist

        tbl=self.ui.tblLookup
        retlist=[]
        for i in range(tbl.rowCount()):
            feature=tbl.item(i,0).text()
            name=tbl.item(i,1).text()
            retlist.append([str(feature),str(name)])
        retval['lookup']=retlist

        tbl=self.ui.tblBlacklist
        retlist=[]
        for i in range(tbl.rowCount()):
            feature=tbl.item(i,0).text()
            retlist.append(str(feature))
        retval['blacklist']=retlist
        return retval

    def set_values(self,values):

        vals=values['managers']
        tbl=self.ui.tblManagers
        tbl.setRowCount(0)
        tbl.setRowCount(len(vals))

        for i,(server,port,name) in enumerate(vals):
            tbl.setItem(i, 0, QtGui.QTableWidgetItem(server))
            tbl.setItem(i, 1, QtGui.QTableWidgetItem(str(port)))
            tbl.setItem(i, 2, QtGui.QTableWidgetItem(name))

        vals=values['lookup'].items()
        tbl=self.ui.tblLookup
        tbl.setRowCount(0)
        tbl.setRowCount(len(vals))

        for i,(feature,name) in enumerate(vals):
            tbl.setItem(i, 0, QtGui.QTableWidgetItem(feature))
            tbl.setItem(i, 1, QtGui.QTableWidgetItem(name))

        vals=values['blacklist']
        tbl=self.ui.tblBlacklist
        tbl.setRowCount(0)
        tbl.setRowCount(len(vals))

        for i,feature in enumerate(vals):
            tbl.setItem(i, 0, QtGui.QTableWidgetItem(feature))

    def on_btnManagersAdd_clicked(self,checked=None):
        self._add_(self.ui.tblManagers,checked)

    def on_btnManagersDel_clicked(self,checked=None):
        self._del_(self.ui.tblManagers,checked)

    def on_btnLookupAdd_clicked(self,checked=None):
        self._add_(self.ui.tblLookup,checked)

    def on_btnLookupDel_clicked(self,checked=None):
        self._del_(self.ui.tblLookup,checked)

    def on_btnBlacklistAdd_clicked(self,checked=None):
        self._add_(self.ui.tblBlacklist,checked)

    def on_btnBlacklistDel_clicked(self,checked=None):
        self._del_(self.ui.tblBlacklist,checked)

    def _add_(self,tbl,checked=None):
        if checked is None: return
        tbl.setRowCount(tbl.rowCount()+1)

    def _del_(self,tbl,checked=None):
        if checked is None: return
        for i in range(tbl.rowCount()-1,-1,-1): #Go backwards thru rows
            item=tbl.item(i,0)
            if tbl.isItemSelected(item):
                tbl.removeRow(i)


    def on_buttonBox_clicked(self,button):
        bbox=self.ui.buttonBox
        if bbox.buttonRole(button)!=bbox.ResetRole:return

        if self.ui.tabWidget.currentIndex() == 0:
            defaults=self.defaults['managers']
            tbl=self.ui.tblManagers
            tbl.setRowCount(0)
            tbl.setRowCount(len(defaults))

            for i,(server,port,name) in enumerate(defaults):
                tbl.setItem(i, 0, QtGui.QTableWidgetItem(server))
                tbl.setItem(i, 1, QtGui.QTableWidgetItem(str(port)))
                tbl.setItem(i, 2, QtGui.QTableWidgetItem(name))

        elif self.ui.tabWidget.currentIndex() == 1:
            defaults=self.defaults['lookup'].items()
            tbl=self.ui.tblLookup
            tbl.setRowCount(0)
            tbl.setRowCount(len(defaults))

            for i,(feature,name) in enumerate(defaults):
                tbl.setItem(i, 0, QtGui.QTableWidgetItem(feature))
                tbl.setItem(i, 1, QtGui.QTableWidgetItem(name))

        elif self.ui.tabWidget.currentIndex() == 2:
            defaults=self.defaults['blacklist']
            tbl=self.ui.tblBlacklist
            tbl.setRowCount(0)
            tbl.setRowCount(len(defaults))

            for i,feature in enumerate(defaults):
                tbl.setItem(i, 0, QtGui.QTableWidgetItem(feature))

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.userinfo=UserInfo()
        self.username=self.userinfo.username

        self.loading=False
        self.selected=None

        self.init_settings()
        self.init_ui()

        #Give QT enough time to set up widgets, otherwise geometry is off
        QtCore.QTimer.singleShot(10, self.loadLicenseInfo)

    def init_settings(self):

        #Default settings
        default_settings=QtCore.QSettings( __file__.replace('.pyw','.ini'),
                                           QtCore.QSettings.IniFormat)
        #default_settings.setSystemIniPath (os.path.dirname(__file__))
        #default_settings.setPath (default_settings.IniFormat,
        #                          os.path.dirname(__file__),
        #                          default_settings.SystemScope)

        try: #pyqt4
            default_managers=json.loads(str(default_settings.value('managers').toPyObject()))
        except AttributeError: #pyside
            default_managers=json.loads(str(default_settings.value('managers')))
        except:default_managers=('',0,'')
        #Lookup for feature names
        try: #pyqt4
            default_lookup=OrderedDict(json.loads(str(default_settings.value('lookup').toPyObject())))
        except AttributeError: #pyside
            default_lookup=OrderedDict(json.loads(str(default_settings.value('lookup'))))
        except:default_lookup={}
        #Blacklist for hiding for features
        try: #pyqt4
            default_blacklist=json.loads(str(default_settings.value('blacklist').toPyObject()))
        except AttributeError: #pyside
            default_blacklist=json.loads(str(default_settings.value('blacklist')))
        except:default_blacklist=[]

        #User settings
        self.settings=QtCore.QSettings( QtCore.QSettings.IniFormat,
                                        QtCore.QSettings.UserScope,
                                        "License Checker")

        self.dlgSettings = SettingsDialog(self, {'managers':default_managers,
                                                 'lookup':default_lookup,
                                                 'blacklist':default_blacklist})

        try:self.managers=json.loads(str(self.settings.value('managers').toPyObject()))
        except:self.managers=default_managers
        try:self.lookup=OrderedDict(json.loads(str(self.settings.value('lookup').toPyObject())))
        except:self.lookup=default_lookup
        try:self.blacklist=json.loads(str(self.settings.value('blacklist').toPyObject()))
        except:self.blacklist=default_blacklist

    def init_ui(self):
        #self.ui = uic.loadUi(__file__.replace('.pyw','.ui'), self)
        self.ui = uiloader(__file__.replace('.pyw','.ui'), self)

        self.gif = QtGui.QMovie(':/resources/images/loading.gif', QtCore.QByteArray(), self)
        self.ui.loadingLabel=QtGui.QLabel(self)
        self.ui.loadingLabel.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.ui.loadingLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.loadingLabel.setMovie(self.gif)
        self.gif.start();self.gif.stop() #required to populate frameRect
        rect=self.gif.frameRect()
        self.ui.loadingLabel.resize(rect.width(), rect.height())

        self.ui.treeWidget.resizeEvent=self.override_resizeEvent(self.ui.treeWidget)

    def loadLicenseInfo(self):
        if self.loading:return
        self.showLoading()
        self.ui.treeWidget.clear()
        self.ui.userTableWidget.setRowCount(0)
        self.Thread = QtCore.QThread()
        self.LicenseInfo=LicenseInfo(self.managers)
        self.LicenseInfo.moveToThread(self.Thread)
        self.LicenseInfo.finished.connect(self.onLicenseInfoFinished)
        self.LicenseInfo.featureinfo.connect(self.onLicenseInfoFeatures)
        self.Thread.started.connect(self.LicenseInfo.get)
        self.Thread.start()

    def showLoading(self):
        self.loading=True
        self.ui.loadingLabel.move(self.ui.userTableWidget.geometry().center())
        self.gif.start()
        self.ui.loadingLabel.show()
        self.ui.actionRefresh.setEnabled(False)
        self.ui.actionSettings.setEnabled(False)

    def hideLoading(self):
        self.Thread.terminate()
        self.ui.loadingLabel.hide()
        self.gif.stop()
        self.ui.actionRefresh.setEnabled(True)
        self.ui.actionSettings.setEnabled(True)
        self.loading=False

    def onLicenseInfoFinished(self):
        self.hideLoading()
        self.ui.treeWidget.resizeColumnToContents(0)

    def onLicenseInfoFeatures(self,manager,featureinfo):

        item=QtGui.QTreeWidgetItem(self.ui.treeWidget)
        item.setText(0,manager)

        self.ui.treeWidget.addTopLevelItem(item)
        featureinfo=dict([(self.lookup.get(f,f),i)
                           for f,i in featureinfo.items()
                           if f not in self.blacklist])

        for feature,info in sorted(featureinfo.items()):
            feature = self.lookup.get(feature,feature)
            child=QtGui.QTreeWidgetItem(item)
            child.setText(0,feature)
            child.setText(1,info['available'].rjust(2))
            child.setText(2,info['issued'].rjust(2))
            child.setText(3,info['inuse'].rjust(2))
            child.setData(0,QtCore.Qt.UserRole,(manager,feature,info,)) #wrap dict in tuple so it doesn't get converted to QT C++ type
            child.setTextAlignment(1, QtCore.Qt.AlignHCenter)
            child.setTextAlignment(2, QtCore.Qt.AlignHCenter)
            child.setTextAlignment(3, QtCore.Qt.AlignHCenter)

    #Autoconnected event handlers
    def on_actionExit_triggered(self,checked=None):
        if checked is None: return
        QtGui.qApp.quit()

    def on_actionMailto_triggered(self,checked=None):
        if checked is None: return

        from urllib import quote
        import webbrowser
        for item in self.ui.treeWidget.selectedItems():
            data = item.data(0,QtCore.Qt.UserRole).toPyObject()
            manager = data[0]
            feature = data[1]
            info = data[2]
            userids=[u[0] for u in info['users']]
            webbrowser.open_new('mailto:%s?subject=%s %s licence?'%(';'.join(userids),manager,feature))
            break

    def on_actionRefresh_triggered(self,checked=None):
        if checked is None: return
        self.loadLicenseInfo()

    def on_actionSettings_triggered(self,checked=None):
        if checked is None: return

        dlg = self.dlgSettings
        dlg.set_values({'managers':self.managers,
                        'lookup':OrderedDict(self.lookup),
                        'blacklist':self.blacklist})

        if dlg.exec_():
            values = dlg.get_values()
            self.managers = values['managers']
            self.lookup = OrderedDict(values['lookup'])
            self.blacklist = values['blacklist']
            self.settings.setValue('managers',json.dumps(self.managers))
            self.settings.setValue('lookup',json.dumps(self.lookup))
            self.settings.setValue('blacklist',json.dumps(self.blacklist))

    def on_treeWidget_currentItemChanged(self, item, *args,**kwargs):
        if item is None:return

        if item.childCount() > 0: #Top level
            item.setExpanded (not item.isExpanded())
        else:#Child
            data = item.data(0,QtCore.Qt.UserRole).toPyObject()
            manager = data[0]
            feature = data[1]
            info = data[2]
            self.ui.userTableWidget.setRowCount(len(info['users']))

            now = datetime.now()
            year=now.year

            for i,user in enumerate(info['users']):
                #[userid,computer,startdate]
                username=self.username(user[0])
                self.userTableWidget.setItem(i, 0, QtGui.QTableWidgetItem(username))
                self.userTableWidget.setItem(i, 1, QtGui.QTableWidgetItem(user[0].upper()))
                self.userTableWidget.setItem(i, 2, QtGui.QTableWidgetItem(user[1]))
                dt=datetime.strptime(user[2],'%a %m/%d %H:%M')
                dt=dt.replace(year=year)   #defaults to 1900, set it to current year
                if (now - dt).days < 0: #Was it last year instead?
                    dt=dt.replace(year=year-1)
                self.userTableWidget.setItem(i, 3, DateTableWidgetItem(dt, '%a %d/%m %H:%M'))

            self.ui.userTableWidget.resizeColumnToContents(2)
            self.ui.userTableWidget.resizeColumnToContents(1)
            self.ui.userTableWidget.resizeColumnToContents(0)

            if int(info['available'])==0:
                self.ui.actionMailto.setEnabled(True)
            else:
                self.ui.actionMailto.setEnabled(False)

    def on_treeWidget_itemExpanded(self,item,*args,**kwargs):
        self.ui.userTableWidget.setRowCount(0)
        self.ui.treeWidget.resizeColumnToContents(0)

    def on_treeWidget_itemCollapsed(self,item,*args,**kwargs):
        for item in self.ui.treeWidget.selectedItems():
            item.setSelected(False)
        self.ui.userTableWidget.setRowCount(0)

    def override_resizeEvent(self,widget):
        def func(event):
            width = event.size().width()

            fixed=55
            fixcols=range(1,4)
            stretch=width - 3*fixed

            widget.setColumnWidth(0, stretch)
            for i in fixcols:widget.setColumnWidth(i, fixed)
        return func

class DateTableWidgetItem(QtGui.QTableWidgetItem):
    '''Convert string to date so we can sort'''
    def __init__(self, date_time, fmt=QtCore.Qt.TextDate):
        if isinstance(date_time, datetime):
            self.datetime=date_time
            date_time=date_time.strftime(fmt)
        else:
            self.datetime=datetime.strptime(date_time,fmt)

        QtGui.QTableWidgetItem.__init__(self,date_time)

    def __lt__(self, other):
        try:
            return self.datetime < other.datetime
        except:
            return QtGui.QTableWidgetItem.__lt__(self,other)

class LicenseInfo(QtCore.QObject):

    finished = QtCore.Signal()
    featureinfo = QtCore.Signal(str,dict)

    def __init__(self,managers):
        QtCore.QObject.__init__(self)

        self.managers=managers

        self.featpat = re.compile(
            (r'Users of (?P<feature>.*):.*'
             r'Total of (?P<issued>\d+) license[s]* issued.*'
             r'Total of (?P<inuse>\d+) license[s]* in use.*$'), re.IGNORECASE)
        self.userpat = re.compile(
            (r'^(?P<userid>\S+)\s(?P<computer>\S+)\s.*'
             r'start (?P<date>.*)$'), re.IGNORECASE)

    #@QtCore.Slot()
    def get(self):
        cmd=['lmutil','lmstat','-a','-c']
        for server,port, manager in self.managers:
            exit_code, stdout, stderr = runcmd(cmd+['%s@%s'%(port,server)])
            stdout=stdout[stdout.find('Users of'):]
            featureinfo = OrderedDict()
            for line in stdout.splitlines():
                line=line.strip()
                if line.startswith('Users of'):
                    r = self.featpat.search(line)
                    if r:
                        d = r.groupdict()
                        issued=d['issued']
                        inuse = d['inuse']
                        available = str(int(issued) - int(inuse))
                        feature=d['feature']
                        featureinfo[feature]={'issued':issued,
                                           'inuse':inuse,
                                           'available':available,
                                           'users':[]
                                           }
                elif line:
                    r = self.userpat.search(line)
                    if r:
                        d = r.groupdict()
                        userid=d['userid']
                        computer = d['computer']
                        startdate=d['date']
                        featureinfo[feature]['users'].append([userid,computer,startdate])

            self.featureinfo.emit(manager,featureinfo)

        self.finished.emit()

class UserInfo(object):
    def __init__(self):
        if os.name=='nt':
            try:
                import win32com.client #raises an error if pythonwin not installed...
                objADSystemInfo = win32com.client.Dispatch("ADSystemInfo")
                objADSPathname= win32com.client.Dispatch("Pathname")
                ADS_SETTYPE_FULL       = 1
                ADS_FORMAT_X500_PARENT = 8
                pathname='LDAP://'+objADSystemInfo.UserName
                objADSPathname.Set(pathname,ADS_SETTYPE_FULL)
                self._parent=objADSPathname.Retrieve(8)
                self.username=self._winusername
            except:
                self.username=self._nousername
        else:
            self.username=self._nixusername

    def _nousername(self,*args):
        return 'Pythonwin is not installed!'

    def _winusername(self,user):
        import win32com.client #raises an error if pythonwin not installed...
        try:
            pathname='LDAP://CN=%s,%s'%(user,self._parent)
            username = win32com.client.GetObject(pathname).displayName
        except:return ''
        return username

    def _nixusername(self,user):
        import pwd
        for u in (user,user.upper(), user.lower()):
	    try:return pwd.getpwnam(u).pw_gecos
            except KeyError:continue
        return ''

def runcmd(cmd):
    if os.name=='nt':
        startupinfo=subprocess.STARTUPINFO()#Windows starts up a console when a subprocess is run from a non-console
        startupinfo.dwFlags |= 1            #app like pythonw unless we pass it a flag that says not to...
    else:startupinfo=None
    proc=subprocess.Popen(cmd, startupinfo=startupinfo,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          stdin=subprocess.PIPE)
    if os.name=='nt':proc.stdin.close()
    stdout,stderr=proc.communicate()
    exit_code=proc.wait()
    return exit_code, stdout, stderr

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
