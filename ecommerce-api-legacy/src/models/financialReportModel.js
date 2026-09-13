// 1 query no lugar de 1 + C + 2E. LEFT JOIN preserva curso sem matrícula e
// matrícula sem usuário/pagamento; o subselect pega o 1º pagamento da matrícula.
const REPORT_SQL = `
    SELECT c.id     AS course_id,
           c.title  AS course_title,
           e.id     AS enrollment_id,
           u.id     AS user_id,
           u.name   AS user_name,
           p.amount AS payment_amount,
           p.status AS payment_status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u       ON u.id = e.user_id
      LEFT JOIN payments p    ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
     ORDER BY c.id, e.id`;

class FinancialReportModel {
    constructor(db) {
        this.db = db;
    }

    async listCoursesWithEnrollments(db = this.db) {
        const rows = await db.all(REPORT_SQL, []);
        const courses = new Map();

        for (const row of rows) {
            if (!courses.has(row.course_id)) {
                courses.set(row.course_id, { id: row.course_id, title: row.course_title, enrollments: [] });
            }
            if (row.enrollment_id === null) continue;

            courses.get(row.course_id).enrollments.push({
                id: row.enrollment_id,
                student: row.user_id === null ? null : { id: row.user_id, name: row.user_name },
                payment: row.payment_status === null ? null : { amount: row.payment_amount, status: row.payment_status },
            });
        }
        return [...courses.values()];
    }
}

module.exports = { FinancialReportModel };
