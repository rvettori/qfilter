# qfilter

Simple query filter for pyhton with dataset.

Tested with https://dataset.readthedocs.io/en/latest/

## Basic Usage:
```
form qfilter import qfilter

q = qfilter(dict(field1__eq=2))

print(q.where)

```

