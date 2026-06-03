# devex-platform

A Developer Experience monorepo containing independent, distributable packages for CLI tooling and infrastructure framework code. This repository is a proof of concept for a Staff Platform Engineer challenge.

## Packages

### cli

Python CLI tool (`devex-cli`) distributed via uv. Entry point: `devex`.

### framework

TypeScript framework (`@luicruz01/devex-framework`) distributed via pnpm.

## Quick install

### CLI

```bash
uvx --from git+https://github.com/luicruz01/devex-platform#subdirectory=cli devex
```

### Framework

```bash
pnpm add github:luicruz01/devex-platform#main --filter framework
```

## TODO

- Documentation, usage guides, and contribution workflow will be added in a future session.
