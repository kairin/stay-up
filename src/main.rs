//! Launch the two Python helpers and show how long they run.

#![windows_subsystem = "windows"]

use std::env;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::mpsc::{self, Receiver};
use std::thread;

use std::os::windows::process::CommandExt;

mod output;
mod ui;

use output::{Output, Views};
use stay_watch::{keep_awake_args, monitor_args, parse_keep_awake_pid, parse_seconds};

const CREATE_NO_WINDOW: u32 = 0x0800_0000;
const HANDSHAKE_FRAGMENT_LIMIT: usize = 16 * 1024;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn python_executable() -> PathBuf {
    match Command::new("python")
        .creation_flags(CREATE_NO_WINDOW)
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

fn capture_helper_stdout(
    stdout: std::process::ChildStdout,
    output: Output,
    errors: Output,
) -> Receiver<u32> {
    let (sender, receiver) = mpsc::channel();
    thread::spawn(move || {
        let mut reader = BufReader::new(stdout);
        let mut fragment = Vec::with_capacity(256);
        let mut sent_pid = false;
        let mut sender = Some(sender);
        loop {
            let consumed = match reader.fill_buf() {
                Ok(chunk) if chunk.is_empty() => break,
                Ok(chunk) => {
                    output.append(chunk);
                    if !sent_pid {
                        if fragment.len() < HANDSHAKE_FRAGMENT_LIMIT {
                            let available = HANDSHAKE_FRAGMENT_LIMIT - fragment.len();
                            fragment.extend_from_slice(&chunk[..chunk.len().min(available)]);
                        }
                        while let Some(end) = fragment.iter().position(|byte| *byte == b'\n') {
                            let line: Vec<u8> = fragment.drain(..=end).collect();
                            let text = String::from_utf8_lossy(&line);
                            if let Some(pid) = parse_keep_awake_pid(text.trim_end_matches(['\r', '\n'])) {
                                if let Some(sender) = sender.take() {
                                    let _ = sender.send(pid);
                                }
                                sent_pid = true;
                                break;
                            }
                        }
                        if fragment.len() == HANDSHAKE_FRAGMENT_LIMIT
                            && !fragment.contains(&b'\n')
                        {
                            fragment.clear();
                        }
                    }
                    chunk.len()
                }
                Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
                Err(error) => {
                    errors.append(format!("\r\n[stdout read failed: {error}]\r\n").as_bytes());
                    break;
                }
            };
            reader.consume(consumed);
        }
    });
    receiver
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
    let keep_script = repo.join("scripts").join("keep-awake.py");
    let monitor_script = repo.join("scripts").join("monitor-helper.py");
    if !keep_script.is_file() || !monitor_script.is_file() {
        std::process::exit(1);
    }

    let log = repo.join("logs").join("keep-awake.monitor.log");
    if let Some(parent) = log.parent() {
        if fs::create_dir_all(parent).is_err() {
            std::process::exit(1);
        }
    }

    let python = python_executable();
    let views = Views::new(log.clone());
    let (_script, keep_args) = keep_awake_args(&repo, seconds);
    let mut keep = match Command::new(&python)
        .creation_flags(CREATE_NO_WINDOW)
        .args(&keep_args)
        .current_dir(&repo)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(child) => child,
        Err(_) => std::process::exit(1),
    };
    let stdout = keep.stdout.take().expect("keep-awake stdout");
    let helper_pid_receiver = capture_helper_stdout(stdout, views.helper.clone(), views.helper_errors.clone());
    if let Some(stderr) = keep.stderr.take() {
        views.helper_errors.drain(stderr);
    }
    let helper_pid = helper_pid_receiver.recv().unwrap_or_else(|_| keep.id());

    let mon_args = monitor_args(&repo, helper_pid, &log);
    let mut monitor = match Command::new(&python)
        .creation_flags(CREATE_NO_WINDOW)
        .args(&mon_args)
        .current_dir(&repo)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(child) => child,
        Err(_) => {
            let _ = keep.kill();
            let _ = keep.wait();
            std::process::exit(1);
        }
    };
    if let Some(stdout) = monitor.stdout.take() {
        views.monitor_output.drain(stdout);
    }
    if let Some(stderr) = monitor.stderr.take() {
        views.monitor_errors.drain(stderr);
    }

    if let Err(_) = ui::run(keep, monitor, helper_pid, views) {
        std::process::exit(1);
    }
}
