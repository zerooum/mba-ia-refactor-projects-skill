// Formato público das respostas JSON (contrato HTTP original).
const checkoutResponse = ({ enrollmentId }) => ({ msg: 'Sucesso', enrollment_id: enrollmentId });

const financialReportResponse = (courses) => courses.map((course) => ({
    course: course.title,
    revenue: course.revenue,
    students: course.students.map((s) => ({ student: s.name, paid: s.paid })),
}));

module.exports = { checkoutResponse, financialReportResponse };
