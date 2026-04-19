#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Child};
use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_updater::UpdaterExt;

struct BackendProcess(Mutex<Option<Child>>);

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
    // Backend stoppen bevor der NSIS-Installer handover-backend.exe überschreibt
    if let Some(mut child) = app.state::<BackendProcess>().0.lock().unwrap().take() {
        let _ = child.kill();
    }
    let updater = app.updater().map_err(|e| e.to_string())?;
    if let Some(update) = updater.check().await.map_err(|e| e.to_string())? {
        update.download_and_install(|_, _| {}, || {}).await.map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn find_backend() -> Option<std::path::PathBuf> {
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()));

    let candidates = vec![
        // NSIS installer: neben der .exe
        exe_dir.as_ref().map(|d| d.join("handover-backend.exe")),
        // Resources Unterordner
        exe_dir.as_ref().map(|d| d.join("resources").join("handover-backend.exe")),
        // AppData Local (NSIS user install)
        dirs_next_path("handover-backend.exe"),
    ];

    for path in candidates.into_iter().flatten() {
        if path.exists() {
            return Some(path);
        }
    }
    None
}

fn dirs_next_path(filename: &str) -> Option<std::path::PathBuf> {
    // Suche auch im AppData\Local\handover Ordner
    if let Ok(exe) = std::env::current_exe() {
        if let Some(parent) = exe.parent() {
            let candidate = parent.join(filename);
            if candidate.exists() {
                return Some(candidate);
            }
        }
    }
    None
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![check_for_updates, install_update])
        .setup(|app| {
            #[cfg(not(debug_assertions))]
            {
                // Alle möglichen Pfade sammeln
                let exe_dir = std::env::current_exe()
                    .ok()
                    .and_then(|p| p.parent().map(|p| p.to_path_buf()));

                let resource_dir = app.path().resource_dir().ok();

                let mut candidates: Vec<std::path::PathBuf> = Vec::new();

                if let Some(ref d) = exe_dir {
                    candidates.push(d.join("handover-backend.exe"));
                    candidates.push(d.join("resources").join("handover-backend.exe"));
                    candidates.push(d.join("_up_").join("handover-backend.exe"));
                }
                if let Some(ref d) = resource_dir {
                    candidates.push(d.join("handover-backend.exe"));
                }

                // Log alle Pfade für Debugging
                for path in &candidates {
                    eprintln!("[HandOver] Suche Backend: {:?} — exists={}", path, path.exists());
                }

                let mut started = false;
                for path in &candidates {
                    if path.exists() {
                        eprintln!("[HandOver] Starte Backend: {:?}", path);
                        let mut cmd = Command::new(path);

                        // Windows: kein Konsolenfenster anzeigen
                        #[cfg(target_os = "windows")]
                        {
                            use std::os::windows::process::CommandExt;
                            cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
                        }

                        match cmd.spawn() {
                            Ok(child) => {
                                *app.state::<BackendProcess>().0.lock().unwrap() = Some(child);
                                // Warten bis Backend bereit
                                std::thread::sleep(std::time::Duration::from_millis(3000));
                                started = true;
                                eprintln!("[HandOver] Backend gestartet!");
                                break;
                            }
                            Err(e) => eprintln!("[HandOver] Fehler: {}", e),
                        }
                    }
                }

                if !started {
                    eprintln!("[HandOver] WARNUNG: Backend nicht gefunden!");
                    eprintln!("[HandOver] exe_dir={:?}", exe_dir);
                    eprintln!("[HandOver] resource_dir={:?}", resource_dir);
                }
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let state = window.state::<BackendProcess>();
                let child = state.0.lock().unwrap().take();
                if let Some(mut c) = child {
                    let _ = c.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("Fehler beim Starten der App");
}
