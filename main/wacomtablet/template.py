pkgname = "wacomtablet"
pkgver = "6.2.1"
pkgrel = 0
build_style = "cmake"
# X*: fail outside x11
make_check_args = ["-E", "(XInputAdaptor|XsetWacomAdaptor|DBusTabletService)"]
make_check_wrapper = ["wlheadless-run", "--"]
hostmakedepends = [
    "cmake",
    "extra-cmake-modules",
    "gettext",
    "ninja",
    "pkgconf",
]
makedepends = [
    "kcmutils-devel",
    "kconfig-devel",
    "kcoreaddons-devel",
    "kdbusaddons-devel",
    "kdoctools-devel",
    "kglobalaccel-devel",
    "ki18n-devel",
    "kio-devel",
    "knotifications-devel",
    "kwidgetsaddons-devel",
    "kwindowsystem-devel",
    "kxmlgui-devel",
    "libplasma-devel",
    "libwacom-devel",
    "plasma5support-devel",
    "qt6-qtdeclarative-devel",
    "xserver-xorg-input-wacom-devel",
]
checkdepends = ["xwayland-run"]
pkgdesc = "GUI configurator for Wacom tablets"
maintainer = "Jami Kettunen <jami.kettunen@protonmail.com>"
license = "GPL-2.0-or-later"
url = "https://invent.kde.org/plasma/wacomtablet"
source = f"$(KDE_SITE)/plasma/{pkgver}/wacomtablet-{pkgver}.tar.xz"
sha256 = "d4bd3f956147d26a1cb8e73971b124f7c15da466853987673c424b2cd0a42610"
