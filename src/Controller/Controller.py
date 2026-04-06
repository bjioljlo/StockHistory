from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Callable

from src.Model.Model import IModel
from src.View.View import IWindow
from src.View.ViewUtils import MAIN_TITALLIST, PICK__TITALLIST


class controllers(Enum):
    Main = 1
    Pick = 2
    BackTest = 3


class IController(ABC):
    def __init__(self):
        super().__init__()
        self.GetController: GetControllerEvent = None

    @abstractmethod
    def GetView(self) -> IWindow:
        raise NotImplementedError

    @abstractmethod
    def ShowWindow(self):
        raise NotImplementedError

    @abstractmethod
    def GetEndDate(self) -> datetime:
        raise NotImplementedError

    @abstractmethod
    def GetStockNumber(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def SetStockNumber(self, stockNumber: str):
        raise NotImplementedError
    
    def handle_message(self, message_type: str, **kwargs):
        """
        處理來自 Mediator 的訊息
        子類別可覆寫此方法以支援訊息傳遞
        """
        handler = getattr(self, f"on_{message_type}", None)
        if callable(handler):
            return handler(**kwargs)
        return None
    
    def bind_event(self, widget, event_name: str, handler):
        """
        標準化 UI 事件綁定方法
        統一事件處理格式與錯誤處理
        """
        def wrapped_handler(*args, **kwargs):
            try:
                return handler(*args, **kwargs)
            except Exception as e:
                self.on_event_error(event_name, e)
        
        widget.clicked.connect(wrapped_handler)
    
    def on_event_error(self, event_name: str, error: Exception):
        """
        UI 事件錯誤處理預設實作
        子類別可覆寫此方法提供自訂錯誤處理
        """
        print(f"UI Event Error [{event_name}]: {str(error)}")


GetControllerEvent = Callable[[controllers], IController]


class TController(IController):
    def __init__(self, _view: IWindow = None, _model: IModel = None) -> None:
        super(TController, self).__init__()
        self.View = _view
        self.Model = _model

    @property
    def View(self):
        if self._View is None:
            raise
        return self._View

    @View.setter
    def View(self, _view: IWindow):
        self._View = _view

    @property
    def Model(self):
        if self._Model is None:
            raise
        return self._Model

    @Model.setter
    def Model(self, _model: IModel):
        self._Model = _model

    def GetView(self) -> IWindow:
        return self.View

    def ShowWindow(self):
        self.GetView().GetFormUI().show()
