
use crate::db::Db;
use crate::errors::AppError;
use crate::models::Topic;
use crate::repository::topics as repo;
use tauri::State;

#[tauri::command]
pub fn list_topics(db: State<Db>, limit: Option<i64>, offset: Option<i64>) -> Result<Vec<Topic>, AppError> {
    let conn = db.0.lock().map_err(|_| AppError::LockPoisoned)?;
    repo::list(&conn, limit.unwrap_or(10), offset.unwrap_or(0))
}

#[tauri::command]
pub fn add_topic(db: State<Db>, name: String) -> Result<Topic, AppError> {
    let conn = db.0.lock().map_err(|_| AppError::LockPoisoned)?;
    repo::add(&conn, &name)
}

#[tauri::command]
pub fn delete_topic(db: State<Db>, id: i64) -> Result<(), AppError> {
    let conn = db.0.lock().map_err(|_| AppError::LockPoisoned)?;
    repo::delete(&conn, id)
}