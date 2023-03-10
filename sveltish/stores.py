# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_stores.ipynb.

# %% ../nbs/00_stores.ipynb 0
from __future__ import annotations
from typing import Callable, TypeVar,  Generic, Union, Optional, Set, Protocol, Any, Sequence
from fastcore.test import test_eq, test_fail

# %% auto 0
__all__ = ['T', 'covT', 'Subscriber', 'Unsubscriber', 'Updater', 'Notifier', 'Readable', 'StoreProtocol', 'Writable', 'Store',
           'writable', 'ReadableStore', 'readable', 'DerivedStore', 'derived', 'pipe']

# %% ../nbs/00_stores.ipynb 6
T = TypeVar("T")
covT = TypeVar("covT", covariant=True)
Subscriber = Callable[[T], None] # a callback
Unsubscriber = Callable[[], None] # a callback to be used upon termination of the subscription
Updater = Callable[[T], T]
Notifier = Callable[[Subscriber], Union[Unsubscriber, None]]

class StoreProtocol(Protocol, Generic[covT]):
    ''' The Svelte Store ~~contract~~ protocol. '''
    def subscribe(self, subscriber: Subscriber[T]) -> Unsubscriber: ...

Readable: TypeAlias = StoreProtocol[T]

class Writable(Readable[T]):
    ''' Writable protocol'''
    def set(self, value: T) -> None: ...
    def update(self, updater: Updater[T]) -> None: ...

# %% ../nbs/00_stores.ipynb 9
import sveltish.utils as utils

# %% ../nbs/00_stores.ipynb 10
class Store(Readable[T]):
    ''' A Writable Store.'''
    def __init__(self:Writable,
                initial_value: Any = None, # initial value of the store
                start: Notifier = utils.noop # A Notifier (Optional)
                ) -> None:
        self.value = initial_value
        self.subscribers: Set[Subscriber] = set() # callbacks to be called when the value changes
        self.start: Notifier = start # function called when the first subscriber is added
        self.stop: Optional[Unsubscriber] = None  # functional called when the last subscriber is removed

    def get(self) -> T: return self.value
    __call__ = get

    def subscribe(self:Writable,
                  callback: Subscriber # callback to be called when the store value changes
                  ) -> Unsubscriber:
        ''' Adds callback to the list of subscribers.'''
        self.subscribers.add(callback)
        if (len(self.subscribers) == 1):
            self.stop = self.start(self.__set) or (lambda: None) #type: ignore
        callback(self.value)
        def unsubscribe() -> None:
            ''' Removes callback from the list of subscribers.'''
            self.subscribers.remove(callback) if callback in self.subscribers else None
            if (len(self.subscribers) == 0):
                self.stop() if self.stop else None #type: ignore
                self.stop = None #type: ignore
        return unsubscribe

    def __set(self,
            new_value: T # The new value of the store
            ) -> None:
        ''' Internal implementation of set used inside Readable Store, which does not exposes set.'''
        if (utils.safe_not_equal(self.value, new_value)):
            self.value = new_value
            for subscriber in self.subscribers:
                subscriber(new_value)

    def set(self,
            new_value: T # The new value of the store
            ) -> None:
        ''' Set value of store.'''
        self.__set(new_value)

    def update(self,
               fn: Callable[[T], T] # a callback that takes the existing store value and updates it
               ) -> None:
        ''' Update the store value by applying `fn` to the existing value.'''
        self.set(fn(self.value))

    def __len__(self) -> int:
        ''' The length of the store is the number of subscribers.'''
        return len(self.subscribers)

    def __repr__(self) -> str:
        return f"w<{len(self)}> ${self.value.__class__.__name__}: {self.value.__repr__()}"

    def __getattr__(self, k):
        '''Called if property not found in Store object.'''
        conditions = [
            isinstance(k, (int, str)),
            not isinstance(self, DerivedStore), #type: ignore
            k[:2]!='__'
        ]
        if all(conditions):
            if isinstance(self.value, dict) and k in self.value:
                return self.value[k] # look in Store value
            if hasattr(self.value, k): 
                return getattr(self.value, k) # look in Store value
        raise AttributeError(k)

    def __setattr__(self, k:str,v) -> None:
        exceptions = ['value', 'subscribers', 'start', 'stop', 'sources', 'fn', 'target']

        if k not in exceptions:
            new_value = self.value
            if isinstance(self.value, dict) and k in self.value:
                new_value = {**self.value, k:v}
            if hasattr(self.value, k):
                new_value = self.value.__class__(**{**self.value.__dict__, k:v})
            # uses set instead of __set because this shouldn't work with readable store 
            self.set(new_value)
        else: super().__setattr__(k,v)

