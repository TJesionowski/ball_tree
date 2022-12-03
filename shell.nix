{pkgs ? import (fetchTarball
  #"https://github.com/NixOS/nixpkgs/archive/47728c4392cd05839d01037beeac7f6104e77ee2.tar.gz"
  "https://github.com/NixOS/nixpkgs/archive/49b8ad618e64d9fe9ab686817bfebe047860dcae.tar.gz"
  ) {}}: pkgs.mkShell { nativeBuildInputs = [ pkgs.manim pkgs.python3
  pkgs.ffmpeg ]; }
