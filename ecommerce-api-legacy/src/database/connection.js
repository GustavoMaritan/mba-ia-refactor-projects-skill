const sqlite3 = require('sqlite3');

// Wrapper do sqlite3 com Promises e transação serializada.
class Database {
  constructor(file) {
    this.raw = new sqlite3.Database(file);
    this.txQueue = Promise.resolve();
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.run(sql, params, function onRun(err) {
        if (err) return reject(err);
        resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
  }

  // Uma conexão só: as transações entram numa fila para não se misturarem.
  transaction(work) {
    const exec = async () => {
      await this.run('BEGIN');
      try {
        const result = await work();
        await this.run('COMMIT');
        return result;
      } catch (err) {
        await this.run('ROLLBACK');
        throw err;
      }
    };
    const next = this.txQueue.then(exec, exec);
    this.txQueue = next.catch(() => {});
    return next;
  }

  close() {
    return new Promise((resolve, reject) => this.raw.close((err) => (err ? reject(err) : resolve())));
  }
}

module.exports = Database;
