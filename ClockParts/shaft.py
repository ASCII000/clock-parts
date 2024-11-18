from functools import wraps

from ClockParts.utils.main import FlexibleSchedule

import datetime
import asyncio
import importlib
import inspect
import os
from typing import Any, Callable, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor

from colorama import Fore, Style, init
import psutil

import logging


init()

class TaskDescriptor:
    """
    Descritor de tarefa. Ele é responsável por armazenar a função que representa a tarefa e o agendamento da tarefa.
    Ele também armazena o último resultado retornado pela função, o último momento em que a função foi executada e o
    número de vezes que a função foi executada. Ele também fornece métodos para verificar se a função deve ser
    executada e para atualizar o último momento em que a função foi executada e o último resultado retornado pela função.

    Args:
        func (Callable): Função que representa a tarefa.
        schedule (Union[datetime.timedelta, str]): Horário ou intervalo de execução da tarefa.

    Attributes:
        func (Callable): Função que representa a tarefa.
        schedule (Union[datetime.timedelta, str]): Agendamento da tarefa.
        time_to_execute (Optional[datetime.timedelta]): Intervalo de tempo para a execução da tarefa (se aplicável).
        last_run_map (Dict[Any, datetime.datetime]): Mapeia o último momento em que a função foi executada para cada objeto.
        last_result (Any): Último resultado retornado pela função.
        last_execution_time (Optional[datetime.datetime]): Último momento em que a função foi executada.
        execution_count (int): Número de vezes que a função foi executada.
        init_time (datetime.datetime): Momento de inicialização do descritor.
        elapsed_time (Optional[float]): Tempo decorrido para a execução da tarefa em milissegundos.
    """

    def __init__(self, func: Callable, schedule: Union[datetime.timedelta, str], timeout: int = None) -> None:

        self.func = func  # Função que representa a tarefa
        self.schedule = schedule if isinstance(schedule, FlexibleSchedule) \
            else FlexibleSchedule(schedule) if isinstance(schedule, str) else None  # Agendamento da tarefa
        self.time_to_execute = schedule if isinstance(schedule, datetime.timedelta) else None  # Intervalo de tempo para a execução da tarefa
        self.last_run_map: Dict[Any, datetime.datetime] = {}  # Mapeia o último momento em que a função foi executada para cada objeto
        self.last_result: Any = None  # Último resultado retornado pela função
        self.last_execution_time: Optional[datetime.datetime] = None  # Último momento em que a função foi executada
        self.execution_count: int = 0  # Número de vezes que a função foi executada
        self.init_time: datetime.datetime = datetime.datetime.now()  # Momento de inicialização do descritor
        self.elapsed_time: float | None = None
        self.error: Exception = None
        self.time_out: int | None = timeout

    def should_run(self, obj) -> bool:
        """
        Verifica se a função deve ser executada para o objeto fornecido.
        Ou seja, verifica se o momento atual é maior ou igual ao momento em que a função deve ser executada.
        """

        now = datetime.datetime.now()  # Pega a data e hora atuais
        last_run = self.last_run_map.get(obj)  # Pega o último momento em que a função foi executada para o objeto fornecido
        
        if last_run is None:  # Se o último momento em que a função foi executada não foi encontrado
            if self.schedule:  # Se o agendamento foi fornecido
                return now >= self.schedule.next_run(self.init_time)  # Verifica se o momento atual é maior ou igual ao próximo momento de execução
            else:
                return now >= self.init_time + self.time_to_execute  # Verifica se o momento atual é maior ou igual ao momento de inicialização mais o intervalo de tempo para a execução
        else:
            if self.schedule:
                return now >= self.schedule.next_run(last_run)  # Verifica se o momento atual é maior ou igual ao próximo momento de execução
            else:
                return now >= last_run + self.time_to_execute  # Verifica se o momento atual é maior ou igual ao último momento de execução mais o intervalo de tempo para a execução

    def update_last_run(self, obj) -> None:
        """
        Atualiza o último momento em que a função foi executada para o objeto fornecido.
        """

        self.last_run_map[obj] = datetime.datetime.now()  # Atualiza o último momento em que a função foi executada para o objeto fornecido
        self.execution_count += 1  # Incrementa o número de vezes que a função foi executada

    def update_last_result(self, result: Any) -> None:
        """
        Atualiza o último resultado retornado pela função e o último momento em que a função foi executada.
        """

        self.last_result = result  # Atualiza o último resultado retornado pela função
        self.last_execution_time = datetime.datetime.now()  # Atualiza o último momento em que a função foi executada

    def __get__(self, obj, objtype=None):  # Permite que o descritor seja acessado como um atributo de classe
        if obj is None:
            return self
        
        @wraps(self.func)
        async def wrapper(*args, **kwargs):
            return await self.func(obj, *args, **kwargs)
        
        return wrapper

