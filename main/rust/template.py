pkgname = "rust"
pkgver = "1.79.0"
pkgrel = 1
hostmakedepends = [
    "cmake",
    "curl",
    "pkgconf",
    "python",
    "llvm-devel",
    "llvm-tools",
    "libffi-devel",
    "ncurses-devel",
    "libxml2-devel",
    "zlib-ng-compat-devel",
    "zstd-devel",
    "cargo-bootstrap",
    "wasi-libc",
]
makedepends = [
    "libffi-devel",
    "ncurses-devel",
    "libxml2-devel",
    "zlib-ng-compat-devel",
    "zstd-devel",
    "llvm-devel",
]
depends = [f"rust-std={pkgver}-r{pkgrel}", "clang", "musl-devel"]
pkgdesc = "Rust programming language"
maintainer = "q66 <q66@chimera-linux.org>"
license = "MIT OR Apache-2.0"
url = "https://rust-lang.org"
source = f"https://static.rust-lang.org/dist/rustc-{pkgver}-src.tar.xz"
sha256 = "ab826e84b8d48ec6eda3370065034dea8c006f6a946d78a9ba12bcb50e6d3c7a"
# global environment
env = {
    "SSL_CERT_FILE": "/etc/ssl/certs/ca-certificates.crt",
    "OPENSSL_NO_VENDOR": "1",
    "RUST_BACKTRACE": "1",
}
# disable check at least for now
# lto always breaks across major llvm vers because of consumer/reader mismatch
options = ["!check", "!lto"]

if self.profile().cross:
    hostmakedepends += ["rust"]
    env["PKG_CONFIG_ALLOW_CROSS"] = "1"
elif self.current_target == "custom:bootstrap":
    hostmakedepends += ["rust"]
else:
    hostmakedepends += ["rust-bootstrap"]

_rlib_dir = f"usr/lib/rustlib/{self.profile().triplet}"

if self.current_target == "custom:bootstrap":
    # bootstrap binaries are statically linked to llvm to
    # avoid cyclic pains when updating llvm to a newer version
    #
    # since there is just one static switch, we need static llvm
    # for both host and target rustc builds
    hostmakedepends += ["llvm-devel-static"]
    makedepends += ["llvm-devel-static"]
    # avoid debug cflags and so on for vendor libs
    options += ["!debug"]


def post_patch(self):
    from cbuild.util import cargo

    # we are patching these
    cargo.clear_vendor_checksums(self, "libc-0.2.150")
    cargo.clear_vendor_checksums(self, "libc-0.2.151")
    cargo.clear_vendor_checksums(self, "libc-0.2.153")


