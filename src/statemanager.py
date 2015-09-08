#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox


import config

if config.USE_APPINFO:
    from appinfo.client import AppInfoClient

import backend

from pmutils import *
from pmlogging import logger

class StateManager(QObject):

    (ALL, INSTALL, REMOVE, UPGRADE, HISTORY) = range(5)

    def __init__(self, parent=None):
        QObject.__init__(self)
        self.state = self.ALL
        self._group_cache = {}
        self.iface = backend.pm.Iface()
        self.reset()

    def reset(self):
        self.cached_packages = None
        self._typeCaches = {}
        self._typeFilter = 'normal'
        self.initializePackageLists()

    def initializePackageLists(self):
        self.__groups = self.iface.getGroups()
        self.__installed_packages = self.iface.getInstalledPackages()
        self.__new_packages = self.iface.getNewPackages()
        self.__all_packages = self.__installed_packages + self.__new_packages

    repositoriesChanged = pyqtSignal()
    def setState(self, state):
        self.state = state
        self.reset()
        self.repositoriesChanged.emit()

    def getState(self):
        return self.state

    def packages(self):
        if self.cached_packages == None:
            if self.state == self.UPGRADE:
                self.cached_packages = self.iface.getUpdates()
                self._typeCaches = {}
            else:
                if self.state == self.REMOVE:
                    self.cached_packages = self.__installed_packages
                elif self.state == self.INSTALL:
                    self.cached_packages = self.__new_packages
                else:
                    self.cached_packages = self.__all_packages
                if self.onlyGuiInState():
                    self.cached_packages = set(self.cached_packages).intersection(self.iface.getIsaPackages("app:gui"))
        if not self._typeFilter == 'normal' and self.state == self.UPGRADE:
            if not self._typeCaches.has_key(self._typeFilter):
                self._typeCaches[self._typeFilter] = self.iface.filterUpdates(self.cached_packages, self._typeFilter)
            return self._typeCaches[self._typeFilter]
        return list(self.cached_packages)

    def onlyGuiInState(self):
        return config.PMConfig().showOnlyGuiApp()

    def setCachedPackages(self, packages):
        self.cached_packages = packages

    def getActionCurrent(self, action):
        return {"System.Manager.installPackage":self.tr("Installing Package(s)"),
                "System.Manager.reinstallPackage":self.tr("Installing Package(s)"),
                "System.Manager.removePackage":self.tr("Removing Package(s)"),
                "System.Manager.updatePackage":self.tr("Upgrading Package(s)"),
                "System.Manager.setRepositories":self.tr("Applying Repository Changes"),
                "System.Manager.updateRepository":self.tr("Updating Repository"),
                "System.Manager.updateAllRepositories":self.tr("Updating Repository(s)")}[str(action)]

    def toBe(self):
        return {self.INSTALL:self.tr("installed"),
                self.REMOVE :self.tr("removed"),
                self.UPGRADE:self.tr("upgraded"),
                self.ALL    :self.tr("modified")}[self.state]

    def getActionName(self, state = None):
        state = self.state if state == None else state
        return {self.INSTALL:self.tr("Install Package(s)"),
                self.REMOVE :self.tr("Remove Package(s)"),
                self.UPGRADE:self.tr("Upgrade Package(s)"),
                self.ALL    :self.tr("Select Operation")}[state]

    def getActionIcon(self, state = None):
        state = self.state if state == None else state
        return {self.INSTALL:KIcon(("list-add", "add")),
                self.REMOVE :KIcon(("list-remove", "remove")),
                self.UPGRADE:KIcon(("system-software-update", "gear")),
                self.ALL    :KIcon("preferences-other")}[state]

    def getSummaryInfo(self, total):
        return {self.INSTALL:self.tr("%1 new package(s) have been installed succesfully.", total),
                self.REMOVE :self.tr("%1 package(s) have been removed succesfully.", total),
                self.UPGRADE:self.tr("%1 package(s) have been upgraded succesfully.", total),
                self.ALL    :self.tr("%1 package(s) have been modified succesfully.", total)}[self.state]

    def getBasketInfo(self):
        return {self.INSTALL:self.tr("You have selected the following package(s) to install:"),
                self.REMOVE :self.tr("You have selected the following package(s) to removal:"),
                self.UPGRADE:self.tr("You have selected the following package(s) to upgrade:"),
                self.ALL    :self.tr("You have selected the following package(s) to modify:")}[self.state]

    def getBasketExtrasInfo(self):
        return {self.INSTALL:self.tr("Extra dependencies of the selected package(s) that are also going to be installed:"),
                self.REMOVE :self.tr("Reverse dependencies of the selected package(s) that are also going to be removed:"),
                self.UPGRADE:self.tr("Extra dependencies of the selected package(s) that are also going to be upgraded:"),
                self.ALL    :self.tr("Extra dependencies of the selected package(s) that are also going to be modified:")}[self.state]

    def groups(self):
        return self.__groups

    def groupPackages(self, name):
        if name == "all":
            return self.packages()
        else:
            if self._group_cache.has_key(name):
                group_packages = self._group_cache[name]
            else:
                group_packages = self.iface.getGroupPackages(name)
                self._group_cache[name] = group_packages
            return list(set(self.packages()).intersection(group_packages))

    def chainAction(self, operation):
        chains = { "System.Manager.setRepositories":lambda:self.repositoriesChanged.emit() }
        if chains.has_key(operation):
            chains[operation]()

    def updateRepoAction(self, silence = False):

        if not self.iface.updateRepositories():
            if not silence:
                self.showFailMessage()
            return False

        if config.USE_APPINFO:
            if network_available():
                if not AppInfoClient().checkOutDB()[0]:
                    AppInfoClient().setServer('http://appinfo.pisilinux.org')
                    AppInfoClient().checkOutDB()

        return True

    def statusText(self, packages, packagesSize, extraPackages, extraPackagesSize):
        if not packages:
            return ''

        text = self.tr("Currently there are <b>%1</b> selected package(s) of total <b>%2</b> of size ", packages, packagesSize)
        if extraPackages:
            if self.state == self.REMOVE:
                text += self.tr("with <b>%1</b> reverse dependencies of total <b>%2</b> of size ", extraPackages, extraPackagesSize)
            else:
                text += self.tr("with <b>%1</b> extra dependencies of total <b>%2</b> of size ", extraPackages, extraPackagesSize)
        text += self.tr("in your basket.")

        return text

    def operationAction(self, packages, silence = False, reinstall = False, connection_required = True):

        if connection_required:
            if not network_available() and not self.state == self.REMOVE:
                if not repos_available(self.iface):
                    self.showFailMessage()
                    return False

        if not silence and not self.state == self.REMOVE:
            if not self.conflictCheckPasses(packages):
                return False

        if reinstall:
            return self.iface.reinstallPackages(packages)

        return {self.ALL    :self.iface.modifyPackages,
                self.INSTALL:self.iface.installPackages,
                self.REMOVE :self.iface.removePackages,
                self.UPGRADE:self.iface.upgradePackages}[self.state](packages)

    def setActionHandler(self, handler):
        self.iface.setHandler(handler)

    def setExceptionHandler(self, handler):
        self.iface.setExceptionHandler(handler)

    def conflictCheckPasses(self, packages):
        (C, D, pkg_conflicts) = self.iface.getConflicts(packages, self.state)

        conflicts_within = list(D)
        if conflicts_within:
            text = self.tr("Selected packages [%1] are in conflict with each other. These packages can not be installed together.", ", ".join(conflicts_within))
            QMessageBox.critical(None, self.tr("Conflict Error"), text, QMessageBox.Ok)
            return False

        if pkg_conflicts:
            text = self.tr("The following packages conflicts:\n")
            for pkg in pkg_conflicts.keys():
                text += self.tr("%1 conflicts with: [%2]\n", pkg, ", ".join(pkg_conflicts[pkg]))
            text += self.tr("\nRemove the conflicting packages from the system?")
            return QMessageBox.warning(None, self.tr("Conflict Error"), text, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes

        return True

    def checkUpdateActions(self, packages):
        return self.iface.checkUpdateActions(packages)

    def checkInstallActions(self, packages):
        return filter(lambda x: x in self.__installed_packages, packages)

    def checkRemoveActions(self, packages):
        important_packages = open(config.DATA_DIR + 'important_packages').read().split('\n')
        return list(set(important_packages).intersection(packages))

    def inInstall(self):
        return self.state == self.INSTALL

    def inRemove(self):
        return self.state == self.REMOVE

    def inUpgrade(self):
        return self.state == self.UPGRADE

    def showFailMessage(self):
        QMessageBox.critical(None,
                             self.tr("Network Error"),
                             self.tr("Please check your network connections and try again."),
                             QMessageBox.Ok)