class Shaft:
    """
    Esta é a haste que conecta os cogs. Ela é responsável por gerenciar os cogs e verificar se as tarefas devem ser
    executadas. Ela também permite que os cogs se inscrevam para receber notificações quando uma tarefa é executada.

    Args:
        timeout_cog (int): Tempo limite para a execução de uma tarefa em segundos.
    """

    def __init__(self, default_timeout_cog: int = 5) -> None:
        self.cogs: List[Dict[str, Any]] = []
        self.cogs_methods: List[str] = []
        self.subscribers: Dict[str, List[Callable]] = {}
        self.startup_app = None
        self.shutdown_app = None
        self.default_timeout_cog = default_timeout_cog

    
    def startup(self) -> Callable:
        """
        Função de decoração para marcar um método como método de inicialização do aplicativo.
        """
    
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            self.startup_app = wrapper
            return wrapper
        return decorator

    def shutdown(self) -> Callable:
        """
        Função de decoração para marcar um método como método de encerramento do aplicativo.
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            self.shutdown_app = wrapper
            return wrapper
        return decorator

    def cog(self, task_name: str):
        """
        Manipula a chamada de um método de instância. Retorna um método de instância que chama a função armazenada no
        descritor, passando o objeto de instância como primeiro argumento.

        Args:
            task_name (str): Nome da tarefa a ser inscrita.
        """
        
        if task_name not in self.cogs_methods:
            raise ValueError(f"Tarefa '{task_name}' não encontrada")

        def decorator(func: Callable) -> Callable:
            sig = inspect.signature(func)  # Pega assinatura da função
            params = list(sig.parameters.values())  # Pega parâmetros da função
            
            if len(params) != 1 and len(params) != 2:  # Verifica se a função tem um ou dois parâmetros
                raise ValueError(f"Função {func.__name__} deve ter um ou dois parâmetros")

            @wraps(func)
            async def wrapper(descriptor: TaskDescriptor, result: Any):
                if len(params) == 1:  # Se a função tem um parâmetro
                    await func(result)  # Chama a função com o resultado da tarefa
                else:
                    if params[0].annotation == TaskDescriptor:  # Se o primeiro parâmetro é um descritor de tarefa
                        await func(descriptor, result)  # Chama a função com o descritor de tarefa e o resultado da tarefa
                    else:
                        await func(result)  # Chama a função com o resultado da tarefa
            
            if task_name not in self.subscribers:  # Verifica se a tarefa já tem inscritos
                self.subscribers[task_name] = []
            self.subscribers[task_name].append(wrapper)  # Adiciona a função inscrita à lista de inscritos
            return wrapper
        return decorator

    def add_cogs(self, cogs_dir: str = "cogs") -> None:

        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                cogs_path = cogs_dir.replace("/", ".")
                module = importlib.import_module(f"{cogs_path}.{filename[:-3]}")
                for _, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Cog) and obj is not Cog:
                        if obj.__module__ == module.__name__:
                            cog_instance = obj()
                            self.cogs.append({
                                "alias": obj.__name__,
                                "obj": cog_instance
                            })

                            # Execute startup method if it exists
                            for method_name, method in inspect.getmembers(cog_instance):
                                if hasattr(method, '__cog_startup__'):
                                    asyncio.run(method())

                            for method_name, _ in inspect.getmembers(cog_instance):
                                if not method_name.startswith("__"):
                                    self.cogs_methods.append(method_name)

                            break

    async def verify_cogs(self) -> None:
        """
        Método que verifica os cogs e executa as tarefas que devem ser executadas.
        """
        logging.info("Iniciando verificação de cogs")
        logging.debug("Cogs disponíveis:")
        for cog in self.cogs:
            logging.debug(f"{cog['alias']}")
            for task_name, task_descriptor in inspect.getmembers(
                type(cog["obj"]), predicate=lambda x: isinstance(x, TaskDescriptor)
            ):
                logging.debug(f"  {task_name} - {task_descriptor.schedule}")

        for subscriber in self.subscribers:
            logging.debug(f"Inscritos em {subscriber}:")
            for sub in self.subscribers[subscriber]:
                logging.debug(f"  {sub.__name__}")

        # Criando o ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=10) as executor:
            while True:
                logging.debug("Verificando cogs")
                
                # Lista para armazenar as tasks que serão executadas em paralelo
                tasks = []

                for cog in self.cogs:  # Percorre os cogs
                    for task_name, task_descriptor in inspect.getmembers(
                        type(cog["obj"]), predicate=lambda x: isinstance(x, TaskDescriptor)
                    ):  # Percorre os descritores de tarefa do cog
                        if task_descriptor.should_run(cog["obj"]):  # Verifica se a tarefa deve ser executada
                            # Cria uma tarefa assíncrona que executa o método no executor
                            task = asyncio.get_event_loop().run_in_executor(
                                executor, self.run_task, cog["obj"], task_name, task_descriptor
                            )
                            tasks.append(task)

                # Aguarda todas as tarefas terminarem
                await asyncio.gather(*tasks)

                await asyncio.sleep(1)

    def run_task(self, cog_obj, task_name, task_descriptor):
        """Executa a tarefa e notifica os inscritos, tratando erros e tempo de execução."""
        e = None
        result = None
        try:
            start_time = datetime.datetime.now()
            task_func = getattr(cog_obj, task_name)

            # Verifica se a função é uma corrotina
            if asyncio.iscoroutinefunction(task_func):
                # Executa e aguarda a corrotina
                result = asyncio.run(task_func())
            else:
                # Executa a função síncrona normalmente
                result = task_func()

            end_time = datetime.datetime.now()
            task_descriptor.elapsed_time = (end_time - start_time).total_seconds() * 1000
        except Exception as ex:
            logging.error(f"Erro ao executar tarefa {task_name}: {ex}")
            e = ex
        finally:
            task_descriptor.update_last_run(cog_obj)
            task_descriptor.update_last_result(result)
            task_descriptor.error = e

            # Notifica os inscritos, se houver
            if task_name in self.subscribers:
                for subscriber in self.subscribers[task_name]:
                    try:
                        subscriber(task_descriptor, result)  # Executa de forma síncrona
                    except Exception as ex:
                        logging.error(f"Error in subscriber for {task_name}: {ex}")


    async def shutdown_cogs(self):
        """
        Método para executar os métodos de encerramento de todos os cogs.
        """
        for cog in self.cogs:
            for _, method in inspect.getmembers(cog["obj"]):
                if hasattr(method, '__cog_shutdown__'):
                    await method()

    async def main(self):
        """
        Método principal para executar o Shaft.
        """
        try:
            logging.info("[Shaft] - Iniciando Shaft")
            if self.startup_app:
                await self.startup_app()
            self.print_system_info()
            self.print_tasks_info()
            await self.verify_cogs()
        finally:
            if self.shutdown_app:
                await self.shutdown_app()

            await self.shutdown_cogs()
    
    def run(self):
        """
        Método para executar o Shaft.
        """
        asyncio.run(self.main())

    def print_system_info(self):
        mem = psutil.virtual_memory()
        print(f"{Fore.CYAN}Sistema Iniciado{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Memória RAM disponível: {mem.available / (1024 * 1024):.2f} MB{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Uso de CPU: {psutil.cpu_percent()}%{Style.RESET_ALL}")

    def print_tasks_info(self):
        print(f"\n{Fore.YELLOW}Tarefas registradas:{Style.RESET_ALL}")
        for cog in self.cogs:
            print(f"\n{Fore.MAGENTA}{cog['alias']}:{Style.RESET_ALL}")
            for task_name, task_descriptor in inspect.getmembers(
                type(cog["obj"]), predicate=lambda x: isinstance(x, TaskDescriptor)
            ):
                print(f"  {Fore.CYAN}{task_name}{Style.RESET_ALL} - Agendamento: {task_descriptor.time_to_execute} - Última execução: {task_descriptor.last_execution_time} - Número de execuções: {task_descriptor.execution_count} - Tempo de execução: {task_descriptor.elapsed_time} ms")

class Cog:
    @staticmethod
    def task(schedule: Union[datetime.timedelta, str], *, timeout: int = None) -> Callable:
        """
        Agenda uma tarefa para ser executada em um horário específico ou em intervalos regulares.

        Args:
            schedule (Union[datetime.timedelta, str]): Horário ou intervalo de execução da tarefa.
        
        Notes:
            Dias da semana válidos: "mon", "tue", "wed", "thu", "fri", "sat", "sun"

        Exemplos:
            >>> class ExampleCog(Cog):
            >>>    @Cog.task("19:00")
            >>>    async def daily_task(self):
            >>>        print(f"Executando tarefa diária às 19:00")
            >>>        return "Tarefa diária concluída"
            >>> 
            >>>    @Cog.task("1d 08:30")
            >>>    async def explicit_daily_task(self):
            >>>        print(f"Executando tarefa diária explícita às 08:30")
            >>>        return "Tarefa diária explícita concluída"
            >>>
            >>>    @Cog.task("mon 10:00")
            >>>    async def weekly_task(self):
            >>>        print(f"Executando tarefa semanal toda segunda-feira às 10:00")
            >>>        return "Tarefa semanal concluída"
            >>>
            >>>    @Cog.task("1w wed 15:30")
            >>>    async def explicit_weekly_task(self):
            >>>        print(f"Executando tarefa semanal explícita toda quarta-feira às 15:30")
            >>>        return "Tarefa semanal explícita concluída"
            >>>
            >>>    @Cog.task("1m 12:00")
            >>>    async def monthly_task(self):
            >>>        print(f"Executando tarefa mensal no primeiro dia do mês às 12:00")
            >>>        return "Tarefa mensal concluída"
            >>>
            >>>    @Cog.task(datetime.timedelta(seconds=10))
            >>>    async def interval_task(self):
            >>>        print(f"Executando tarefa a cada 10 segundos")
            >>>        return "Tarefa de intervalo concluída"
        """

        def decorator(func: Callable) -> TaskDescriptor:
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                start_time = datetime.datetime.now()
                result = await func(self, *args, **kwargs)
                end_time = datetime.datetime.now()
                wrapper.time_in_ms = (end_time - start_time).total_seconds() * 1000
                return result
            
            return TaskDescriptor(wrapper, schedule)
        return decorator

    @staticmethod
    def startup():
        """
        Decorator para marcar um método como método de inicialização do cog.
        Este método será executado quando o cog for carregado.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                return await func(self, *args, **kwargs)
            wrapper.__cog_startup__ = True
            return wrapper
        return decorator

    @staticmethod
    def shutdown():
        """
        Decorator para marcar um método como método de encerramento do cog.
        Este método será executado quando o cog for descarregado ou o programa for encerrado.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                return await func(self, *args, **kwargs)
            wrapper.__cog_shutdown__ = True
            return wrapper
        return decorator
    