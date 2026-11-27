
use crate::errors::AppError;
use crate::models::Topic;
use rusqlite::Connection;

pub fn list(conn: &Connection) -> Result<Vec<Topic>, AppError> {
    let mut statement = conn.prepare(
        "
            SELECT 
                id,
                name,
                created_at,
                is_active
            FROM topics 
            ORDER BY created_at DESC
        ",
    )?;
    let rows = statement.query_map([], |row| {
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
    conn.execute(
        "   INSERT INTO topics
                (name, created_at, is_active)
            VALUES 
                (?1, unixepoch(),1)
        ",
        [name],
    )?;

    let id = conn.last_insert_rowid();
    let created_at: i64 = conn.query_row(
        "SELECT created_at FROM topics WHERE id = ?1",
        [id],
        |r| r.get(0),
    )?;
    Ok(Topic {
        id,
        name: name.to_string(),
        created_at,
        is_active: true,
    })
} //end add 

pub fn delete(conn: &Connection, id: i64) -> Result<(), AppError> {
    conn.execute("DELETE FROM topics WHERE id = ?1", [id])?;
    Ok(())
} //end delete 

// TESTS
#[cfg(test)]

mod tests {
    use super::*;
    use crate::db::Db;

    fn conn() -> Connection {
        Db::test_connection()
    }

    #[test]
    fn list_is_empty_at_start() {
        let conn = conn();
        assert!(list(&conn).unwrap().is_empty());
    }

    #[test]
    fn add_then_list() {
        let conn = conn();
        let topic = add(&conn, "rust").unwrap();
        assert_eq!(topic.name, "rust");
        assert!(topic.is_active);
        let all_topics = list(&conn).unwrap();
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
        assert!(list(&conn).unwrap().is_empty());
    }
}