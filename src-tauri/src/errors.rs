
use serde::Serialize;
use std::fmt;

#[derive(Debug)]
pub enum AppError {
    Database(rusqlite::Error), // Raw DB error, never displayed as-is
    LockPoisoned,
    NotFound,
    Validation(String), // For validating empty, long, etc., names
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::Database(e) => write!(f, "database error: {}", e),
            AppError::LockPoisoned => write!(f, "database lock poisoned"),
            AppError::NotFound => write!(f,"resource not found"),
            AppError::Validation(msg) => write!(f,"invalid input: {}", msg),
        }
    }
}

impl std::error::Error for AppError {} 

impl From<rusqlite::Error> for AppError {
    fn from(e: rusqlite::Error) -> Self {
        AppError::Database(e)
    }
}

impl Serialize for AppError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where S: serde::Serializer {
        let (code,msg) = match self {
            AppError::Database(e) => {
                if cfg!(debug_assertions) {
                    ("DB_ERROR", e.to_string())
                } else {
                    ("DB_ERROR", "internal error".to_string())
                }
            }
            AppError::LockPoisoned => ("LOCK", "resource busy".to_string()),
            AppError::NotFound => ("NOT_FOUND", "resource not found".to_string()),
            AppError::Validation(m) => ("VALIDATION", m.clone()),
        };
        serializer.serialize_str(&format!("{}: {}", code, msg))
    }
}