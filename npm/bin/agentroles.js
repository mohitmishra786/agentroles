#!/usr/bin/env node

"use strict";

const { execFileSync, execSync } = require("child_process");

function checkNodeVersion() {
  const version = process.version;
  const match = version.match(/v(\d+)\./);
  if (!match || parseInt(match[1], 10) < 20) {
    console.error(
      "agentroles: Node.js 20.0.0 or later is required.\n" +
        "  Current version: " +
        version +
        "\n" +
        "  Node 18 is end-of-life. Upgrade to Node 20+.\n" +
        "  https://nodejs.org/",
    );
    process.exit(1);
  }
}

const args = process.argv.slice(2);
const command = args[0];

checkNodeVersion();

function ensurePython() {
  try {
    const version = execFileSync("python3", ["--version"], {
      encoding: "utf8",
    }).trim();
    const match = version.match(/Python (\d+)\.(\d+)/);
    if (!match) {
      console.error(
        "agentroles: Could not parse Python version from:",
        version,
      );
      process.exit(1);
    }
    const major = parseInt(match[1], 10);
    const minor = parseInt(match[2], 10);
    if (major < 3 || (major === 3 && minor < 11)) {
      console.error(
        `agentroles: Python 3.11+ is required. Found: ${version}\n` +
          "Install Python 3.11+ from https://python.org or your package manager.",
      );
      process.exit(1);
    }
  } catch {
    console.error(
      "agentroles: Python 3 is required but was not found on your PATH.\n" +
        "Install Python 3.11+ from https://python.org or your package manager.",
    );
    process.exit(1);
  }
}

function ensurePipPackage(name, importName) {
  try {
    execFileSync("python3", ["-c", `import ${importName}`], {
      stdio: "ignore",
    });
  } catch {
    console.error(
      `\nagentroles Python package not found. Installing via pip...\n`,
    );
    try {
      execFileSync("python3", ["-m", "pip", "install", name], {
        stdio: "inherit",
      });
    } catch {
      console.error(
        `Failed to install ${name}. Try:\n  python3 -m pip install ${name}`,
      );
      process.exit(1);
    }
  }
}

function main() {
  ensurePython();

  if (
    command === "init" ||
    command === "build" ||
    command === "validate" ||
    command === "migrate"
  ) {
    ensurePipPackage("agentroles", "agentroles");
  }

  try {
    execFileSync("python3", ["-m", "agentroles.cli", ...args], {
      stdio: "inherit",
    });
  } catch (e) {
    process.exit(e.status || 1);
  }
}

main();
