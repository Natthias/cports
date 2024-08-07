pkgname = "brlaser"
pkgver = "6.2.6"
pkgrel = 0
build_style = "cmake"
hostmakedepends = ["cmake", "ninja"]
makedepends = ["cups-devel"]
pkgdesc = "CUPS driver for monochrome Brother laser printers"
maintainer = "Orphaned <orphaned@chimera-linux.org>"
license = "GPL-2.0-or-later"
url = "https://github.com/Owl-Maintain/brlaser"
source = f"{url}/archive/refs/tags/v{pkgver}.tar.gz"
sha256 = "551f85a234c75c52c52bb76f379eb458ebc7bd7164d55763d97e197a0ad47f6d"
hardening = ["cfi", "vis"]
