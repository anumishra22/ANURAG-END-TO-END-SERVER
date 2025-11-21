{ pkgs }: {
  deps = [
    pkgs.chromedriver
    pkgs.chromium
    pkgs.picolisp
    pkgs.pio
    pkgs.bashInteractive
    pkgs.nodePackages.bash-language-server
    pkgs.man
  ];
}