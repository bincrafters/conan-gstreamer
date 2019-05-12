#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, Meson
import os
import shutil


class GStreamerConan(ConanFile):
    name = "gstreamer"
    version = "1.14.4"
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

    requires = ("glib/2.58.3@bincrafters/stable",)
    generators = "pkg_config"

    def configure(self):
        del self.settings.compiler.libcxx

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def build_requirements(self):
        if not tools.which("meson"):
            self.build_requires("meson_installer/0.49.0@bincrafters/stable")
        if not tools.which("pkg-config"):
            self.build_requires("pkg-config_installer/0.29.2@bincrafters/stable")
        self.build_requires("bison_installer/3.3.2@bincrafters/stable")
        self.build_requires("flex_installer/2.6.4@bincrafters/stable")

    def source(self):
        self.run("git clone https://gitlab.freedesktop.org/gstreamer/gstreamer.git --branch %s --depth 1" % self.version)
        os.rename(self.name, self._source_subfolder)

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
        meson.configure(build_folder=self._build_subfolder,
                        source_folder=self._source_subfolder,
                        pkg_config_paths=pkg_config_paths,
                        defs=defs)
        return meson

    def build(self):
        if self.settings.os == "Linux":
            shutil.move("libmount.pc", "mount.pc")
        shutil.move("pcre.pc", "libpcre.pc")
        meson = self._configure_meson()
        meson.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        meson = self._configure_meson()
        meson.install()

    def package_info(self):
        self.cpp_info.libs = ["gstreamer-1.0", "gstbase-1.0", "gstnet-1.0"]
        self.cpp_info.includedirs = [os.path.join("include", "gstreamer-1.0")]
