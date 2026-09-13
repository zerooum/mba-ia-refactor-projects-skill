const STATEMENTS = [
    // FK no SQLite só vale com o pragma ligado, por conexão
    'PRAGMA foreign_keys = ON',
    `CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass TEXT NOT NULL
    )`,
    `CREATE TABLE courses (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER NOT NULL
    )`,
    `CREATE TABLE enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
        UNIQUE (user_id, course_id)
    )`,
    `CREATE TABLE payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE RESTRICT,
        amount REAL NOT NULL,
        status TEXT NOT NULL
    )`,
    `CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT NOT NULL,
        created_at DATETIME NOT NULL
    )`,
];

async function createSchema(db) {
    for (const sql of STATEMENTS) {
        await db.run(sql);
    }
}

module.exports = { createSchema };
