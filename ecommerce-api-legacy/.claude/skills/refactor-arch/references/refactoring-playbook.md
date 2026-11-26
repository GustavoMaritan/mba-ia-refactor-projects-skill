# Playbook de refatoração

Transformações concretas, cada uma com antes/depois em Python e JavaScript. Aplique na ordem da Fase 3 (config → dados → models → services → controllers → rotas → middlewares → entry point) e valide ao final de cada camada quando possível.

| T | Transformação | Resolve |
|---|---|---|
| T1 | Extrair configuração para env | AP01, AP11, AP19 (porta) |
| T2 | Queries parametrizadas | AP02 |
| T3 | Extrair model/repository do God Class | AP03, AP09 |
| T4 | Extrair service layer | AP07, AP14, AP18 |
| T5 | Controller fino + rotas declarativas | AP03, AP07 |
| T6 | Error handler centralizado (+ T6b auth de admin) | AP16, AP06, AP04 |
| T7 | Composition root / injeção de dependência | AP08, AP09 |
| T8 | Eliminar N+1 | AP13 |
| T9 | Hash de senha seguro | AP05 |
| T10 | Transação em escrita multi-etapas | AP10 |
| T11 | Substituir APIs deprecated | AP17 |
| T12 | Callbacks → async/await | AP12 |
| T13 | Constantes nomeadas | AP19 |
| T14 | Serialização explícita sem dados sensíveis | AP06, AP14 |
| T15 | Validação na borda | AP15 |

---

## T1 — Extrair configuração para variáveis de ambiente

**Python — antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Python — depois** (`src/config/settings.py`)
```python
import os, secrets

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
```
**JS — antes**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```
**JS — depois** (`src/config/index.js`)
```js
module.exports = {
  port: Number(process.env.PORT) || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  databaseFile: process.env.DATABASE_FILE || ':memory:',
};
```
Documente as variáveis em um `.env.example` sem valores reais.

## T2 — Queries parametrizadas

**Python — antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```
**Python — depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
clauses.append("(nome LIKE ? OR descricao LIKE ?)"); params += [f"%{termo}%", f"%{termo}%"]
cursor.execute("SELECT * FROM produtos WHERE " + " AND ".join(clauses), params)
```
**JS — antes**
```js
db.all(`SELECT * FROM courses WHERE id = ${req.params.id}`, cb);
```
**JS — depois**
```js
const course = await db.get('SELECT * FROM courses WHERE id = ?', [id]);
```
Só concatene identificadores vindos de uma whitelist fixa no código, nunca valores.

## T3 — Extrair model/repository do God Class

**Python — antes** (`models.py` faz SQL + regra + formatação de tudo)
```python
def criar_pedido(usuario_id, itens):
    db = get_db(); cursor = db.cursor()
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
        ...
```
**Python — depois** (`src/models/produto_model.py`)
```python
class ProdutoModel:
    def __init__(self, db):
        self.db = db

    def find_by_id(self, produto_id):
        row = self.db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return dict(row) if row else None
```
**JS — antes**
```js
class AppManager { initDb() { /* schema+seed */ } setupRoutes(app) { /* rotas+SQL+regra */ } }
```
**JS — depois** (`src/models/courseModel.js`)
```js
class CourseModel {
  constructor(db) { this.db = db; }
  findActiveById(id) { return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]); }
  findAll() { return this.db.all('SELECT * FROM courses ORDER BY id'); }
}
module.exports = CourseModel;
```

## T4 — Extrair service layer

**Python — antes** (controller com regra e "notificações")
```python
resultado = models.criar_pedido(usuario_id, itens)
print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]))
print("ENVIANDO SMS: Seu pedido foi recebido!")
```
**Python — depois** (`src/services/pedido_service.py`)
```python
class PedidoService:
    def __init__(self, pedidos, produtos, notifier):
        self.pedidos, self.produtos, self.notifier = pedidos, produtos, notifier

    def criar(self, usuario_id, itens):
        total = 0
        for item in itens:
            produto = self.produtos.find_by_id(item["produto_id"])
            if produto is None:
                raise BusinessRuleError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise BusinessRuleError(f"Estoque insuficiente para {produto['nome']}")
            total += produto["preco"] * item["quantidade"]
        pedido_id = self.pedidos.create(usuario_id, itens, total)
        self.notifier.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}
