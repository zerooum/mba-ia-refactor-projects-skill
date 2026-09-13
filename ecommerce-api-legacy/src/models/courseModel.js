function toCourse(row) {
    return row && { id: row.id, title: row.title, price: row.price, active: row.active === 1 };
}

class CourseModel {
    constructor(db) {
        this.db = db;
    }

    async findActiveById(id, db = this.db) {
        return toCourse(await db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]));
    }

    async listAll(db = this.db) {
        const rows = await db.all('SELECT id, title, price, active FROM courses ORDER BY id', []);
        return rows.map(toCourse);
    }
}

module.exports = { CourseModel };
