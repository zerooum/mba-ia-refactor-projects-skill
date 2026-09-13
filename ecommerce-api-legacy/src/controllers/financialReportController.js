const { PaymentStatus, UNKNOWN_STUDENT } = require('../models/constants');
const { persistenceFailure } = require('../models/errors');

class FinancialReportController {
    constructor({ financialReports }) {
        this.financialReports = financialReports;
    }

    // Receita soma só pagamentos PAID; `paid` mostra o valor do pagamento qualquer que seja o status.
    async generate() {
        const courses = await this.financialReports.listCoursesWithEnrollments()
            .catch(persistenceFailure('Erro DB'));

        return courses.map((course) => ({
            title: course.title,
            revenue: course.enrollments
                .filter((e) => e.payment && e.payment.status === PaymentStatus.PAID)
                .reduce((sum, e) => sum + e.payment.amount, 0),
            students: course.enrollments.map((e) => ({
                name: e.student ? e.student.name : UNKNOWN_STUDENT,
                paid: e.payment ? e.payment.amount : 0,
            })),
        }));
    }
}

module.exports = { FinancialReportController };
