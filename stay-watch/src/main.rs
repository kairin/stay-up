//! Launch the two Python helpers and show how long they run.

#![windows_subsystem = "windows"]

use std::env;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::thread;

mod ui;

use stay_watch::{keep_awake_args, monitor_args, parse_keep_awake_pid, parse_seconds};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("stay-watch crate must live in the repository")
        .to_path_buf()
}

fn python_executable() -> PathBuf {
    match Command::new("python")
        .args(["-c", "import sys; print(sys.executable)"])
        .output()
    {
        Ok(output) if output.status.success() => {
            let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !path.is_empty() {
                return PathBuf::from(path);
            }
        }
        _ => {}
    }
    PathBuf::from("python")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let seconds = match parse_seconds(&args) {
        Ok(value) => value,
        Err(error) => {
            let _ = error;
            std::process::exit(2);
        }
    };

    let repo = repo_root();
    let keep_script = repo.join("keep-awake.py");
    let monitor_script = repo.join("monitor-helper.py");
    if !keep_script.is_file() || !monitor_script.is_file() {
        std::process::exit(1);
    }

    let log = repo.join("local").join("stay-watch").join("keep-awake.monitor.log");
    if let Some(parent) = log.parent() {
        if fs::create_dir_all(parent).is_err() {
            std::process::exit(1);
        }
    }

    let python = python_executable();
    let (_script, keep_args) = keep_awake_args(&repo, seconds);
    let mut keep = match Command::new(&python)
        .args(&keep_args)
        .current_dir(&repo)
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
    {
        Ok(child) => child,
        Err(_) => std::process::exit(1),
    };
    let stdout = keep.stdout.take().expect("keep-awake stdout");
    let mut lines = BufReader::new(stdout).lines();
    let mut helper_pid = keep.id();
    while let Some(Ok(line)) = lines.next() {
        if let Some(pid) = parse_keep_awake_pid(&line) {
            helper_pid = pid;
            break;
        }
    }
    thread::spawn(move || {
        for _line in lines.flatten() {}
    });

    let mon_args = monitor_args(&repo, helper_pid, &log);
    let monitor = match Command::new(&python)
        .args(&mon_args)
        .current_dir(&repo)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
    {
        Ok(child) => child,
        Err(_) => {
            let _ = keep.kill();
            std::process::exit(1);
        }
    };

    if let Err(_) = ui::run(keep, monitor, helper_pid) {
        std::process::exit(1);
    }
}
