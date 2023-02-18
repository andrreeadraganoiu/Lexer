from typing import Callable, Generic, TypeVar
from queue import Queue
from src.NFA import NFA
import copy

S = TypeVar("S")
T = TypeVar("T")


def epsilon_closure(initial_state, nfa) -> 'set[int]':
    queue = Queue()
    queue.put(initial_state)

    closure = set()
    closure.add(initial_state)

    while not queue.empty():
        q = queue.get()
        for s in nfa.next(q, 'eps'):
            closure.add(s)
            queue.put(s)

    return closure


class DFA(Generic[S]):
    def __init__(self, initial_state, final_states, delta, states, sigma):
        self.initial_state = initial_state
        self.final_states = final_states
        self.delta = delta
        self.states = states
        self.sigma = sigma

    def map(self, f: Callable[[S], T]) -> 'DFA[T]':
        pass

    def next(self, from_state: S, on_chr: str) -> S:
        s = set()

        if from_state not in self.delta.keys():
            return s

        for i in self.delta[from_state]:
            if i[0] == on_chr:
                s.add(i[1])

        return list(s)[0]

    def getStates(self) -> 'set[S]':
        return self.states

    def accepts(self, str: str) -> bool:
        stack = []
        stack.append((self.initial_state, str))
        isAccepted = False

        while stack:
            q = stack.pop()
            state = q[0]
            word = copy.deepcopy(q[1])

            if self.isFinal(state) and not word:
                isAccepted = True
                break

            if not self.isFinal(state):
                isAccepted = False

            if word:
                if word[0] not in self.sigma:
                    isAccepted = False
                    break
                stack.append((self.next(state, word[0]), word[1:len(word)]))

        return isAccepted

    def isFinal(self, state: S) -> bool:
        return state in self.final_states

    @staticmethod
    def fromPrenex(str: str) -> 'DFA[int]':

        nfa = NFA[int].fromPrenex(str)
        Q0 = epsilon_closure(nfa.initial_state, nfa)
        queue = Queue()
        queue.put(Q0)

        delta = {}
        Q = set()  # multime de grupuri de stari a dfa
        Q.add(frozenset(Q0))
        F = set()

        while not queue.empty():
            P = queue.get()
            delta[frozenset(P)] = []
            for p in P:
                if nfa.isFinal(p):
                    F.add(frozenset(P))
                    break

            for a in nfa.sigma:
                S = set()
                for p in P:
                    for next in nfa.next(p, a):
                        S = S.union(epsilon_closure(next, nfa))

                if S == set():  # daca nu am tranzitii pe caracterul a
                    continue

                if frozenset(S) not in Q:  # daca grupul de stari este nou
                    Q.add(frozenset(S))
                    queue.put(S)
                delta[frozenset(P)].append((a, frozenset(S)))

        dict = {}
        count = 0

        states = []
        final_states = []

        for q in Q:
            dict[q] = count
            states.append(count)
            count += 1
        for f in F:
            final_states.append(dict[f])

        deltaprim = {}  # copiez delta traducand grupurile de stari in numere
        for kv in delta.items():
            deltaprim[dict[kv[0]]] = []
            for t in kv[1]:  # lista de tranzitii
                deltaprim[dict[kv[0]]].append((t[0], dict[t[1]]))

        sink_state = -1
        deltaprim[sink_state] = []

        for a in nfa.sigma:
            deltaprim[sink_state].append((a, sink_state))

        for s in states:
            for a in nfa.sigma:
                found = False
                for p in deltaprim[s]:
                    if p[0] == a:
                        found = True
                        break
                if not found:
                    deltaprim[s].append((a, sink_state))

        return DFA[int](dict[frozenset(Q0)], final_states, deltaprim, states, nfa.sigma)
