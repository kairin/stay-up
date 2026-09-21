//! Command helpers for the first stay-watch launcher.

use std::path::{Path, PathBuf};

/// Format elapsed seconds as HH:MM:SS.
pub fn format_elapsed(seconds: u64) -> String {
    let hours = seconds / 3600;
    let minutes = (seconds % 3600) / 60;
    let rest = seconds % 60;
    format!("{:02}:{:02}:{:02}", hours, minutes, rest)
}

/// Read the helper PID from a keep-awake status line.
pub fn parse_keep_awake_pid(line: &str) -> Option<u32> {
    let rest = line.strip_prefix("PID ")?;
    let number = rest.split(':').next()?;
    number.trim().parse().ok()
}

/// Reset the idle timer only after a later last-input tick.
pub fn should_reset_idle(have_sample: bool, previous: u32, current: u32) -> bool {
    have_sample && previous != current
}
pub fn parse_seconds(args: &[String]) -> Result<Option<u64>, String> {
    let mut value = None;
    let mut index = 1;
    while index < args.len() {
        if args[index] == "--seconds" {
            let raw = args.get(index + 1).ok_or("--seconds needs a number")?;
            let parsed: u64 = raw.parse().map_err(|_| "--seconds must be a number")?;
            value = Some(parsed);
            index += 2;
            continue;
        }
        return Err(format!("unknown argument: {}", args[index]));
    }
    Ok(value)
}

/// Build the keep-awake command. The Rust program does not make power requests.
pub fn keep_awake_args(repo: &Path, seconds: Option<u64>) -> (PathBuf, Vec<String>) {
    let script = repo.join("scripts").join("keep-awake.py");
    let mut args = vec![script.to_string_lossy().into_owned()];
    if let Some(limit) = seconds {
        args.push("--seconds".to_string());
        args.push(limit.to_string());
    }
    (script, args)
}

/// Build the monitor command. The monitor follows the keep-awake process ID.
pub fn monitor_args(repo: &Path, helper_pid: u32, log: &Path) -> Vec<String> {
    vec![
        repo.join("scripts")
            .join("monitor-helper.py")
            .to_string_lossy()
            .into_owned(),
        helper_pid.to_string(),
        "--interval".to_string(),
        "60".to_string(),
        "--log".to_string(),
        log.to_string_lossy().into_owned(),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn format_elapsed_zero() {
        assert_eq!(format_elapsed(0), "00:00:00");
    }

    #[test]
    fn format_elapsed_minutes_and_seconds() {
        assert_eq!(format_elapsed(65), "00:01:05");
    }

    #[test]
    fn format_elapsed_hour() {
        assert_eq!(format_elapsed(3661), "01:01:01");
    }

    #[test]
    fn keep_awake_args_without_limit() {
        let repo = PathBuf::from("D:/Apps/stay-up");
        let (script, args) = keep_awake_args(&repo, None);
        assert_eq!(script, repo.join("scripts").join("keep-awake.py"));
        assert_eq!(
            args,
            vec![repo
                .join("scripts")
                .join("keep-awake.py")
                .to_string_lossy()
                .into_owned()]
        );
    }

    #[test]
    fn keep_awake_args_with_limit() {
        let repo = PathBuf::from("D:/Apps/stay-up");
        let (_script, args) = keep_awake_args(&repo, Some(3));
        assert_eq!(args[1], "--seconds");
        assert_eq!(args[2], "3");
    }

    #[test]
    fn parse_seconds_reads_limit() {
        let args = vec![
            "stay-watch".to_string(),
            "--seconds".to_string(),
            "3".to_string(),
        ];
        assert_eq!(parse_seconds(&args).unwrap(), Some(3));
    }

    #[test]
    fn parse_seconds_rejects_unknown() {
        let args = vec!["stay-watch".to_string(), "--help".to_string()];
        assert!(parse_seconds(&args).is_err());
    }

    #[test]
    fn parse_keep_awake_pid_from_status_line() {
        let line = "PID 27628: keep-awake active. Ctrl+C stops it.";
        assert_eq!(parse_keep_awake_pid(line), Some(27628));
    }

    #[test]
    fn monitor_args_include_pid_and_log() {
        let repo = PathBuf::from("D:/Apps/stay-up");
        let log = PathBuf::from("D:/Apps/stay-up/logs/keep-awake.monitor.log");
        let args = monitor_args(&repo, 12345, &log);
        assert_eq!(args[1], "12345");
        assert_eq!(args[3], "60");
        assert!(args[5].ends_with("keep-awake.monitor.log"));
    }

    #[test]
    fn idle_timer_does_not_reset_on_first_sample() {
        assert!(!should_reset_idle(false, 0, 100));
    }

    #[test]
    fn idle_timer_resets_when_last_input_tick_changes() {
        assert!(should_reset_idle(true, 100, 140));
    }

    #[test]
    fn idle_timer_holds_when_last_input_tick_is_unchanged() {
        assert!(!should_reset_idle(true, 140, 140));
    }
}