def do_configure(self):
    _tools = ["rustdoc"]
    if self.current_target == "custom:bootstrap":
        _llvm_shared = "false"
        _use_docs = "false"
        _use_rpath = "true"
        _extended = "false"
        _profiler = "false"
    else:
        _llvm_shared = "true"
        # fails to build for wasm targets
        _use_docs = "false"
        _use_rpath = "false"
        _extended = "true"
        _profiler = "true"
        # while we'd love to build cargo and rust in one build, this is
        # unfortunately not possible as rustbuild is junk and breaks rather
        # hard when trying that
        _tools += ["clippy", "src", "rustfmt", "rust-demangler"]
        # for rust-analyzer, only builds on these archs
        match self.profile().arch:
            case "aarch64" | "ppc64" | "ppc64le" | "x86_64":
                _tools += ["rust-analyzer-proc-macro-srv"]

    if self.profile().cross:
        _local_rebuild = "true"
    else:
        _local_rebuild = "false"

    if self.build_dbg:
        _debug = "2"
        _debug_rustc = "1"
    else:
        _debug = "0"
        _debug_rustc = "0"

    tgt_profile = self.profile()
    _tgt_spec = [f"'{tgt_profile.triplet}'"]
    if self.current_target != "custom:bootstrap":
        _tgt_spec += ["'wasm32-wasi'", "'wasm32-unknown-unknown'"]

    # this is a hack that violates packaging guidelines, but it's only
    # for bootstrapping anyway, and conditionally patching it is worse
    #
    # we need to ensure to link to these otherwise we get undefined refs
    if _llvm_shared == "false":
        with open(self.cwd / "compiler/rustc_llvm/src/lib.rs", "a") as f:
            f.write(
                """
#[link(name = "ffi")]
extern {}
#[link(name = "z")]
extern {}
#[link(name = "zstd")]
extern {}
#[link(name = "ncursesw")]
extern {}
"""
            )

    with self.profile("host") as hpf:
        host_profile = hpf

    with open(self.cwd / "config.toml", "w") as cfg:
        cfg.write(
            f"""
change-id = 123711

[llvm]
ninja = false
link-shared = {_llvm_shared}
static-libstdcpp = false
use-libcxx = true

[build]

build = '{host_profile.triplet}'
host = ['{tgt_profile.triplet}']
target = [{','.join(_tgt_spec)}]

cargo = '/usr/bin/cargo'
rustc = '/usr/bin/rustc'

docs = {_use_docs}

python = 'python'

locked-deps = true
vendor = true

extended = {_extended}

tools = [{", ".join(map(lambda v: '"' + v + '"', _tools))}]

profiler = {_profiler}

local-rebuild = {_local_rebuild}

[install]

prefix = '/usr'

[rust]

optimize = true
debug = false
backtrace-on-ice = true
codegen-units = 1
codegen-units-std = 1

debuginfo-level = {_debug_rustc}
debuginfo-level-std = {_debug}

incremental = false
parallel-compiler = false

channel = 'stable'
description = 'Chimera Linux'

rpath = {_use_rpath}

frame-pointers = true

deny-warnings = false

llvm-libunwind = 'system'

[dist]

src-tarball = true
compression-formats = ['xz']

[target.{host_profile.triplet}]

cc = '{self.get_tool("CC", target="host")}'
cxx = '{self.get_tool("CXX", target="host")}'
ar = '/usr/bin/llvm-ar'
ranlib = '/usr/bin/llvm-ranlib'
linker = '{self.get_tool("CC", target="host")}'
llvm-config = '/usr/bin/llvm-config'
crt-static = false

"""
        )
        # cross-target definition if used
        if tgt_profile.cross:
            cfg.write(
                f"""
[target.{tgt_profile.triplet}]

cc = '{self.get_tool("CC")}'
cxx = '{self.get_tool("CXX")}'
ar = '/usr/bin/llvm-ar'
ranlib = '/usr/bin/llvm-ranlib'
linker = '{self.get_tool("CC")}'
llvm-config = '/usr/bin/llvm-config'
crt-static = false
"""
            )
        # wasm targets for non-bootstrap
        if self.current_target != "custom:bootstrap":
            cfg.write(
                """
[target.wasm32-unknown-unknown]

sanitizers = false
profiler = false

[target.wasm32-wasi]

sanitizers = false
profiler = false
wasi-root = '/usr/wasm32-unknown-wasi'
"""
            )


def do_build(self):
    benv = {}
    benv["CARGO_HOME"] = str(self.chroot_cwd / ".cargo")
    # we don't want the default cross sysroot here
    benv["RUSTFLAGS"] = ""
    # ensure correct flags are used for host C/C++ code
    with self.profile("host") as pf:
        benv["CFLAGS_" + pf.triplet] = self.get_cflags(shell=True)
        benv["CXXFLAGS_" + pf.triplet] = self.get_cxxflags(shell=True)
    # ensure correct flags are used for target C/C++ code
    with self.profile("target") as pf:
        benv["CFLAGS_" + pf.triplet] = self.get_cflags(shell=True)
        benv["CXXFLAGS_" + pf.triplet] = self.get_cxxflags(shell=True)
    # and hope it does not fail
    #
    # we also need to ensure PKG_CONFIG is unset because otherwise the
    # target pkg-config will leak into some host build stuff and will
    # affect the sysroot used (which will result in link failures)
    #
    self.do(
        "env",
        "-u",
        "PKG_CONFIG",
        # prevent global flags from being applied to wasi/other targets
        "-u",
        "CFLAGS",
        "-u",
        "CXXFLAGS",
        "--",
        "python",
        "x.py",
        "dist",
        "--jobs",
        str(self.make_jobs),
        env=benv,
    )


