# opensearch-log

`opensearch-log` - это Python log handler, предназначенный для прямой и эффективной передачи логов в 
OpenSearch или AWS CloudWatch.

Также он может быть использован для JSON логирования в stdout.

Используя контекстный менеджер или декоратор, можно легко добавить дополнительные поля к сообщениям 
логов.

## Установка

Для установки `opensearch-log` выполните следующую команду:

```bash
pip install opensearch-log
```

## Настройка логгера

Для глобальной конфигурации логгера используйте соответствующую функцию `get_logger` в зависимости 
от того, куда вы собираетесь отправлять логи. 

Эта функция не только возвращает настроенный логгер, но и конфигурирует логгер по умолчанию, 
гарантируя, что последующие вызовы `logging.getLogger()` вернут тот же экземпляр логгера.

### Отправка логов в OpenSearch

Для отправки логов в OpenSearch используйте:

```python
from opensearch_log import Logging
from opensearch_log.opensearch_handler import get_logger

logger = get_logger(index_name="myindex", echo_stdout=True)
with Logging(my_log_field="Из Python"):
    logger.info("Привет, мир")
```

Это передаст в OpenSearch запись, которая выглядит так (вывод сокращен для удобочитаемости):

```json
{
  "_index": "myindex-2023.12.16",
  "_source": {
    "@timestamp": "2023-12-16T06:39:19.479Z",
    "msg": "Привет, мир",
    "my_log_field": "Из Python"
  }
}
```

Одновременно это будет выведено в терминале (вывод сокращен для удобочитаемости):

```json
{
  "message": "Привет, мир",
  "name": "root",
  "my_log_field": "Из Python"
}
```

### Отправка логов в AWS CloudWatch

Для логирования в AWS CloudWatch используйте `get_logger` из `cloudwatch_handler`:

```python
from opensearch_log.cloudwatch_handler import get_logger

logger = get_logger(index_name="myindex", echo_stdout=True)
```

### JSON логирование в stdout

Для приложений, требующих только JSON логирования без необходимости отправки логов в OpenSearch 
или AWS CloudWatch, используйте `get_logger` из `stdout_handler`:

```python
from opensearch_log.stdout_handler import get_logger

logger = get_logger(index_name="myindex", echo_stdout=True)
```

## Добавление полей к логам

Дополнение логов полями может быть достигнуто с использованием декоратора, контекстного менеджера 
или простых вызовов функций. 

После этого поля будут добавлены во все сообщения логов.

### Контекстный менеджер

```python
from opensearch_log import Logging

with Logging(my_log_field="Из Python"):
    logger.info("Привет, мир")
```

### Декоратор

```python
from opensearch_log import log_fields

@log_fields(my_log_field="Из Python")
def my_func():
    logger.info("Привет, мир")
```

### Простые функции

```python
from opensearch_log import add_log_fields, remove_log_fields

added_fields = add_log_fields(my_log_field="Из Python")
try:
    logger.info("Привет, мир")
finally:
    remove_log_fields(*added_fields)
```
