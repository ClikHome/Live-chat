#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import itertools


class ValidateArguments(object):
    def __init__(self, **kwargs):
        self.validators = kwargs

    def __call__(self, cls):
        def wrapper(*args, **kwargs):
            for method in inspect.getmembers(cls, predicate=inspect.ismethod):
                args_names = method[1].__code__.co_varnames[1:]
                if any(arg_name in self.validators for arg_name in args_names):
                    setattr(cls, method[0], self.validate(method[1]))

            return cls(*args, **kwargs)
        return wrapper

    def validate(self, f):
        def wrapper(*args, **kwargs):
            args_names = inspect.getargspec(f).args

            for arg_name, arg in dict(itertools.izip(args_names, args)).items():
                if arg_name in self.validators:
                    kwargs[arg_name] = self.validators[arg_name](arg)
                else:
                    kwargs[arg_name] = arg

            instance = kwargs.get('self', None)

            if instance:
                del kwargs['self']
                return f(instance, **kwargs)
            return f(**kwargs)
        return wrapper