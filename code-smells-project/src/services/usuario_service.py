import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models import domain

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def listar(self):
        return self.usuarios.listar()

    def buscar_por_id(self, usuario_id):
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, nome, email, senha):
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        usuario_id = self.usuarios.criar(nome, email, generate_password_hash(senha), domain.TIPO_USUARIO_PADRAO)
        logger.info("usuário criado: id=%s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        for usuario in self.usuarios.buscar_credenciais(email):
            if usuario["senha"] and check_password_hash(usuario["senha"], senha):
                logger.info("login ok: id=%s", usuario["id"])
                return {k: usuario[k] for k in ("id", "nome", "email", "tipo")}
        logger.info("login falhou")
        raise UnauthorizedError("Email ou senha inválidos", sucesso=False)