```
**JS — antes** (regra de pagamento dentro da rota)
```js
app.post('/api/checkout', (req, res) => { let status = cc.startsWith("4") ? "PAID" : "DENIED"; /* + 4 callbacks */ });
```
**JS — depois** (`src/services/checkoutService.js`)
```js
class CheckoutService {
  constructor({ courses, users, enrollments, paymentGateway, db }) { Object.assign(this, { courses, users, enrollments, paymentGateway, db }); }
  async checkout({ name, email, password, courseId, card }) {
    const course = await this.courses.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');
    if (this.paymentGateway.charge(card, course.price) !== 'PAID') throw new BusinessError('Pagamento recusado');
    return this.db.transaction(async () => { /* user + enrollment + payment + audit */ });
  }
}
```

## T5 — Controller fino + rotas declarativas

**Python — antes**
```python
app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
def listar_produtos():
    try:
        produtos = models.get_todos_produtos()
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```
**Python — depois**
```python
# src/controllers/produto_controller.py
class ProdutoController:
    def __init__(self, service):
        self.service = service
    def listar(self):
        return jsonify({"dados": self.service.listar(), "sucesso": True}), 200

# src/views/routes.py
def register_routes(app, c):
    bp = Blueprint("api", __name__)
    bp.add_url_rule("/produtos", "listar_produtos", c.produtos.listar, methods=["GET"])
    app.register_blueprint(bp)
```
**JS — antes**
```js
app.delete('/api/users/:id', (req, res) => { this.db.run("DELETE ...", [req.params.id], () => res.send("ok")); });
```
**JS — depois**
```js
// src/controllers/userController.js
const remove = (userService) => async (req, res) => { await userService.delete(req.params.id); res.send('Usuário deletado.'); };
// src/routes/index.js
router.delete('/api/users/:id', asyncHandler(userController.remove));
```

## T6 — Error handler centralizado

**Python — antes**: `try/except Exception as e: return jsonify({"erro": str(e)}), 500` em todo handler.
**Python — depois** (`src/middlewares/error_handler.py`)
```python
class AppError(Exception):
    status = 400
    def __init__(self, message, payload=None):
        super().__init__(message); self.message = message; self.payload = payload or {}

class NotFoundError(AppError):
    status = 404

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, **err.payload}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```
**JS — antes**: `if (err) return res.status(500).send("Erro DB");` repetido; erros de callback ignorados.
**JS — depois** (`src/middlewares/errorHandler.js`)
```js
class AppError extends Error { constructor(message, status = 400) { super(message); this.status = status; } }
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
function errorHandler(err, req, res, next) {
  if (err instanceof AppError) return res.status(err.status).send(err.message);
  console.error(err);
  res.status(500).send('Erro interno');
}
module.exports = { AppError, asyncHandler, errorHandler };
```

### T6b — Autorização de rotas administrativas
**Python**
```python
def admin_required(settings):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            token = request.headers.get("X-Admin-Token", "")
            if not settings.ADMIN_TOKEN or not hmac.compare_digest(token, settings.ADMIN_TOKEN):
                return jsonify({"erro": "Acesso negado"}), 403
            return fn(*a, **kw)
        return wrapper
    return decorator
```
**JS**
```js
const requireAdmin = (token) => (req, res, next) =>
  token && req.get('X-Admin-Token') === token ? next() : res.status(403).send('Acesso negado');
```

## T7 — Composition root / injeção de dependência

**Python — antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
```
**Python — depois** (`src/app.py`)
```python
def create_app(settings=None):
    settings = settings or Settings()
    app = Flask(__name__)
    app.config.from_object(settings)
    database.init_app(app)                 # conexão por request em flask.g, fechada no teardown
    produtos = ProdutoModel(database.get_db)
    controllers = Controllers(produtos=ProdutoController(ProdutoService(produtos)))
    register_routes(app, controllers)
    register_error_handlers(app)
    return app
```
**JS — antes**
```js
let globalCache = {}; module.exports = { globalCache };   // estado compartilhado mutável
const manager = new AppManager(); manager.initDb(); manager.setupRoutes(app);
```
**JS — depois** (`src/app.js`)
```js
function createApp({ db, config }) {
  const cache = new MemoryCache();
  const checkoutService = new CheckoutService({ db, courses: new CourseModel(db), cache, paymentGateway: new FakePaymentGateway(config) });
  const app = express();
  app.use(express.json());
  app.use(buildRoutes({ checkoutController: checkoutController(checkoutService) }));
  app.use(errorHandler);
  return app;
}
```

## T8 — Eliminar N+1

**Python — antes**
```python
for row in rows:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Python — depois**
```python
placeholders = ",".join("?" * len(ids))
itens = db.execute(f"""SELECT i.*, p.nome AS produto_nome FROM itens_pedido i
                       LEFT JOIN produtos p ON p.id = i.produto_id
                       WHERE i.pedido_id IN ({placeholders}) ORDER BY i.id""", ids).fetchall()
# agrupa em memória por pedido_id
```
ORM: `Task.query.options(joinedload(Task.user), joinedload(Task.category))`; contagens com `func.count` + `group_by`.
**JS — antes**
```js
enrollments.forEach(enr => { db.get("SELECT name FROM users WHERE id = ?", [enr.user_id], (e, user) => {
  db.get("SELECT amount FROM payments WHERE enrollment_id = ?", [enr.id], ...) }) });
