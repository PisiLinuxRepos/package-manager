#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

from PyQt5.QtCore import QObject

# Çoklu dil için bu sınıfın tr() methodunu kullanacağız.
_ = QObject()

# Package Manager Version String
version = "2.4.1"
PACKAGE = "Package Manager"

# KAboutData ile ki18nc nin işlevini bilmiyorum.

# Application Data
appName     = "package-manager"
catalog     = appName
programName = _.tr(PACKAGE)
description = _.tr(PACKAGE)
license     = "GPL" #KAboutData.License_GPL
copyright   = _.tr("(c) 2009-2010 TUBITAK/UEKAE")
text        = _.tr(None)
homePage    = "https://github.com/pisilinux/project/tree/master/package-manager-pds"
bugEmail    = "bugs@pisilinux.org"
aboutData   = """KAboutData(appName, catalog, programName, version,
                         description, license, copyright, text,
                         homePage, bugEmail)"""

# Authors
"""aboutData.addAuthor(_.tr("Gökmen Göksel"), _.tr("Developer"))
aboutData.addAuthor(_.tr("Metehan Özbek"), _.tr("KDE5 Port"))
aboutData.addAuthor(_.tr("Faik Uygur"), _.tr("First Author"))
aboutData.setTranslator(ki18nc("NAME OF TRANSLATORS", "Your names"),
                        ki18nc("EMAIL OF TRANSLATORS", "Your emails"))
aboutData.setProgramIconName(":/data/package-manager.png")"""

