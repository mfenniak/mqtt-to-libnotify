{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        python = "python311";
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = (pythonInterpreter: (ps:
          [
            # FIXME: not all these dependencies are needed for the package; some could be split into devShell only
            ps.aiohttp
            ps.aiomqtt
            ps.backoff
            ps.mypy
            ps.pylint
            ps.pytest
            ps.pytest-asyncio
            ps.pytz
            ps.types-pytz
          ]
        ));
      in rec {
        overlays.default = self: super: {
          mqtt-to-libnotify = packages.default;
        };

        packages.default = pkgs.${python}.pkgs.buildPythonApplication {
          pname = "mqtt-to-libnotify";
          version = "0.1";
          src = ./.;
          propagatedBuildInputs = [] ++ ((pythonPackages pkgs.${python}) pkgs.${python}.pkgs);
          doCheck = false; # unit tests fail due to home assistant component's presence
        };

        devShells.default = pkgs.mkShell {
          packages = [
            (pkgs.${python}.withPackages (pythonPackages pkgs.${python}))
            pkgs.mosquitto # for mosquitto_sub & mosquitto_pub test cmds
            pkgs.libnotify
          ];
          shellHook = ''
            export NOTIFY_SEND_CMD=${pkgs.libnotify}/bin/notify-send
          '';
        };
      });
}
