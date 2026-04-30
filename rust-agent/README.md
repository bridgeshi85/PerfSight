# perfsight-agent

PerfSight 
 
High-performance system monitoring agent (CLI).

## Prerequisites

- Rust toolchain (stable)

## Build

```zsh
cargo build
```

## Run (CLI)

### Start monitoring (default)

```zsh
cargo run -- start
```

### Start monitoring with options

```zsh
cargo run -- start -c config.toml -o ./output -i 5 -f json -d 60
```

### Generate default config

```zsh
cargo run -- init-config -o config.toml
```

### Show system info

```zsh
cargo run -- info
```

### Run the built binary

```zsh
./target/debug/perfsight-agent start
```

## Configuration

- Default config path: `config.toml`
- Default output directory: `output`
- If the config file does not exist, the agent uses built-in defaults.

## CLI Reference

- `start`: run the agent
  - `-c, --config <PATH>` (default: `config.toml`)
  - `-o, --output <DIR>` (default: `output`)
  - `-i, --interval <SECONDS>` (default: `5`)
  - `-f, --format <FORMAT>` (default: `json`)
  - `-d, --duration <SECONDS>` (default: `0`, run forever)
- `init-config`: write a default config to a path
- `info`: print a quick system summary

