import datetime
import calendar
from typing import Optional

import logging

class FlexibleSchedule:
    """
    Classe que representa um agendamento flexível. O agendamento pode ser diário, semanal ou mensal. O agendamento diário
    pode ser definido por um horário específico ou por um intervalo de tempo. O agendamento semanal pode ser definido por
    um dia da semana e um horário específico ou por um intervalo de tempo. O agendamento mensal pode ser definido por um
    horário específico ou por um intervalo de tempo.

    Estilos de agendamento:
    - [time]: Agendamento diário no horário especificado
        Exemplo: "12:00"
    - ["1d", time]: Agendamento diário no horário especificado
        Exemplo: "1d 12:00"
    - [day, time]: Agendamento semanal no dia e horário especificados
        Exemplo: "mon 12:00"
        Dias da semana válidos: "mon", "tue", "wed", "thu", "fri", "sat", "sun"
    - ["1w", day, time]: Agendamento semanal no dia e horário especificados
        Exemplo: "1w mon 12:00"
    - ["1m", time]: Agendamento mensal no horário especificado
    """

    def __init__(self, schedule: str):
        self.schedule = schedule  # Agendamento
        self.parse_schedule()  # Analisa o agendamento

    def parse_schedule(self):
        parts = self.schedule.split()
        match parts:
            case [time]:
                # Formato 24h diário
                self.interval = "daily"
                self.time = datetime.datetime.strptime(time, "%H:%M").time()
                logging.debug(f"Agendamento diário às {self.time}")
            
            case ["1d", time]:
                # Formato diário explícito
                self.interval = "daily"
                self.time = datetime.datetime.strptime(time, "%H:%M").time()
                logging.debug(f"Agendamento diário explícito às {self.time}")
            
            case [day, time] if day.lower() in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                # Formato semanal
                self.interval = "weekly"
                self.day = day.lower()
                self.time = datetime.datetime.strptime(time, "%H:%M").time()
                logging.debug(f"Agendamento semanal às {self.time} toda(o) {self.day}")
            
            case ["1w", day, time] if day.lower() in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                # Formato semanal explícito
                self.interval = "weekly"
                self.day = day.lower()
                self.time = datetime.datetime.strptime(time, "%H:%M").time()
                logging.debug(f"Agendamento semanal explícito às {self.time} toda(o) {self.day}")
            
            case ["1m", time]:
                # Formato mensal
                self.interval = "monthly"
                self.time = datetime.datetime.strptime(time, "%H:%M").time()
                logging.debug(f"Agendamento mensal às {self.time}")
            
            case _:
                raise ValueError("Formato de agendamento inválido")

    def next_run(self, last_run: Optional[datetime.datetime] = None) -> datetime.datetime:
        now = datetime.datetime.now()  # Pega a data e hora atuais
        if last_run is None:  # Se o último momento de execução não foi fornecido
            last_run = now  # Usa a data e hora atuais

        next_run = None  # Inicializa a variável com None para garantir que tenha um valor

        if self.interval == "daily":  # Se o agendamento é diário
            next_run = datetime.datetime.combine(last_run.date(), self.time)  # Pega a data e hora da próxima execução
            if next_run <= last_run:  # Se a próxima execução é antes do último momento de execução
                next_run += datetime.timedelta(days=1)  # Adiciona um dia à próxima execução
            logging.debug(f"Próxima execução: {next_run}")

        elif self.interval == "weekly":  # Se o agendamento é semanal
            # Verifica o número do dia da semana atual (0 = segunda, 6 = domingo)
            current_weekday = last_run.weekday()
            target_weekday = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"].index(self.day)
            
            # Calcula quantos dias faltam até o próximo dia especificado
            days_ahead = target_weekday - current_weekday

            if days_ahead == 0:  # O dia do agendamento é hoje
                next_run = datetime.datetime.combine(last_run.date(), self.time)
                if next_run <= last_run:  # Se o horário do agendamento já passou hoje, agendar para a próxima semana
                    next_run += datetime.timedelta(days=7)
            elif days_ahead < 0:  # Se o dia já passou nesta semana, agenda para a próxima semana
                days_ahead += 7

            if days_ahead > 0:  # Se ainda não é o dia do agendamento
                next_run = datetime.datetime.combine(last_run.date() + datetime.timedelta(days=days_ahead), self.time)

            logging.debug(f"Próxima execução: {next_run}")

        elif self.interval == "monthly":
            next_run = datetime.datetime.combine(last_run.date(), self.time)  # Pega a data e hora da próxima execução
            if next_run <= last_run:
                # Avança para o próximo mês
                if last_run.month == 12:
                    next_run = next_run.replace(year=last_run.year + 1, month=1)  # Avança para o próximo ano
                else:
                    next_run = next_run.replace(month=last_run.month + 1)  # Avança para o próximo mês
                
                # Ajusta para o último dia do mês se necessário
                last_day = calendar.monthrange(next_run.year, next_run.month)[1]  # Pega o último dia do mês
                if next_run.day > last_day:  # Se o dia da próxima execução é maior que o último dia do mês
                    next_run = next_run.replace(day=last_day)  # Ajusta para o último dia do mês
                logging.debug(f"Próxima execução: {next_run}")

        # Garantir que next_run tenha sido atribuído antes de retornar
        if next_run is None:
            raise ValueError("O agendamento não foi corretamente definido. Verifique os parâmetros de agendamento.")

        return next_run
