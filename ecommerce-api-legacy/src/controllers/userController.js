function userController(userService) {
  return {
    async remove(req, res) {
      await userService.delete(req.params.id);
      res.send('Usuário deletado.');
    },
  };
}

module.exports = userController;