def do_check(self):
    self.do(
        "python",
        "x.py",
        "test",
        f"-j{self.make_jobs}",
        "--no-fail-fast",
        "src/test/codegen",
        "src/test/codegen-units",
        "src/test/incremental",
        "src/test/mir-opt",
        "src/test/pretty",
        "src/test/run-make",
        "src/test/run-make-fulldeps",
        "src/test/ui",
        "src/test/ui-fulldeps",
    )


def _untar(self, name, has_triple=True):
    trip = self.profile().triplet

    fname = f"{name}-{pkgver}"
    if isinstance(has_triple, str):
        fname += f"-{has_triple}"
    elif has_triple:
        fname += f"-{trip}"
    fname += ".tar.xz"

    self.do(
        "tar",
        "xf",
        self.chroot_cwd / f"build/dist/{fname}",
        "-C",
        self.chroot_destdir / "usr",
        "--strip-components=2",
        "--exclude=manifest.in",
        "--no-same-owner",
    )


@custom_target("bootstrap", "build")
def _boot(self):
    # already done
    pass


def do_install(self):
    self.install_license("COPYRIGHT")
    self.install_license("LICENSE-APACHE")
    self.install_license("LICENSE-MIT")

    # used if we decide to ship src
    self.install_dir("usr/src")

    # extract the archives
    for f in ["rustc", "rust-std", "rustc-dev", "clippy", "rustfmt"]:
        self.log(f"unpacking {f}...")
        _untar(self, f)
    # wasm shit
    _untar(self, "rust-std", "wasm32-unknown-unknown")
    _untar(self, "rust-std", "wasm32-wasi")

    self.log("unpacking rust-src...")
    _untar(self, "rust-src", False)

    # remove rust copies of llvm tools
    self.log("cleaning up tools...")
    trip = self.profile().triplet
    for f in (self.destdir / f"usr/lib/rustlib/{trip}/bin").glob("rust-ll*"):
        f.unlink()

    # usr/lib stuff should be symlinks into rustlib
    self.log("relinking rustlibs...")
    for f in (self.destdir / "usr/lib").glob("*.so"):
        rlibf = self.destdir / _rlib_dir / "lib" / f.name
        rlibf.unlink()
        self.mv(f, rlibf)
        f.symlink_to(rlibf.relative_to(f.parent))


@subpackage("rust-wasm")
def _wasm(self):
    self.pkgdesc = "WebAssembly targets"
    self.depends = [f"{pkgname}={pkgver}-r{pkgrel}", "lld", "wasi-libc"]
    self.options = ["!strip"]

    return ["usr/lib/rustlib/wasm32-*"]


@subpackage("rust-clippy")
def _clippy(self):
    self.pkgdesc = "Lints to catch common mistakes"
    self.depends = [f"{pkgname}={pkgver}-r{pkgrel}"]

    return [
        "usr/bin/cargo-clippy",
        "usr/bin/clippy-driver",
    ]


@subpackage("rustfmt")
def _fmt(self):
    self.pkgdesc = "Rust code formatter"
    self.depends = [f"{pkgname}={pkgver}-r{pkgrel}"]

    return [
        "usr/bin/rustfmt",
        "usr/bin/cargo-fmt",
    ]


@subpackage("rust-std")
def _std(self):
    self.pkgdesc = f"{pkgdesc} (static rlibs)"
    self.options = ["!strip"]

    return [
        f"{_rlib_dir}/lib/*.rlib",
        f"{_rlib_dir}/lib/*.rmeta",
    ]


@subpackage("rust-src")
def _src(self):
    self.pkgdesc = f"{pkgdesc} (source)"

    return [
        "usr/lib/rustlib/rustc-src",
        "usr/lib/rustlib/src",
    ]