```
**JS — depois**
```js
const rows = await db.all(`SELECT c.id AS course_id, c.title, u.name, p.amount, p.status
  FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id, e.id`);
```

## T9 — Hash de senha seguro

**Python — antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
**Python — depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash
self.password = generate_password_hash(pwd)
def check_password(self, pwd): return check_password_hash(self.password, pwd)
```
**JS — antes**
```js
function badCrypto(pwd) { let h = ""; for (let i = 0; i < 10000; i++) h += Buffer.from(pwd).toString('base64').substring(0, 2); return h.substring(0, 10); }
```
**JS — depois**
```js
const crypto = require('crypto');
function hashPassword(pwd) {
  const salt = crypto.randomBytes(16).toString('hex');
  return `${salt}:${crypto.scryptSync(pwd, salt, 64).toString('hex')}`;
}
```
Nunca aceite senha padrão fixa: gere uma aleatória ou exija o campo.

## T10 — Transação em escrita multi-etapas

**Python — antes**: `INSERT pedidos`, `INSERT itens`, `UPDATE estoque` e só um `commit()` no fim, sem rollback.
**Python — depois**
```python
with db:   # sqlite3: commit no sucesso, rollback em exceção
    pedido_id = db.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)", (uid, total)).lastrowid
    db.executemany("INSERT INTO itens_pedido (...) VALUES (?, ?, ?, ?)", linhas)
    db.executemany("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", baixas)
```
**JS — antes**: três `db.run` aninhados sem transação; `DELETE FROM users` deixando matrículas órfãs.
**JS — depois**
```js
await db.transaction(async () => {
  const { lastID: enrollmentId } = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
  await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, price, 'PAID']);
});
```

## T11 — Substituir APIs deprecated

**Python — antes**
```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
user = User.query.get(user_id)
```
**Python — depois**
```python
def utcnow():   # naive UTC, mesmo formato que já está no banco
    return datetime.now(timezone.utc).replace(tzinfo=None)
created_at = db.Column(db.DateTime, default=utcnow)
user = db.session.get(User, user_id)
```
**JS — antes**
```js
const buf = new Buffer(pwd); const { query } = url.parse(req.url, true);
```
**JS — depois**
```js
const buf = Buffer.from(pwd); const { searchParams } = new URL(req.url, 'http://localhost');
```

## T12 — Callbacks → async/await

**JS — antes**
```js
db.get(sql1, [a], (err, course) => { db.get(sql2, [b], (err, user) => { db.run(sql3, [c], function (err) { res.json(...) }) }) });
```
**JS — depois** (`src/database/connection.js`)
```js
const get = (sql, params = []) => new Promise((resolve, reject) => db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
// uso
const course = await get(sql1, [a]);
const user = await get(sql2, [b]);
```
**Python** (equivalente: guard clauses no lugar de pirâmide de `if`)
```python
# antes
if task.due_date:
    if task.due_date < now:
        if task.status != 'done' and task.status != 'cancelled':
            return True
# depois
return bool(task.due_date) and task.due_date < now and task.status not in CLOSED_STATUSES
```

## T13 — Constantes nomeadas

**Python — antes**
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
```
**Python — depois**
```python
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (faturamento acima de, percentual)
desconto = next((faturamento * pct for limite, pct in FAIXAS_DESCONTO if faturamento > limite), 0)
```
**JS — antes**
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```
**JS — depois**
```js
const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });
const APPROVED_CARD_PREFIX = '4';   // regra do gateway fake
```

## T14 — Serialização explícita sem dados sensíveis

**Python — antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```
**Python — depois**
```python
PUBLIC_FIELDS = ("id", "name", "email", "role", "active")
def to_dict(self):
    data = {f: getattr(self, f) for f in PUBLIC_FIELDS}
    data["created_at"] = str(self.created_at)
    return data
```
**JS — antes**
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
res.json(user);   // inclui pass
```
**JS — depois**
```js
logger.info(`Processando cartão final ${card.slice(-4)}`);
res.json({ id: user.id, name: user.name, email: user.email });
```

## T15 — Validação na borda

**Python — antes**
```python
preco = dados["preco"]
if preco < 0:   # TypeError com string → 500
```
**Python — depois**
```python
def numero(dados, campo, msg_tipo):
    valor = dados.get(campo)
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(msg_tipo)
    return valor
```
**JS — antes**
```js
if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
```
**JS — depois**
```js
function parseCheckout(body) {
  const { usr, eml, pwd, c_id: courseId, card } = body || {};
  if (!usr || !eml || !courseId || !card) throw new AppError('Bad Request', 400);
  return { name: usr, email: eml, password: pwd, courseId, card: String(card) };
}
```
