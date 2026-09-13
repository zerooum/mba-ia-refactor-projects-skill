import logging

log = logging.getLogger(__name__)


class NotificadorConsole:
    """Notificações de pedido. Hoje só registram no log, como o sistema original fazia no console."""

    def pedido_criado(self, pedido_id, usuario_id):
        log.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        log.info("ENVIANDO SMS: Seu pedido foi recebido!")
        log.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def pedido_aprovado(self, pedido_id):
        log.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)

    def pedido_cancelado(self, pedido_id):
        log.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)
