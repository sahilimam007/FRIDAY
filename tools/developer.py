import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import re
from config import BASE_DIR

# ── Known projects ─────────────────────────────────────────────────────────────
PROJECTS = {
    "friday": os.path.expanduser("~/Developer/friday"),
}

def run_applescript(script):
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip()

def _run(cmd: list, cwd: str = None) -> tuple:
    """Run a shell command. Returns (stdout, stderr, returncode)."""
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


# ── Git ────────────────────────────────────────────────────────────────────────

def git_status(project: str = "friday") -> str:
    path = PROJECTS.get(project.lower(), PROJECTS["friday"])
    out, err, code = _run(["git", "status", "--short"], cwd=path)
    if not out:
        return f"No changes in {project}, everything is clean."
    lines = out.split("\n")
    return f"{len(lines)} changed file(s) in {project}: {', '.join(l.strip() for l in lines[:5])}."

def git_add_commit_push(message: str = "", project: str = "friday") -> str:
    path = PROJECTS.get(project.lower(), PROJECTS["friday"])
    if not message:
        message = "Update via Friday"
    _run(["git", "add", "."], cwd=path)
    out, err, code = _run(["git", "commit", "-m", message], cwd=path)
    if "nothing to commit" in out:
        return "Nothing to commit, working tree is clean."
    push_out, push_err, push_code = _run(["git", "push"], cwd=path)
    if push_code == 0:
        return f"Committed and pushed: {message}."
    return f"Committed but push failed: {push_err}"

def git_log(project: str = "friday", n: int = 3) -> str:
    path = PROJECTS.get(project.lower(), PROJECTS["friday"])
    out, _, _ = _run(["git", "log", f"--oneline", f"-{n}"], cwd=path)
    if not out:
        return "No commits found."
    return "Recent commits: " + " | ".join(out.split("\n"))

def git_diff(project: str = "friday") -> str:
    path = PROJECTS.get(project.lower(), PROJECTS["friday"])
    out, _, _ = _run(["git", "diff", "--stat"], cwd=path)
    if not out:
        return "No unstaged changes."
    return f"Changes: {out}"


# ── VS Code ────────────────────────────────────────────────────────────────────

def open_vscode(project: str = "friday") -> str:
    path = PROJECTS.get(project.lower(), os.path.expanduser(f"~/Developer/{project}"))
    _run(["code", path])
    return f"Opening {project} in VS Code."

def open_vscode_file(filepath: str) -> str:
    expanded = os.path.expanduser(filepath)
    _run(["code", expanded])
    return f"Opening {filepath} in VS Code."


# ── Terminal commands ──────────────────────────────────────────────────────────

def run_command(command: str) -> str:
    """Run a safe shell command and return output."""
    # Block dangerous commands
    blocked = ["rm -rf", "sudo rm", "mkfs", "dd if", ":(){", "chmod 777 /"]
    for b in blocked:
        if b in command.lower():
            return f"That command is blocked for safety."

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=15,
            cwd=os.path.expanduser("~/Developer/friday")
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if out:
            return out[:500]  # cap at 500 chars
        if err:
            return f"Error: {err[:300]}"
        return "Command ran with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Failed to run command: {e}"


# ── Port control ───────────────────────────────────────────────────────────────

def kill_port(port: int) -> str:
    out, _, _ = _run(["lsof", "-ti", f":{port}"])
    if not out:
        return f"Nothing running on port {port}."
    pids = out.strip().split("\n")
    for pid in pids:
        _run(["kill", "-9", pid.strip()])
    return f"Killed {len(pids)} process(es) on port {port}."

def what_is_on_port(port: int) -> str:
    out, _, code = _run(["lsof", "-i", f":{port}"])
    if not out or code != 0:
        return f"Nothing is running on port {port}."
    lines = out.split("\n")
    if len(lines) > 1:
        parts = lines[1].split()
        if parts:
            return f"Port {port} is used by {parts[0]} (PID {parts[1]})."
    return f"Something is on port {port} but couldn't identify it."

def list_open_ports() -> str:
    out, _, _ = _run(["lsof", "-i", "-n", "-P"])
    if not out:
        return "No open ports found."
    lines = [l for l in out.split("\n") if "LISTEN" in l][:8]
    if not lines:
        return "No listening ports found."
    results = []
    for line in lines:
        parts = line.split()
        if len(parts) > 8:
            results.append(f"{parts[0]} on {parts[8]}")
    return "Listening: " + ", ".join(results)


# ── Server health ──────────────────────────────────────────────────────────────

def check_server(url: str = "http://localhost:3000") -> str:
    import urllib.request
    if not url.startswith("http"):
        url = f"http://localhost:{url}"
    try:
        req = urllib.request.urlopen(url, timeout=5)
        return f"Server at {url} is up. Status: {req.status}."
    except Exception as e:
        return f"Server at {url} is down or unreachable."

def check_localhost(port: int = 3000) -> str:
    return check_server(f"http://localhost:{port}")


# ── Python environment ─────────────────────────────────────────────────────────

def list_installed_packages() -> str:
    out, _, _ = _run(["pip", "list", "--format=columns"])
    lines = out.split("\n")[2:]  # skip header
    count = len(lines)
    return f"{count} packages installed in venv."

def check_python_version() -> str:
    out, _, _ = _run(["python3", "--version"])
    return out if out else "Python version unknown."

def run_python_file(filename: str) -> str:
    path = os.path.join(os.path.expanduser("~/Developer/friday"), filename)
    if not os.path.exists(path):
        return f"File {filename} not found in friday project."
    out, err, code = _run(["python3", path],
                           cwd=os.path.expanduser("~/Developer/friday"))
    if code == 0:
        return f"Ran {filename} successfully. Output: {out[:300]}" if out else f"Ran {filename} successfully."
    return f"Error running {filename}: {err[:300]}"


# ── Code tools ─────────────────────────────────────────────────────────────────

def explain_error(error_text: str) -> str:
    """Pass to Ollama for explanation — returns prompt for orchestrator to handle."""
    return f"EXPLAIN_ERROR:{error_text}"

def get_project_structure(project: str = "friday") -> str:
    path = PROJECTS.get(project.lower(), PROJECTS["friday"])
    out, _, _ = _run(["find", path, "-maxdepth", "2",
                       "-not", "-path", "*/.*",
                       "-not", "-path", "*/venv/*",
                       "-not", "-path", "*/__pycache__/*",
                       "-name", "*.py"])
    files = [f.replace(path + "/", "") for f in out.split("\n") if f]
    return f"{project} project files: " + ", ".join(files[:20])

def count_lines_of_code(project: str = "friday") -> str:
    path = PROJECTS.get(project.lower(), PROJECTS["friday"])
    out, _, _ = _run(
        ["find", path, "-name", "*.py",
         "-not", "-path", "*/venv/*",
         "-not", "-path", "*/__pycache__/*"]
    )
    files = [f for f in out.split("\n") if f]
    total = 0
    for f in files:
        try:
            with open(f) as fp:
                total += sum(1 for _ in fp)
        except:
            pass
    return f"Friday project has {total} lines of Python code across {len(files)} files."

def add_project(name: str, path: str) -> str:
    """Add a new project to the known projects list."""
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        PROJECTS[name.lower()] = expanded
        return f"Added project {name} at {path}."
    return f"Path {path} doesn't exist."


# ── Quick test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(git_status())
    print(git_log())
    print(check_python_version())
    print(count_lines_of_code())
    print(list_open_ports())
    print(get_project_structure())
    