# %% ../nbs/00_stores.ipynb 12
def writable(value: T = None, # initial value of the store
             start: Notifier = utils.noop # Optional Notifier, a function called when the first subscriber is added
             ) -> Writable[T]: # Writable Store
    ''' Creates a new Writable Store (A Writable factory).'''
    return Store(value, start)

# %% ../nbs/00_stores.ipynb 15
class ReadableStore(Store[T]):
    ''' A Readable Store.'''
    def __init__(self,
                 initial_value: T, # initial value of the store
                 start: Notifier # function called when the first subscriber is added
                ) -> None:
        super().__init__(initial_value, start)
    def set(self, *args, **kwargs): raise Exception("Cannot set a Readable Store.")
    def update(self, *args, **kwargs): raise Exception("Cannot update a Readable Store.")
    def __repr__(self) -> str: return "r" + super().__repr__()[1:]

# %% ../nbs/00_stores.ipynb 17
def readable(value: T, # initial value of the store
             start: Notifier  # function called when the first subscriber is added
             ) -> Readable[T]:  # Readable Store
    ''' Creates a new Readable Store (A Readable factory).'''
    return ReadableStore(value, start)

# %% ../nbs/00_stores.ipynb 21
from .utils import compose
from fastcore.foundation import L

# %% ../nbs/00_stores.ipynb 22
class DerivedStore(Store[T]):
    ''' A Derived Store.'''
    def __init__(self,
                 s: Union[Store, list[Store]], # source store(s)
                 *functions: Callable, # a callback that takes the source store(s) values and returns the derived value
             ) -> None:
        self.sources = L(s)
        if not all(isinstance(x, Store) for x in self.sources):
            raise Exception("s must be a Store or a list of Stores")
        self.fn = compose(*functions)

        def start(set_fn: Subscriber):
            def sync(x=None): # x is ignored
                values = self.sources.map(lambda x: x.get())
                set_fn(self.fn(*values))
            sync() # sync target with source values, they can have changed since Derived creation
            unsubscribers = self.sources.map(lambda s: s.subscribe(sync))
            def stop():
                for unsubscribe in unsubscribers: unsubscribe()
            return stop
        values = self.sources.map(lambda x: x.get())
        self.target = readable(self.fn(*values), start)

    def get(self): return self.target.get()
    def set(self, *args, **kwargs): raise Exception("Cannot set a Derived Store.")
    def update(self, *args, **kwargs): raise Exception("Cannot update a Derived Store.")
    def subscribe(self,
                  callback: Subscriber # callback to be called when any of the source stores change
                  ) -> Unsubscriber:
        ''' Adds callback to the list of subscribers.'''
        return self.target.subscribe(callback)

# %% ../nbs/00_stores.ipynb 24
def derived(s: Union[Store, list[Store]], # source store(s)
            *functions: list(Callable[...,T]) # a callback that takes the source store(s) values and returns the derived value
            ) -> Readable: # Derived Store
    ''' Creates a new Derived Store (A Derived factory).'''
    return DerivedStore(s, *functions).target

# %% ../nbs/00_stores.ipynb 28
import fastcore.all as fc

# %% ../nbs/00_stores.ipynb 29
@fc.patch
def pipe(self:Store, # source store
         *functions: list(Callable[...,T]) # functions that transform the source store
         )->Readable[T]: # returned store
     ''' Unix-like Pipe operator.'''
     return derived(self, *functions)

# %% ../nbs/00_stores.ipynb 31
@fc.patch
def __or__(self:Store, # source store
           other: Callable[...,T] # function that transforms the source store
           ) -> Readable[T]: # returned store
    ''' self | other  works like Unix pipes. It returns a Derived Store that is the result of applying other to self.'''
    return self.pipe(other)
