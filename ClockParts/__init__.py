"""
Este módulo oferece funcionalidades para agendamento, execução de tarefas e gerenciamento de tarefas recorrentes.
Ele inclui as classes `TaskDescriptor`, `Shaft`, e `Cog`, que juntas permitem a criação de um sistema flexível
para execução de tarefas em horários ou intervalos programados.

Principais Componentes:
- TaskDescriptor: Representa uma tarefa e controla seu agendamento, execução e resultado.
- Shaft: Gerencia cogs e verifica se as tarefas devem ser executadas, com suporte a inscrição de cogs para notificações.
- Cog: Fornece um mecanismo de decoração para tarefas, permitindo o agendamento e execução de funções.
"""

from .shaft import (
    TaskDescriptor,
    Shaft,
    Cog
)

__all__ = [
    'TaskDescriptor',
    'Shaft',
    'Cog'
]

__version__ = "1.0.0"