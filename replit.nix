{ pkgs }: {
  deps = [
    pkgs.picolisp
    pkgs.pio
    pkgs.bashInteractive
    pkgs.nodePackages.bash-language-server
    pkgs.man
  ];
}