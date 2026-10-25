#!/usr/bin/env node

/**
 * BOB (Bouncer-on-Board) — Zero-Trust IDE Agent Firewall & Security Gatekeeper
 * 
 * Standalone Node.js CLI & NPX installer.
 * Zero npm dependencies (pure Node.js standard library).
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn, spawnSync, execSync } = require('child_process');
const readline = require('readline');

const VERSION = '0.1.0';

// ANSI Colors (Standard 16-color palette for maximum terminal compatibility)
const c = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
};

function printBanner() {
  console.log(`
${c.cyan}  ____   ____  ____  ${c.reset}
${c.cyan} | __ ) / __ \\| __ ) ${c.reset}  ${c.bold}BOB (Bouncer-on-Board)${c.reset}
${c.cyan} |  _ \\| |  | |  _ \\ ${c.reset}  ${c.dim}Zero-Trust IDE Agent Firewall & Security Gatekeeper${c.reset}
${c.cyan} | |_) | |__| | |_) |${c.reset}  ${c.green}v${VERSION}${c.reset}
${c.cyan} |____/ \\____/|____/ ${c.reset}
`);
}

function findPythonCommand() {
  const isWindows = process.platform === 'win32';
  const candidates = isWindows ? ['python', 'py -3', 'py', 'python3'] : ['python3', 'python'];

  for (const cmd of candidates) {
    try {
      const parts = cmd.split(' ');
      const res = spawnSync(parts[0], [...parts.slice(1), '--version'], { encoding: 'utf-8', timeout: 2500 });
      if (res.status === 0) {
        const out = (res.stdout || res.stderr || '').trim();
        const match = out.match(/Python\s+(\d+)\.(\d+)/i);
        if (match) {
          const major = parseInt(match[1], 10);
          const minor = parseInt(match[2], 10);
          if (major >= 3 && minor >= 10) {
            return { cmd: parts[0], args: parts.slice(1), version: out };
          }
        }
      }
    } catch (_) {}
  }
  return null;
}

function findBobExecutable() {
  const isWindows = process.platform === 'win32';
  const cwd = process.cwd();

  // 1. Check local virtualenv in current working directory
  const venvPaths = isWindows
    ? [
        path.join(cwd, '.venv', 'Scripts', 'bob.exe'),
        path.join(cwd, 'venv', 'Scripts', 'bob.exe'),
      ]
    : [
        path.join(cwd, '.venv', 'bin', 'bob'),
        path.join(cwd, 'venv', 'bin', 'bob'),
      ];

  for (const p of venvPaths) {
    if (fs.existsSync(p)) {
      return { path: p, isVenv: true };
    }
  }

  // 2. Check system PATH
  try {
    const whichCmd = isWindows ? 'where bob' : 'which bob';
    const out = execSync(whichCmd, { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'], timeout: 2000 }).trim();
    const firstLine = out.split('\n')[0].trim();
    if (firstLine && fs.existsSync(firstLine)) {
      return { path: firstLine, isVenv: false };
    }
  } catch (_) {}

  // 3. Check python -m bob.cli
  const py = findPythonCommand();
  if (py) {
    try {
      const checkRes = spawnSync(py.cmd, [...py.args, '-m', 'bob.cli', '--help'], {
        encoding: 'utf-8',
        timeout: 3000,
      });
      if (checkRes.status === 0) {
        return { isModule: true, py };
      }
    } catch (_) {}
  }

  return null;
}

function getSkillTemplate() {
  // Try reading bundled SKILL.md
  const skillFile = path.resolve(__dirname, '..', 'skills', 'bob', 'SKILL.md');
  if (fs.existsSync(skillFile)) {
    try {
      return fs.readFileSync(skillFile, 'utf-8');
    } catch (_) {}
  }

  return `---
name: bob
description: "Zero-Trust IDE Agent Firewall & Security Gatekeeper. Inspects packages before download to block slopsquatting, scans code for secrets with native IDE AI triage, guards instructions against prompt injection, and manages automatic terminal shims."
argument-hint: "bob scan [path] | bob check <pypi|npm> <package> | bob guard <file> | bob doctor | bob protect"
user-invocable: true
---

# BOB (Bouncer-on-Board) — Zero-Trust IDE Agent Firewall
Use \`/bob scan\`, \`/bob check <pypi|npm> <pkg>\`, \`/bob guard <file>\`, \`/bob doctor\`, or \`/bob protect\`.
`;
}

function deploySkillFiles(targetDir, targetIde) {
  const installed = [];
  const content = getSkillTemplate();
  const ide = (targetIde || 'all').toLowerCase();
  const home = os.homedir();

  // 1. Antigravity Skill (~/.gemini/config/skills/bob/SKILL.md)
  if (ide === 'all' || ide === 'antigravity') {
    try {
      const agDir = path.join(home, '.gemini', 'config', 'skills', 'bob');
      fs.mkdirSync(agDir, { recursive: true });
      const agFile = path.join(agDir, 'SKILL.md');
      fs.writeFileSync(agFile, content, 'utf-8');
      installed.push(agFile);
    } catch (_) {}
  }

  // 2. Claude Code Skill (~/.claude/skills/bob/SKILL.md)
  if (ide === 'all' || ide === 'claude') {
    try {
      const claudeDir = path.join(home, '.claude', 'skills', 'bob');
      fs.mkdirSync(claudeDir, { recursive: true });
      const claudeFile = path.join(claudeDir, 'SKILL.md');
      fs.writeFileSync(claudeFile, content, 'utf-8');
      installed.push(claudeFile);
    } catch (_) {}
  }

  // 3. Cursor Rules (.cursor/rules/bob.mdc)
  if (ide === 'all' || ide === 'cursor' || ide === 'vscode') {
    try {
      const cursorDir = path.join(targetDir, '.cursor', 'rules');
      fs.mkdirSync(cursorDir, { recursive: true });
      const cursorFile = path.join(cursorDir, 'bob.mdc');
      fs.writeFileSync(cursorFile, content, 'utf-8');
      installed.push(cursorFile);
    } catch (_) {}
  }

  // 4. Initialize workspace allowlist
  try {
    const bobDir = path.join(targetDir, '.bob');
    fs.mkdirSync(bobDir, { recursive: true });
    const allowlist = path.join(bobDir, 'allowlist.yaml');
    if (!fs.existsSync(allowlist)) {
      fs.writeFileSync(allowlist, '# Human-managed package allowlist\n[]\n', 'utf-8');
      installed.push(allowlist);
    }
  } catch (_) {}

  return installed;
}

function promptUser(query) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(query, (ans) => {
      rl.close();
      resolve(ans.trim());
    });
  });
}

async function runInteractiveInstaller() {
  printBanner();
  console.log(`${c.bold}Welcome to the BOB Installer & Setup Assistant!${c.reset}\n`);
  console.log('BOB acts as an automated firewall and security gatekeeper for your IDE agents.');
  console.log('It stops slopsquatting, intercepts unverified package downloads, and audits secrets.\n');

  console.log(`${c.cyan}Step 1: Intelligence Mode${c.reset}`);
  console.log(`  ${c.bold}1${c.reset} IDE-Native AI (${c.green}Recommended for IDE Skills${c.reset} - Zero Config, uses host agent)`);
  console.log(`  ${c.bold}2${c.reset} Local AI via Ollama (Private, Free, Gemma)`);
  console.log(`  ${c.bold}3${c.reset} Cloud AI via API Key (Gemini, OpenAI, Groq)`);
  console.log(`  ${c.bold}4${c.reset} Pure Deterministic Mode (100% built-in local rules)`);

  const aiChoice = (await promptUser(`\nChoose intelligence mode [1-4] (default 1): `)) || '1';

  console.log(`\n${c.cyan}Step 2: IDE Environment Protection${c.reset}`);
  console.log(`  ${c.bold}1${c.reset} Cursor / VS Code / Windsurf`);
  console.log(`  ${c.bold}2${c.reset} Google Antigravity IDE`);
  console.log(`  ${c.bold}3${c.reset} Claude Code / Terminal Agents`);
  console.log(`  ${c.bold}4${c.reset} All of the Above (${c.green}Complete Protection - Recommended${c.reset})`);

  const ideChoice = (await promptUser(`\nSelect environment to protect [1-4] (default 4): `)) || '4';

  const ideMap = { '1': 'cursor', '2': 'antigravity', '3': 'claude', '4': 'all' };
  const chosenIde = ideMap[ideChoice] || 'all';

  const targetDir = process.cwd();
  console.log(`\nDeploying universal skill and firewall rules to: ${c.bold}${targetDir}${c.reset}...`);
  const installed = deploySkillFiles(targetDir, chosenIde);

  for (const item of installed) {
    console.log(`  ${c.green}[+]${c.reset} Installed: ${item}`);
  }

  // Check Python backend
  const bobExe = findBobExecutable();
  if (bobExe) {
    console.log(`\n${c.green}[OK]${c.reset} Python core engine detected.`);
    // Run bob protect
    if (bobExe.path) {
      spawnSync(bobExe.path, ['protect'], { stdio: 'inherit' });
    } else if (bobExe.isModule) {
      spawnSync(bobExe.py.cmd, [...bobExe.py.args, '-m', 'bob.cli', 'protect'], { stdio: 'inherit' });
    }
  } else {
    console.log(`\n${c.yellow}[!] Python core engine ('bob') is not yet installed.${c.reset}`);
    const py = findPythonCommand();
    if (py) {
      const installNow = await promptUser(`Would you like to install the Python CLI now via pip? (y/N): `);
      if (installNow.toLowerCase() === 'y' || installNow.toLowerCase() === 'yes') {
        const pyprojectExists = fs.existsSync(path.join(targetDir, 'pyproject.toml'));
        const pipArgs = pyprojectExists
          ? [...py.args, '-m', 'pip', 'install', '-e', targetDir]
          : [...py.args, '-m', 'pip', 'install', 'bouncer-on-board'];
        console.log(`Running: ${py.cmd} ${pipArgs.join(' ')}...`);
        spawnSync(py.cmd, pipArgs, { stdio: 'inherit' });
      }
    } else {
      console.log(`Notice: Python 3.10+ was not found in PATH.`);
      console.log(`Skill files are deployed. Once Python is installed, run: pip install bouncer-on-board`);
    }
  }

  console.log(`\n${c.bold}${c.green}BOB is ready!${c.reset}`);
  console.log(`In your IDE (Antigravity, Claude Code, Cursor), you can now use:`);
  console.log(`  ${c.cyan}/bob scan${c.reset}                 - Security audit of workspace`);
  console.log(`  ${c.cyan}/bob check pypi <pkg>${c.reset}     - Pre-install package gatekeeper`);
  console.log(`  ${c.cyan}/bob doctor${c.reset}               - Diagnostics & shim inspection`);
  console.log(`  ${c.cyan}/bob protect${c.reset}              - Re-apply terminal protection`);
}

function showHelp() {
  printBanner();
  console.log(`Usage: npx bouncer-on-board [command] [options]
       bob [command] [options]

Commands:
  install, setup        Run interactive onboarding and configure IDE skills & shims
  protect [workspace]   Configure Layer 1 IDE hooks and Layer 2 PATH shims
  scan [path]           Scan code for secrets, vulnerabilities, and prompt injection
  check <pypi|npm> <pkg> Intercept & inspect package before downloading (blocks slopsquatting)
  guard <file>          Audit markdown or prompt text for indirect injection
  doctor                Run environment diagnostics and verify active shims
  allow <pkg>           Allowlist a verified package

Options:
  --help, -h            Show this help message
  --version, -v         Show version number

Examples:
  npx bouncer-on-board install
  npx bouncer-on-board doctor
  npx bouncer-on-board check pypi requests
  npx bouncer-on-board scan .
`);
}

function forwardToPythonBob(bobExe, args) {
  // Normalize command aliases: 'check' -> 'check-install'
  const normalizedArgs = args.map((a) => (a === 'check' ? 'check-install' : a));

  if (bobExe.path) {
    const child = spawn(bobExe.path, normalizedArgs, { stdio: 'inherit' });
    child.on('exit', (code) => process.exit(code || 0));
  } else if (bobExe.isModule) {
    const child = spawn(bobExe.py.cmd, [...bobExe.py.args, '-m', 'bob.cli', ...normalizedArgs], {
      stdio: 'inherit',
    });
    child.on('exit', (code) => process.exit(code || 0));
  }
}

async function main() {
  const args = process.argv.slice(2);
  const firstArg = args[0] ? args[0].toLowerCase() : '';

  if (firstArg === '--version' || firstArg === '-v') {
    console.log(`bob version ${VERSION}`);
    process.exit(0);
  }

  if (firstArg === '--help' || firstArg === '-h') {
    showHelp();
    process.exit(0);
  }

  if (!firstArg || firstArg === 'install' || firstArg === 'setup') {
    await runInteractiveInstaller();
    process.exit(0);
  }

  // Passthrough to Python bob CLI
  const bobExe = findBobExecutable();
  if (bobExe) {
    forwardToPythonBob(bobExe, args);
  } else {
    // Python bob CLI not found
    if (firstArg === 'protect') {
      const targetDir = args[1] ? path.resolve(args[1]) : process.cwd();
      const installed = deploySkillFiles(targetDir, 'all');
      console.log(`${c.green}[OK]${c.reset} Deployed BOB skill files to:`);
      for (const f of installed) {
        console.log(`  - ${f}`);
      }
      process.exit(0);
    }

    console.error(`${c.red}Error:${c.reset} Python core engine ('bob') is not available on PATH.`);
    console.error(`Please install Python 3.10+ and run:`);
    console.error(`  ${c.cyan}pip install bouncer-on-board${c.reset}`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`Unexpected error: ${err.message}`);
  process.exit(1);
});
