#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::fs::OpenOptions;
use std::io::Write;
use std::net::TcpStream;
use std::sync::Mutex;
use std::time::{Duration, Instant};
use tauri::Manager;
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_updater::UpdaterExt;

struct BackendProcess(Mutex<Option<CommandChild>>);

#[tauri::command]
async fn check_for_updates(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    let updater = app.updater().map_err(|e| e.to_string())?;
    match updater.check().await {
        Ok(Some(update)) => Ok(serde_json::json!({
            "available": true,
            "version": update.version,
            "body": update.body,
            "date": update.date.map(|d| d.to_string()),
        })),
        Ok(None) => Ok(serde_json::json!({ "available": false })),
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
async fn install_update(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(child) = app.state::<BackendProcess>().0.lock().unwrap().take() {
        let _ = child.kill();
    }
    let updater = app.updater().map_err(|e| e.to_string())?;
    if let Some(update) = updater.check().await.map_err(|e| e.to_string())? {
        update.download_and_install(|_, _| {}, || {}).await.map_err(|e| e.to_string())?;
    }
    Ok(())
}

// Pollt Port 8000 bis das Backend antwortet oder der Timeout abläuft.
fn wait_for_backend(timeout_secs: u64) -> bool {
    let addr = "127.0.0.1:8000".parse().unwrap();
    let deadline = Duration::from_secs(timeout_secs);
    let start = Instant::now();
    loop {
        if TcpStream::connect_timeout(&addr, Duration::from_millis(200)).is_ok() {
            return true;
        }
        if start.elapsed() >= deadline {
            return false;
        }
        std::thread::sleep(Duration::from_millis(300));
    }
}

fn kill_backend(app: &tauri::AppHandle) {
    if let Some(child) = app.state::<BackendProcess>().0.lock().unwrap().take() {
        let _ = child.kill();
    }
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![check_for_updates, install_update])
        .setup(|app| {
            #[cfg(not(debug_assertions))]
            {
                // Log-Datei im App-Verzeichnis öffnen
                let log_path = app.path().app_log_dir().ok().map(|p| {
                    let _ = std::fs::create_dir_all(&p);
                    p.join("handover-backend.log")
                });

                let sidecar = app
                    .shell()
                    .sidecar("handover-backend")
                    .map_err(|e| format!("Sidecar nicht gefunden: {e}"))?;

                let (mut rx, child) = sidecar
                    .spawn()
                    .map_err(|e| format!("Sidecar konnte nicht gestartet werden: {e}"))?;

                *app.state::<BackendProcess>().0.lock().unwrap() = Some(child);

                // Backend-Output (stdout + stderr) in Log-Datei schreiben
                tauri::async_runtime::spawn(async move {
                    use tauri_plugin_shell::process::CommandEvent;
                    let mut log_file = log_path
                        .and_then(|p| OpenOptions::new().create(true).append(true).open(p).ok());
                    while let Some(event) = rx.recv().await {
                        let line = match event {
                            CommandEvent::Stdout(b) => String::from_utf8_lossy(&b).into_owned(),
                            CommandEvent::Stderr(b) => {
                                format!("[ERR] {}", String::from_utf8_lossy(&b))
                            }
                            CommandEvent::Error(e) => format!("[CRASH] {e}"),
                            _ => continue,
                        };
                        if let Some(f) = log_file.as_mut() {
                            let _ = writeln!(f, "{line}");
                        }
                    }
                });

                // Health-Check: bis zu 15 Sekunden auf Port 8000 warten
                if !wait_for_backend(15) {
                    app.dialog()
                        .message(
                            "Das Backend konnte nicht gestartet werden.\n\n\
                            Mögliche Ursachen:\n\
                            • Windows Defender hat handover-backend.exe blockiert\n\
                            • Port 8000 ist bereits durch eine andere Anwendung belegt\n\n\
                            Fehlerdetails in der Log-Datei:\n\
                            %APPDATA%\\com.shoriu.handover\\logs\\handover-backend.log",
                        )
                        .title("HandOver – Backend-Fehler")
                        .kind(tauri_plugin_dialog::MessageDialogKind::Error)
                        .blocking_show();
                    return Err("Backend nicht erreichbar".into());
                }
            }
            Ok(())
        })
        .on_window_event(|window, event| match event {
            // Fenster wird geschlossen → Backend sofort killen, bevor der
            // Prozess verschwindet, damit kein Sidecar verwaist zurueckbleibt.
            tauri::WindowEvent::CloseRequested { .. } | tauri::WindowEvent::Destroyed => {
                kill_backend(&window.app_handle());
            }
            _ => {}
        })
        .build(tauri::generate_context!())
        .expect("Fehler beim Starten der App")
        .run(|app_handle, event| {
            // Letzter Sicherheitsnetz-Hook: spaetestens beim App-Exit
            // (z.B. via Tray, Auto-Update-Restart) das Backend beenden.
            if let tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit = event {
                kill_backend(app_handle);
            }
        });
}
