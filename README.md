Sveltish
================

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

`Svelte Stores` are one of the secret weapons of the [Svelte
framework](https://svelte.dev/) (the recently voted [most loved web
framework](https://insights.stackoverflow.com/survey/2021#section-most-loved-dreaded-and-wanted-web-frameworks)).

Stores allow easy [reactive
programming](https://en.wikipedia.org/wiki/Reactive_programming) by
presenting an [Observer
pattern](https://en.wikipedia.org/wiki/Observer_pattern) that is as
simple as necessary, but not simpler.

## Install

``` sh
pip install sveltish
```

## How to use

Sometimes, you’ll have values that need to be accessed by multiple
unrelated objects.

For that, you can use `stores`. It is a very simple implementation
(around 100 lines of code) of the Observer/Observable pattern.

A store is simply an object with a `subscribe` method that allows
interested parties to be notified when its value changes.

#### **Writable Stores**

``` python
from sveltish.stores import Writable
```

``` python
count = Writable(0)
history = []  # logging for testing
# subscribe returns an unsubscriber
def record(x): 
    history.append(x)
    print(history)
stop = count.subscribe(record)
count
```

    [0]

    Writable(0)

We just created a store, `count`. Its value can be accessed via a
`callback` we pass in the `count.subscribe` method:

A **Writable** can be set from the outside. When it happens, all its
subscribers will react.

``` python
def increment(): count.update(lambda x: x + 1)
def decrement(): count.update(lambda x: x - 1)
def reset(): count.set(0)

count.set(3)
increment()
decrement()
decrement()
reset()
count.set(42)


test_eq(history, [0, 3, 4, 3, 2, 0, 42])
```

    [0, 3]
    [0, 3, 4]
    [0, 3, 4, 3]
    [0, 3, 4, 3, 2]
    [0, 3, 4, 3, 2, 0]
    [0, 3, 4, 3, 2, 0, 42]

The `unsubscriber`, in this example the `stop` function, stops the
notifications to the `subscriber`.

``` python
stop()
reset()
count.set(22)
test_eq(history, [0, 3, 4, 3, 2, 0, 42])
count
```

    Writable(22)

Notice that you can still change the `store` but there was no print
message this time. There was no observer listening.

<div>

> **Note**
>
> `Observer`, `Subscriber` and `Callback` are used as synomyms here.

</div>

When we subscribe new callbacks, they will be promptly informed of the
current state of the `store`.

``` python
stop  = count.subscribe(lambda x: print(f"Count is now {x}"))
stop2 = count.subscribe(lambda x: print(f"double of count is {2*x}"))
```

    Count is now 22
    double of count is 44

``` python
reset()
```

    Count is now 0
    double of count is 0

``` python
stop()
stop2()
```

You can create an empty `Writable Store`.

``` python
store = Writable()
history = []
unsubscribe = store.subscribe(lambda x: history.append(x))
unsubscribe()
test_eq(history, [None])
```

If you try to unsubscribe twice, it won’t break. It just does nothing
the second time… and in the third time… and…

``` python
unsubscribe(), unsubscribe(), unsubscribe()
```

    (None, None, None)

Stores assume mutable objects.

<div>

> **Note**
>
> In Python everythong is an object. Here we are calling an object
> something that is not a primitive (eg. int, bool, etc)

</div>

``` python
class Bunch:
    __init__ = lambda self, **kw: setattr(self, '__dict__', kw)

obj = Bunch()
called = 0
store = Writable(obj)
def callback(x):
    global called
    called += 1
stop = store.subscribe(callback)
```

``` python
test_eq(called, 1)
obj.a = 1 #type: ignore
store.set(obj)
test_eq(called, 2)
```

#### **Readable Stores**

However… It is clear that not all stores should be writable by whoever
has a reference to them. Many times you want a single `publisher` of
change in store that is only consumed (`subscribed`) by many other
objects. For those cases, we have readable stores.

<div>

> **Note**
>
> The `Publisher Subscriber (PubSub)` pattern is a variant of the
> `Observable/Observer` pattern.

</div>

``` python
from sveltish.stores import Readable
```

``` python
# from sveltish.stores import Readable
# from threading import Event, Thread
# import time


# def start(set): # the start function is the publisher
#     stopped = Event()
#     def loop(): # needs to be in a separate thread
#         while not stopped.wait(1): # in seconds
#             set(time.localtime())
#     Thread(target=loop).start()    
#     return stopped.set
   
# now = Readable(time.localtime(), start)
```

<div>

> **Note**
>
> The `loop` needs to be in its own thread, otherwise the function would
> never return and we would wait forever.

</div>

``` python
# now
```

    Readable(time.struct_time(tm_year=2023, tm_mon=2, tm_mday=23, tm_hour=18, tm_min=25, tm_sec=36, tm_wday=3, tm_yday=54, tm_isdst=0))

While there is no subscriber, the Readable will not be updated.

``` python
# now
```

    Readable(time.struct_time(tm_year=2023, tm_mon=2, tm_mday=23, tm_hour=18, tm_min=25, tm_sec=36, tm_wday=3, tm_yday=54, tm_isdst=0))

``` python
# OhPleaseStop = now.subscribe(lambda x: print(time.strftime(f"%H:%M:%S", x), end="\r"))
```

    18:25:36

``` python
# time.sleep(3)
# OhPleaseStop()
```

    18:25:39

A Readable store without a `start` function is a constant value and has
no meaning for us. Therefore, `start` is a required argument.

``` python
try:
    c = Readable(0) # shoud fail
except Exception as error:
    print(error)
```

    __init__() missing 1 required positional argument: 'start'

<div>

> **Note**
>
> The Svelte Store api allow you to create a Readable Store without a
> Notifier. See discussion
> [here.](https://github.com/sveltejs/svelte/issues/8300)

</div>

#### **Derived Stores**

A `Derived Store` stores a value based on the value of another store.

``` python
from sveltish.stores import Derived
```

``` python
count = Writable(1)
stopCount = count.subscribe(lambda x: print(f"count is {x}"))
double = Derived(count, lambda x: x * 2)
stopDouble = double.subscribe(lambda x: print(f"double is {x}"))
test_eq(double.get(), 2*count.get())
```

    count is 1
    double is 2

``` python
count.set(2)
test_eq(double.get(), 4)
```

    count is 2
    double is 4

Building on our previous example, we can create a store that derives the
elapsed time since the original store was started.

``` python
# def calc_elapsed(then):
#     now = time.localtime()
#     return time.mktime(now) - time.mktime(then)
```

``` python
# elapsed = Derived(now, calc_elapsed)
```

``` python
# stopElapsed = elapsed.subscribe(lambda x: print(f"Elapsed time: {x} seconds.", end="\r"))
```

    Elapsed time: 4.0 seconds.

``` python
# time.sleep(10)
# stopElapsed()
```

    Elapsed time: 14.0 seconds.

Derived stores allow us to transform the value of a store. In RxPy they
are called `operators`. You can build several operators like: `filter`,
`fold`, `map`, `zip`…

Let’s build a custom `filter` operator:

``` python
user = Writable({"name": "John", "age": 32})
stopLog = user.subscribe(lambda x: print(f"User: {x}"))
```

    User: {'name': 'John', 'age': 32}

``` python
name = Derived(user, lambda x: x["name"])
stopName = name.subscribe(lambda x: print(f"Name: {x}"))
```

    Name: John

``` python
user.update(lambda x: x | {"age": 45})
```

    User: {'name': 'John', 'age': 45}

Updating the age does not trigger the name subscriber.

``` python
user.update(lambda x: x | {"name": "Fred"})
```

    Name: Fred
    User: {'name': 'Fred', 'age': 45}

Only changes to the name of the user triggers the `name` subscriber.

Another cool thing about Derived Stores is that you can derive from a
list of stores. Let’s build a `zip` operator.

``` python
a = Writable([1,2,3,4])
b = Writable([5,6,7,8])
a,b
```

    (Writable([1, 2, 3, 4]), Writable([5, 6, 7, 8]))

``` python
zipper = Derived([a,b], lambda a,b: list(zip(a,b)))
test_eq(zipper.get(), [(1, 5), (2, 6), (3, 7), (4, 8)])
```

``` python
a.set([4,3,2,1])
test_eq(zipper.get(), [(4, 5), (3, 6), (2, 7), (1, 8)])
```
