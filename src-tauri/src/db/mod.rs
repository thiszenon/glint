
mod schema;

use crate::errors::AppError;
use rusqlite::Connection;
use std::path::Path;
use std::sync::Mutex;

pub struct Db(pub Mutex<Connection>);

impl Db {
    pub fn open(path: &Path) -> Result<Self, AppError> {
        let conn = Connection::open(path)?;
        conn.execute_batch(schema::SCHEMA)?;
        Ok(Db(Mutex::new(conn)))
    }
}

#[cfg(test)]
impl Db {
    pub fn test_connection() -> Connection {
        let conn = Connection::open_in_memory().expect("in-memory db");
        conn.execute_batch(schema::SCHEMA).expect("schema");
        conn 
    }
}