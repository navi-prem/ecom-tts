{
  description = "Go + Neo4j dev environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          go
          golangci-lint
          gopls
          protobuf
          protoc-gen-go
          protoc-gen-go-grpc
          neo4j
        ];

        shellHook = ''
          export NEO4J_HOME=$PWD/.neo4j
          mkdir -p $NEO4J_HOME/data
          mkdir -p $NEO4J_HOME/logs
          echo "Neo4j home: $NEO4J_HOME"
        '';
      };
    };
}
