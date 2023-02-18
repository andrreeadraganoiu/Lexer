from __future__ import annotations
from builtins import print
from typing import Type
import re


class Parser:

    @staticmethod
    def getLongForm(regex):
        pattern = ""
        found = 0
        for x in regex:
            if x == '[':
                found = 1
            if found == 1:
                if x != ']':
                    pattern += x
                    continue
                pattern += ']'
                regex = regex.replace(pattern, Parser.toLongForm(pattern[1], pattern[len(pattern) - 2]))
                found = 0
                pattern = ""
        return regex

    @staticmethod
    def toLongForm(a, b):
        form = ""
        if a.isalpha():
            for x in range(ord(a), ord(b) + 1):
                form += chr(x) + '|'
            form = form[:-1]
        else:
            for x in range(int(a), int(b) + 1):
                form += str(x) + '|'
            form = form[:-1]
        form = '(' + form
        form += ')'

        return form

    # This function should:
    # -> Classify input as either character(or string) or operator
    # -> Convert special inputs like [0-9] to their correct form
    # -> Convert escaped characters
    # You can use Character and Operator defined in Regex.py
    @staticmethod
    def preprocess(regex: str) -> list:

        found = 0
        plus_op = ""
        regex_string = ""
        for i in range(0, len(regex)):
            if regex[i] == '+':
                found = 1
                if found == 1:
                    if regex[i - 1] == ')':
                        while regex[i - 1] != '(':
                            plus_op = regex[i - 1] + plus_op
                            plus_op = '(' + plus_op
                            i -= 1
                        plus_op = '(' + plus_op
                    elif regex[i - 1] == ']':
                        while regex[i - 1] != '[':
                            plus_op = regex[i - 1] + plus_op
                            i -= 1
                        plus_op = '[' + plus_op
                    else:
                        plus_op = regex[i - 1]
                    regex_string += '.' + plus_op + '*'
                    found = 0
                    plus_op = ""
            else:
                regex_string += regex[i]
        regex = regex_string

        regex = Parser.getLongForm(regex)
        return regex

    @staticmethod
    def swapBrackets(regex: str) -> list:
        string = ""
        for i in regex:
            if i == '(':
                string += ')'
            elif i == ')':
                string += '('
            else:
                string += i
        return string

    # This function should construct a prenex expression out of a normal one.
    @staticmethod
    def toPrenex(s: str) -> str:

        if s == "eps":
            return s

        operators = {'(': 0, ')': 0, '|': 1, '.': 2, '*': 3, '+': 3, '?': 3}

        s = Parser.preprocess(s)

        string = ""
        i = 0
        while i < len(s) - 1:
            if s[i].isalpha() and s[i + 1].isalpha() \
                    or s[i].isalpha() and s[i + 1] == "(" \
                    or s[i] == ")" and s[i + 1].isalpha() \
                    or s[i] == ")" and s[i + 1] == "(" \
                    or s[i] == "*" and s[i + 1] == "(" \
                    or s[i] == "*" and s[i + 1].isalpha() \
                    or s[i] == "+" and s[i + 1] == "(" \
                    or s[i] == "?" and (s[i + 1].isdigit() or s[i + 1].isalpha()):

                string += s[i] + '.'
                i += 1
            else:
                string += s[i]
                i = i + 1

        if i == len(s) - 1:
            s = string + s[i]
        else:
            s = string

        i = 0
        string = ""
        while i < len(s) - 3:
            if (s[i].isalpha() or s[i] == ')') and s[i + 1] == "'" and s[i + 3] == "'":
                string += s[i] + '.' + s[i + 1: i + 3]
                i += 3
            elif i >= 2 and s[i] == "'" and s[i - 2] == "'" and (
                    s[i + 1] == '(' or s[i + 1].isalpha() or s[i + 1] == "'"):
                string += s[i] + '.'
                i += 1
            else:
                string += s[i]
                i = i + 1
        s = string + s[-3:]

        s = s[::-1]

        s = Parser.swapBrackets(s)

        prefix = ""
        stack = []
        for i in s:
            if i not in operators:
                prefix += i
            elif i == '(':
                stack.append(i)
            elif i == ')':
                while stack[-1] != '(':
                    prefix += stack.pop()
                stack.pop()  # se scoate '('
            else:
                while len(stack) > 0 and operators[i] <= operators[stack[-1]]:
                    prefix += stack.pop()
                stack.append(i)
        while len(stack) > 0:
            prefix += stack.pop()

        prefix = prefix[::-1]

        i = 0
        string = ""
        while i < len(prefix) - 2:
            if prefix[i] == "'":
                if prefix[i + 2] == "'":
                    string += prefix[i: i + 3] + " "
                    i += 3
                else:
                    string += prefix[i] + " "
                    i += 1
            else:
                string += prefix[i] + " "
                i += 1
        if i == len(prefix) - 2:
            string += prefix[-2] + " " + prefix[-1]
        if len(prefix) > 1:
            prefix = string

        prefix = prefix.replace('.', "CONCAT")
        prefix = prefix.replace('|', "UNION")
        prefix = prefix.replace('*', "STAR")
        prefix = prefix.replace('?', "UNION eps")

        return prefix
