use std::sync::Mutex;
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIcon, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Emitter, Manager, WindowEvent};

#[derive(Default)]
struct AppState {
    latest_pushed_item_id: Mutex<Option<i64>>,
}

struct TrayState {
    _icon: TrayIcon,
}

#[tauri::command]
fn set_latest_pushed_item(state: tauri::State<AppState>, item_id: i64) -> Result<(), String> {
    let mut lock = state
        .latest_pushed_item_id
        .lock()
        .map_err(|_| "failed to lock latest item state".to_string())?;
    *lock = Some(item_id);
    Ok(())
}

#[tauri::command]
fn get_latest_pushed_item(state: tauri::State<AppState>) -> Result<Option<i64>, String> {
    let lock = state
        .latest_pushed_item_id
        .lock()
        .map_err(|_| "failed to read latest item state".to_string())?;
    Ok(*lock)
}

fn show_main_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
    }
}

fn setup_tray(app: &AppHandle) -> Result<TrayIcon, Box<dyn std::error::Error>> {
    let open = MenuItem::with_id(app, "open-main", "打开主面板", true, None::<&str>)?;
    let push_now = MenuItem::with_id(app, "push-now", "立即推送一条", true, None::<&str>)?;
    let open_latest = MenuItem::with_id(app, "open-latest", "打开最新推送", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit-app", "退出", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&open, &push_now, &open_latest, &quit])?;

    let app_handle = app.clone();
    let tray = TrayIconBuilder::new()
        .menu(&menu)
        .tooltip("Knowledge Push Assistant")
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "open-main" => show_main_window(app),
            "push-now" => {
                show_main_window(app);
                let _ = app.emit("tray-push-now", ());
            }
            "open-latest" => {
                show_main_window(app);
                let _ = app.emit("tray-open-latest", ());
            }
            "quit-app" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                show_main_window(tray.app_handle());
            }
        })
        .build(&app_handle)?;
    Ok(tray)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AppState::default())
        .setup(|app| {
            let tray = setup_tray(app.handle())?;
            app.manage(TrayState { _icon: tray });
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_sql::Builder::default().build())
        .invoke_handler(tauri::generate_handler![
            set_latest_pushed_item,
            get_latest_pushed_item
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
