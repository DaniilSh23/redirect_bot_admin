"""
Кастомные исключения.
"""


class EmptySettingException(Exception):
    """
    Исключения об отсутствии в настройках проекта определенного параметра
    """
    def __init__(self, message, code=None):
        err_msg = "В настройках проекта отсутствует параметр "
        super().__init__(f"{err_msg} {message!r}")  # Передаем сообщение в базовый класс
        self.code = code  # Дополнительный параметр

    def __str__(self):
        if self.code:
            return f"[KeitaroException {self.code}] {super().__str__()}"
        return super().__str__()
