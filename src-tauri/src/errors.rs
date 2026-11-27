
use serde::Serialize;
use std::fmt;

#[derive(Debug)]
pub enum AppError {
    Database(rusqlite::Error),
    LockPoisoned,
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::Database(e) => write!(f, "database error: {}", e),
            AppError::LockPoisoned => write!(f, "database lock poisoned"),
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
    where 
    S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}