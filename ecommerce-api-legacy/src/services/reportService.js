const { PAYMENT_STATUS, UNKNOWN_STUDENT } = require('../models/domain');

class ReportService {
  constructor({ courses }) {
    this.courses = courses;
  }

  async financialReport() {
    const rows = await this.courses.listEnrollmentsWithPayments();
    const byCourse = new Map();
    for (const row of rows) {
      if (!byCourse.has(row.course_id)) {
        byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
      }
      if (row.enrollment_id === null) continue;
      const entry = byCourse.get(row.course_id);
      if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
      entry.students.push({
        student: row.user_id !== null ? row.student : UNKNOWN_STUDENT,
        paid: row.payment_id !== null ? row.amount : 0,
      });
    }
    return [...byCourse.values()];
  }
}

module.exports = ReportService;
