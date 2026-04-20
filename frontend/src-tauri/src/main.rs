#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandChild;
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
    // Backend stoppen bevor der NSIS-Installer die sidecar-.exe überschreibt
    if let Some(mut child) = app.state::<BackendProcess>().0.lock().unwrap().take() {
        let _ = child.kill();
    }
    let updater = app.updater().map_err(|e| e.to_string())?;
    if let Some(update) = updater.check().await.map_err(|e| e.to_string())? {
        update.download_and_install(|_, _| {}, || {}).await.map_err(|e| e.to_string())?;
    }
    Ok(())
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
                let sidecar = app.shell().sidecar("handover-backend")
                    .map_err(|e| format!("Sidecar nicht gefunden: {}", e))?;

                let (mut rx, child) = sidecar.spawn()
                    .map_err(|e| format!("Sidecar konnte nicht gestartet werden: {}", e))?;

                *app.state::<BackendProcess>().0.lock().unwrap() = Some(child);

                // Stdout/Stderr-Receiver im Hintergrund leeren, sonst blockiert der Prozess
                tauri::async_runtime::spawn(async move {
                    while let Some(_) = rx.recv().await {}
                });

                // Warten bis Backend bereit
                std::thread::sleep(std::time::Duration::from_millis(3000));
                eprintln!("[HandOver] Backend (Sidecar) gestartet.");
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
