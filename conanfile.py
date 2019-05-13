#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, Meson
import glob
import os
import shutil


class GStreamerConan(ConanFile):
    name = "gstreamer"
    version = "1.16.0"
    description = "GStreamer is a development framework for creating applications like media players, video editors, streaming media broadcasters and so on"
    topics = ("conan", "gstreamer", "multimedia", "video", "audio", "broadcasting", "framework", "media")
    url = "https://github.com/bincrafters/conan-gstreamer"
    homepage = "https://gstreamer.freedesktop.org/"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "GPL-2.0-only"
    exports = ["LICENSE.md"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    exports_sources = ["patches/*.diff"]

    requires = ("glib/2.58.3@bincrafters/stable",)
    generators = "pkg_config"

    def configure(self):
        del self.settings.compiler.libcxx

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def build_requirements(self):
        if not tools.which("meson"):
            self.build_requires("meson_installer/0.50.0@bincrafters/stable")
        if not tools.which("pkg-config"):
            self.build_requires("pkg-config_installer/0.29.2@bincrafters/stable")
        self.build_requires("bison_installer/3.3.2@bincrafters/stable")
        self.build_requires("flex_installer/2.6.4@bincrafters/stable")

    def source(self):
        self.run("git clone https://gitlab.freedesktop.org/gstreamer/gstreamer.git --branch %s --depth 1" % self.version)
        os.rename(self.name, self._source_subfolder)

    def _apply_patches(self):
        for filename in sorted(glob.glob("patches/*.diff")):
            self.output.info('applying patch "%s"' % filename)
            tools.patch(base_path=self._source_subfolder, patch_file=filename)

    def _configure_meson(self):
        glib_pc = os.path.join(self.deps_cpp_info["glib"].rootpath, "lib", "pkgconfig")
        print(glib_pc)
        pkg_config_paths = [glib_pc, self.source_folder]
        meson = Meson(self)
        defs = dict()
        if self.settings.os == "Linux":
            defs["libdir"] = "lib"
        if str(self.settings.compiler) in ["gcc", "clang"]:
            if self.settings.arch == "x86":
                defs["c_args"] = "-m32"
                defs["cpp_args"] = "-m32"
                defs["c_link_args"] = "-m32"
                defs["cpp_link_args"] = "-m32"
            elif self.settings.arch == "x86_64":
                defs["c_args"] = "-m64"
                defs["cpp_args"] = "-m64"
                defs["c_link_args"] = "-m64"
                defs["cpp_link_args"] = "-m64"
        elif self.settings.compiler == "Visual Studio":
            defs["c_args"] = "-%s" % self.settings.compiler.runtime
            defs["cpp_args"] = "-%s" % self.settings.compiler.runtime
            if int(str(self.settings.compiler.version)) < 14:
                defs["c_args"] += " -Dsnprintf=_snprintf"
                defs["cpp_args"] += " -Dsnprintf=_snprintf"
        defs["tools"] = "disabled"
        defs["examples"] = "disabled"
        defs["benchmarks"] = "disabled"
        defs["tests"] = "disabled"
        meson.configure(build_folder=self._build_subfolder,
                        source_folder=self._source_subfolder,
                        pkg_config_paths=pkg_config_paths,
                        defs=defs)
        return meson

    def build(self):
        self._apply_patches()
        if self.settings.os == "Linux":
            shutil.move("libmount.pc", "mount.pc")
        shutil.move("pcre.pc", "libpcre.pc")
        meson = self._configure_meson()
        meson.build()

    def _fix_library_names(self):
        # regression in 1.16
        if self.settings.compiler == "Visual Studio":
            with tools.chdir(os.path.join(self.package_folder, "lib")):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info("rename %s into %s" % (filename_old, filename_new))
                    shutil.move(filename_old, filename_new)

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        meson = self._configure_meson()
        meson.install()

        self._fix_library_names()

    def package_info(self):
        self.cpp_info.libs = ["gstreamer-1.0", "gstbase-1.0", "gstnet-1.0"]
        self.cpp_info.includedirs = [os.path.join("include", "gstreamer-1.0")]
        if self.settings.os == "Linux":
            self.cpp_info.libs.append("dl")
        elif self.settings.os == "Windows":
            self.cpp_info.libs.append("ws2_32")
        if not self.options.shared:
            self.cpp_info.defines.append("GST_STATIC_COMPILATION")
