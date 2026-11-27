
use crate::errors::AppError;
use crate::models::Topic;
use rusqlite::Connection;

pub fn list(conn: &Connection, limit: i64, offset: i64) -> Result<Vec<Topic>, AppError> {
    let mut statement = conn.prepare(
        "
            SELECT 
                id,
                name,
                created_at,
                is_active
            FROM topics 
            ORDER BY created_at DESC LIMIT ?1 OFFSET?2
        ",
    )?;
    let rows = statement.query_map([limit, offset], |row| {
        Ok(Topic {
            id: row.get(0)?,
            name: row.get(1)?,
            created_at: row.get(2)?,
            is_active: row.get::<_, i64>(3)? != 0,
        })
    })?;
    
    let mut topics = Vec::new();
    for t in rows {
        topics.push(t?);
    }
    Ok(topics)
} // end list 

pub fn add(conn: &Connection, name: &str) -> Result<Topic, AppError> {
    let topic = conn.query_row(
        "INSERT INTO topics (name, created_at, is_active)
        VALUES (?1, unixepoch(), 1)
        RETURNING id, created_at",
        [name],
        |row| {
            Ok(Topic {
                id: row.get(0)?,
                name: name.to_string(),
                created_at: row.get(1)?,
                is_active: true,
            })
        },
    )?;
    Ok(topic)
} //end add 

pub fn delete(conn: &Connection, id: i64) -> Result<(), AppError> {
    let affected = conn.execute("DELETE FROM topics WHERE id = ?1", [id])?;
    if affected == 0 {
        return Err(AppError::NotFound);
    }
    Ok(())
} //end delete 

// TESTS
#[cfg(test)]

mod tests {
    use super::*;
    use crate::db::Db;
    use crate::errors::AppError;

    fn conn() -> Connection {
        Db::test_connection()
    }

    #[test]
    fn list_is_empty_at_start() {
        let conn = conn();
        assert!(list(&conn, 10, 0).unwrap().is_empty());
    }

    #[test]
    fn add_then_list() {
        let conn = conn();
        let topic = add(&conn, "rust").unwrap();
        assert_eq!(topic.name, "rust");
        assert!(topic.is_active);
        let all_topics = list(&conn,10, 0).unwrap();
        assert_eq!(all_topics.len(), 1);
        assert_eq!(all_topics[0].id, topic.id);
    }

    #[test]
    fn add_rejects_duplicate_name() {
        let conn = conn();
        add(&conn, "rust").unwrap();
        assert!(add(&conn, "rust").is_err());
    }

    #[test]
    fn delete_removes_row() {
        let conn = conn();
        let topic = add(&conn, "rust").unwrap();
        delete(&conn, topic.id).unwrap();
        assert!(list(&conn, 10, 0).unwrap().is_empty());
    }

    #[test]
    fn delete_missing_returns_not_found() {
        let conn = conn();
        let error = delete(&conn, 1999).unwrap_err();
        assert!(matches!(error, AppError::NotFound));
    }
}