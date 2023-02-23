# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_stores.ipynb.

# %% ../nbs/00_stores.ipynb 1
from __future__ import annotations
from typing import Callable, TypeVar,  Generic, Union, Optional, Set, Protocol, Any
from typing_extensions import Annotated
from fastcore.test import test_eq, test, test_fail
from fastcore.basics import patch

# %% auto 0
__all__ = ['T', 'covT', 'Subscriber', 'Unsubscriber', 'Updater', 'Notifier', 'StoreProtocol', 'Writable', 'Readable', 'Derived']

# %% ../nbs/00_stores.ipynb 7
T = TypeVar("T")
covT = TypeVar("covT", covariant=True)
Subscriber = Callable[[T], None] # a callback
Unsubscriber = Callable[[], None] # a callback to be used upon termination of the subscription    
Updater = Callable[[T], T]
Notifier = Callable[[Subscriber], Union[Unsubscriber, None]]

# %% ../nbs/00_stores.ipynb 8
class StoreProtocol(Protocol, Generic[covT]):
    ''' The Svelte Store ~~contract~~ protocol. '''
    def subscribe(self, subscriber: Subscriber[T]) -> Unsubscriber: ...

# %% ../nbs/00_stores.ipynb 9
class Store(StoreProtocol[T]):
    ''' A base class for all stores.'''
    value: T
    subscribers: Set[Subscriber]
    def __init__(self, /, **kwargs): 
        self.__dict__.update(kwargs) # see SimpleNamespace: https://docs.python.org/3/library/types.html
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.get()!r})"
    def subscribe(self, callback: Subscriber) -> Unsubscriber:
        return lambda: None
    def get(self) -> T: return self.value

class Readable(Store[T]): pass

class Writable(Store[T]):
    set: Subscriber
    update: Optional[Callable[[Updater],None]] = None

# %% ../nbs/00_stores.ipynb 12
from .util import safe_not_equal

# %% ../nbs/00_stores.ipynb 13
class Writable(Store[T]):
    ''' A Writable Store.'''
    def __init__(self:Writable,
                initial_value: Any = None, # initial value of the store
                start: Notifier = lambda x: None # A Notifier (Optional)
                ) -> None:
        self.value = initial_value
        self.subscribers: Set[Subscriber] = set() # callbacks to be called when the value changes
        self.start: Notifier = start # function called when the first subscriber is added
        self.stop: Optional[Unsubscriber] = None  # functional called when the last subscriber is removed
        
    def subscribe(self:Writable,
                  callback: Subscriber # callback to be called when the store value changes
                  ) -> Unsubscriber:
        ''' Adds callback to the list of subscribers.'''
        self.subscribers.add(callback)
        if (len(self.subscribers) == 1):
            self.stop = self.start(callback) or (lambda: None) #type: ignore
        callback(self.value)

        def unsubscribe() -> None:
            ''' Removes callback from the list of subscribers.'''
            self.subscribers.remove(callback) if callback in self.subscribers else None
            if (len(self.subscribers) == 0):
                self.stop() if self.stop else None #type: ignore
                self.stop = None #type: ignore
        return unsubscribe
        
    def set(self, 
            new_value: T # The new value of the store
            ) -> None:
        ''' Set value of store.'''
        if (safe_not_equal(self.value, new_value)):
            self.value = new_value
            for subscriber in self.subscribers:
                subscriber(new_value)
                
    def update(self, 
               fn: Callable[[T], T] # a callback that takes the existing store value and updates it
               ) -> None:
        ''' Update the store value by applying `fn` to the existing value.'''
        self.set(fn(self.value))
    
    def __len__(self) -> int:
        ''' The length of the store is the number of subscribers.'''
        return len(self.subscribers)

# %% ../nbs/00_stores.ipynb 16
class Readable(Writable[T]):
    ''' A Readable Store.''' 
    def __init__(self, 
                 initial_value: T, # initial value of the store
                 start: Notifier # function called when the first subscriber is added
                ) -> None:
        super().__init__(initial_value, start)
    def set(self, *args, **kwargs): raise Exception("Cannot set a Readable Store.")
    def update(self, *args, **kwargs): raise Exception("Cannot update a Readable Store.")

# %% ../nbs/00_stores.ipynb 19
class Derived(Writable):
    ''' A Derived Store.'''
    def __init__(self:Derived, 
             s: Union[Store, list[Store]], # source store(s)
             fn: Callable, # a callback that takes the source store(s) values and returns the derived value
             ) -> None:
        
        self.target = Writable(None) # target store
        
        isStore = isinstance(s, Store)
        isList = isinstance(s, list) and all([isinstance(x, Store) for x in s])
        if not isStore and not isList: raise Exception("s must be a Store or a list of Stores")
        self.sources:list[Store] = [s] if isStore else s 
        self.fn = fn 
        
        # subscribe to each source store and update the target when any of them change
        self.unsubscribers = [(lambda s=s: s.subscribe(self._update))(s) for s in self.sources] 
        
    def get(self): return self.target.get()

    def set(self, *args, **kwargs): raise Exception("Cannot set a Derived Store.")
    def update(self, *args, **kwargs): raise Exception("Cannot update a Derived Store.")
    
    def subscribe(self, 
                  callback: Subscriber # callback to be called when any of the source stores change
                  ) -> Unsubscriber:
        ''' Adds callback to the list of subscribers.'''
        return self.target.subscribe(callback)
    
    def _update(self:Derived, x): # ignore the new value and just refresh the target from sources
        values = [(lambda s=s: s.get())(s) for s in self.sources] # type: ignore
        self.target.set(self.fn(*values)) # type: ignore
