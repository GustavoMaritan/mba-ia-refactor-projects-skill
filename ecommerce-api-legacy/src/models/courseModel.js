class CourseModel {
  constructor(db) {
    this.db = db;
  }

  findActiveById(id) {
    return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
  }

  // Uma query só para o relatório (antes: 1 + cursos + 2 x matrículas).
  // Uma linha por matrícula; cursos sem matrícula vêm com enrollment_id nulo.
  listEnrollmentsWithPayments() {
    return this.db.all(
      `SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
              u.id AS user_id, u.name AS student, p.id AS payment_id, p.amount, p.status
         FROM courses c
         LEFT JOIN enrollments e ON e.course_id = c.id
         LEFT JOIN users u ON u.id = e.user_id
         LEFT JOIN payments p ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
        ORDER BY c.id, e.id`,
    );
  }
}

module.exports = CourseModel;
