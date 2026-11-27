
use serde:: {Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Topic {
    pub id: i64,
    pub name: String,
    pub created_at: i64,
    pub is_active: bool,
}