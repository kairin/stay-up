//! Bounded, read-only presentation of existing process output and log files.

use std::fs::File;
use std::io::{self, Read, Seek, SeekFrom};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;

pub const LIMIT: usize = 48 * 1024;

#[derive(Clone, Default)]
pub struct Output(Arc<Mutex<Vec<u8>>>);

impl Output {
    pub fn append(&self, bytes: &[u8]) {
        let mut buffer = self.0.lock().unwrap_or_else(|e| e.into_inner());
        if bytes.len() >= LIMIT {
            buffer.clear();
            let start = boundary_after(bytes, bytes.len() - LIMIT);
            buffer.extend_from_slice(&bytes[start..]);
            return;
        }
        let required = buffer.len().saturating_add(bytes.len());
        if required > LIMIT {
            let remove = required - LIMIT;
            let start = boundary_after(&buffer, remove);
            buffer.drain(..start);
        }
        buffer.extend_from_slice(bytes);
    }

    fn replace(&self, bytes: &[u8]) {
        let mut buffer = self.0.lock().unwrap_or_else(|e| e.into_inner());
        buffer.clear();
        buffer.extend_from_slice(bytes);
        trim_tail(&mut buffer);
    }

    pub fn text(&self) -> String {
        let buffer = self.0.lock().unwrap_or_else(|e| e.into_inner());
        String::from_utf8_lossy(&buffer).replace('\0', "�").replace("\r\n", "\n").replace('\n', "\r\n")
    }

    pub fn drain(&self, mut reader: impl Read + Send + 'static) {
        let output = self.clone();
        thread::spawn(move || {
            let mut bytes = [0; 4096];
            loop {
                match reader.read(&mut bytes) {
                    Ok(0) => break,
                    Ok(count) => output.append(&bytes[..count]),
                    Err(error) if error.kind() == io::ErrorKind::Interrupted => continue,
                    Err(error) => {
                        output.append(format!("\n[Output read failed: {error}]\n").as_bytes());
                        break;
                    }
                }
            }
        });
    }
}

fn trim_tail(buffer: &mut Vec<u8>) {
    if buffer.len() <= LIMIT {
        return;
    }
    let start = boundary_after(buffer, buffer.len() - LIMIT);
    buffer.drain(..start);
}

fn boundary_after(bytes: &[u8], start: usize) -> usize {
    let mut start = start.min(bytes.len());
    if let Some(newline) = bytes[start..].iter().position(|byte| *byte == b'\n') {
        start += newline + 1;
    } else {
        while start < bytes.len() && (bytes[start] & 0xc0) == 0x80 {
            start += 1;
        }
    }
    start
}

fn read_tail(path: &PathBuf) -> io::Result<Vec<u8>> {
    let mut file = File::open(path)?;
    let len = file.metadata()?.len();
    let offset = len.saturating_sub(LIMIT as u64);
    file.seek(SeekFrom::Start(offset))?;
    let mut bytes = Vec::new();
    file.take(LIMIT as u64).read_to_end(&mut bytes)?;
    if offset > 0 {
        if let Some(newline) = bytes.iter().position(|b| *b == b'\n') {
            bytes.drain(..=newline);
        }
    }
    Ok(bytes)
}

pub struct Views {
    pub helper: Output,
    pub helper_errors: Output,
    pub monitor_output: Output,
    pub monitor_errors: Output,
    pub log: Output,
    pub log_path: PathBuf,
    stop: Arc<AtomicBool>,
}

impl Views {
    pub fn new(log_path: PathBuf) -> Self {
        let views = Self {
            helper: Output::default(),
            helper_errors: Output::default(),
            monitor_output: Output::default(),
            monitor_errors: Output::default(),
            log: Output::default(),
            log_path,
            stop: Arc::new(AtomicBool::new(false)),
        };
        let path = views.log_path.clone();
        let output = views.log.clone();
        let stop = views.stop.clone();
        thread::spawn(move || {
            while !stop.load(Ordering::Relaxed) {
                match read_tail(&path) {
                    Ok(bytes) => output.replace(&bytes),
                    Err(error) => output.replace(format!("[Log view unavailable: {error}]\n").as_bytes()),
                }
                thread::sleep(Duration::from_secs(1));
            }
        });
        views
    }

    pub fn helper_text(&self) -> String {
        with_streams(self.helper.text(), self.helper_errors.text())
    }

    pub fn monitor_text(&self) -> String {
        with_streams(
            self.log.text(),
            with_streams(self.monitor_output.text(), self.monitor_errors.text()),
        )
    }
}

fn with_streams(mut text: String, streams: String) -> String {
    if !streams.is_empty() {
        if !text.is_empty() && !text.ends_with("\r\n") {
            text.push_str("\r\n");
        }
        text.push_str("\r\n--- Additional output / errors ---\r\n");
        text.push_str(&streams);
    }
    text
}

impl Drop for Views {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn output_is_bounded_even_for_a_large_chunk() {
        let output = Output::default();
        output.append(b"old");
        output.append(&vec![b'x'; LIMIT * 2]);
        output.append(b"new");
        let text = output.text();
        assert_eq!(text.len(), LIMIT);
        assert!(text.ends_with("new"));
    }

    #[test]
    fn split_utf8_and_newlines_are_preserved() {
        let output = Output::default();
        output.append(&[0xe2, 0x82]);
        output.append(&[0xac, b'\r', b'\n', b'x', b'\n']);
        assert_eq!(output.text(), "€\r\nx\r\n");
    }

    #[test]
    fn reading_log_never_changes_its_bytes() {
        let path = std::env::temp_dir().join(format!("stay-watch-tail-test-{}.log", std::process::id()));
        let mut content = vec![b'x'; LIMIT + 100];
        content.extend_from_slice(b"\nrecord one\nrecord two\n");
        std::fs::write(&path, &content).unwrap();
        assert_eq!(read_tail(&path).unwrap(), b"record one\nrecord two\n");
        assert_eq!(std::fs::read(&path).unwrap(), content);
        std::fs::write(&path, b"new file\n").unwrap();
        assert_eq!(read_tail(&path).unwrap(), b"new file\n");
        std::fs::remove_file(&path).unwrap();
        assert!(read_tail(&path).is_err());
    }
}
