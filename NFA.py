from typing import Callable, Generic, TypeVar
import shlex
import copy
import re

S = TypeVar("S")
T = TypeVar("T")


def voidNFA(initial_state, final_state) -> 'NFA[int]':
    states = []
    states.append(initial_state)
    states.append(final_state)
    nfa = NFA[int](initial_state, final_state, {}, states)

    return nfa


def epsilonNFA(initial_state, final_state) -> 'NFA[int]':
    states = []
    states.append(initial_state)
    nfa = NFA[int](initial_state, final_state, {}, states)

    return nfa


def characterNFA(symbol, initial_state, final_state) -> 'NFA[int]':
    delta = {}
    states = [initial_state, final_state]
    delta[initial_state] = []
    delta[initial_state].append((symbol, final_state))
    nfa = NFA[int](initial_state, final_state, delta, states)

    return nfa


def concatNFA(nfa1, nfa2) -> 'NFA[int]':
    nfa = nfa1
    nfa.states = nfa.states + nfa2.states
    nfa.delta.update(nfa2.delta)
    nfa.delta[nfa1.final_state] = []
    nfa.delta[nfa1.final_state].append(('eps', nfa2.initial_state))
    nfa.initial_state = nfa1.initial_state
    nfa.final_state = nfa2.final_state

    return nfa


def unionNFA(nfa1, nfa2, initial_state, final_state) -> 'NFA[int]':
    nfa = nfa1
    nfa.states += nfa2.states
    nfa.states.append(initial_state)
    nfa.states.append(final_state)

    nfa.delta.update(nfa2.delta)

    nfa.delta[initial_state] = []
    nfa.delta[initial_state].append(('eps', nfa1.initial_state))
    nfa.delta[initial_state].append(('eps', nfa2.initial_state))

    nfa.delta[nfa1.final_state] = []
    nfa.delta[nfa1.final_state].append(('eps', final_state))

    nfa.delta[nfa2.final_state] = []
    nfa.delta[nfa2.final_state].append(('eps', final_state))

    nfa.initial_state = initial_state
    nfa.final_state = final_state

    return nfa


def starNFA(nfa, initial_state, final_state) -> 'NFA[int]':
    nfa.states.append(initial_state)
    nfa.states.append(final_state)

    nfa.delta[initial_state] = []
    nfa.delta[initial_state].append(('eps', nfa.initial_state))
    nfa.delta[initial_state].append(('eps', final_state))

    nfa.delta[nfa.final_state] = []
    nfa.delta[nfa.final_state].append(('eps', nfa.initial_state))
    nfa.delta[nfa.final_state].append(('eps', final_state))

    nfa.initial_state = initial_state
    nfa.final_state = final_state

    return nfa


class NFA(Generic[S]):
    def __init__(self, initial_state, final_state, delta, states):
        self.initial_state = initial_state
        self.final_state = final_state
        self.delta = delta
        self.states = states
        self.sigma = set()

    def map(self, f: Callable[[S], T]) -> 'NFA[T]':
        pass

    def next(self, from_state: S, on_chr: str) -> 'set[S]':
        s = set()

        if from_state not in self.delta.keys():
            return s

        for i in self.delta[from_state]:
            if i[0] == on_chr:
                s.add(i[1])

        return s

    def getStates(self) -> 'set[S]':
        return self.states

    def accepts(self, str: str) -> bool:
        stack = []
        stack.append((self.initial_state, 'eps', str))
        isAccepted = False

        while stack:
            q = stack.pop()
            state = q[0]
            word = copy.deepcopy(q[2])

            if q[1] != 'eps':
                word = word[1:len(word)]

            if self.isFinal(state) and not word:
                isAccepted = True
                break

            if not self.isFinal(state):
                isAccepted = False

            for s in self.next(state, 'eps'):
                stack.append((s, 'eps', word))

            if word:
                for s in self.next(state, word[0]):
                    stack.append((s, word[0], word))

        return isAccepted

    def isFinal(self, state: S) -> bool:
        return state == self.final_state

    @staticmethod
    def fromPrenex(str: str) -> 'NFA[int]':

        num_param = {'UNION': 2, 'STAR': 1, 'CONCAT': 2, 'PLUS': 1, 'MAYBE': 1}

        stack = []
        words = shlex.split(str)

        state = 0
        final_nfa = NFA[int](0, 0, {}, [])

        for word in words:
            if word in num_param:
                nfa = NFA[int](0, 0, {}, [])
                num = num_param[word]
                stack.append([[], word, num])
            else:
                num = 0
                nfa = NFA[int](0, 0, {}, [])
                stack.append([[], word, num])

                if word != 'eps' and word != 'void':
                    final_nfa.sigma.add(word)

            while len(stack) > 0 and stack[-1][2] == 0:
                op = stack.pop()
                if op[1] == "CONCAT":
                    nfa1 = op[0][0]
                    nfa2 = op[0][1]
                    nfa = concatNFA(nfa1, nfa2)

                elif op[1] == "UNION":
                    initial_state = state
                    final_state = state + 1
                    nfa1 = op[0][0]
                    nfa2 = op[0][1]
                    nfa = unionNFA(nfa1, nfa2, initial_state, final_state)
                    state += 2

                elif op[1] == "STAR":
                    initial_state = state
                    final_state = state + 1
                    nfa = op[0][0]
                    nfa = starNFA(nfa, initial_state, final_state)
                    state += 2

                elif op[1] == "PLUS":
                    initial_state = state
                    final_state = state + 1
                    nfa = op[0][0]
                    nfa = concatNFA(nfa, starNFA(nfa, initial_state, final_state))
                    state += 2

                elif op[1] == "MAYBE":
                    initial_state1 = state
                    final_state1 = state
                    initial_state2 = state + 1
                    final_state2 = state + 2
                    nfa = op[0][0]
                    nfa = unionNFA(nfa, epsilonNFA(nfa, initial_state1, final_state1), initial_state2, final_state2)
                    state += 3

                elif op[1] == "void":
                    initial_state = state
                    final_state = state + 1
                    nfa = voidNFA(initial_state, final_state)
                    state += 2

                elif op[1] == "eps":
                    initial_state = state
                    final_state = state
                    nfa = epsilonNFA(initial_state, final_state)
                    state += 1

                else:
                    initial_state = state
                    final_state = state + 1
                    nfa = characterNFA(op[1], initial_state, final_state)
                    state += 2

                if len(stack) > 0:
                    stack[-1][0].append(nfa)
                    stack[-1][2] -= 1
                else:
                    sigma = final_nfa.sigma
                    final_nfa = nfa
                    final_nfa.sigma = sigma

        return final_nfa

