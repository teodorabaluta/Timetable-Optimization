import random
import math

class Node:
    def __init__(self, state, parent=None):
        """
        Initializarea unui nod al arborelui de cautare.

        Args:
            state (State): Starea asociata nodului.
            parent (Node): Nodul parinte.
        """
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.score = 0

    def add_child(self, child_state):
        """
        Adaugarea unui copil pentru nodul curent.

        Args:
            child_state (State): Starea copilului.

        Returns:
            Node: Nodul copil creat.
        """
        child = Node(child_state, parent=self)
        self.children.append(child)
        return child

def select_node(node):
    """
    Selecteaza un nod in functie de politica de selectie Monte Carlo.

    Args:
        node (Node): Nodul din care incepe selectia.

    Returns:
        Node: Nodul selectat.
    """
    while node.children:
        if not all(child.visits for child in node.children):
            return random.choice([child for child in node.children if not child.visits])
        node = max(node.children, key=lambda x: x.score / x.visits + 1.4 * (2 * math.log(node.visits) / x.visits) ** 0.5)
    return node


def expand_node(node):
    """
    Extinde un nod prin adaugarea de copii (stari vecine).

    Args:
        node (Node): Nodul care va fi extins.
    """
    if node.state.is_terminal():
        return

    next_states = node.state.generate_next_states()

    for state in next_states:
        child_node = node.add_child(state)

def simulate(node):
    """
    Simuleaza o tranzitie a starii pana la o stare terminala si intoarce rezultatul simularii.

    Args:
        node (Node): Nodul pentru care se simuleaza tranzitia.

    Returns:
        int: Rezultatul simularii.
    """
    current_state = node.state
    while not current_state.is_terminal():
        possible_actions = current_state.generate_next_states()
        action = random.choice(possible_actions)
        current_state = current_state.apply_move(*action)
    return -current_state.get_conflicts()

def backpropagate(node, result):
    """
    Propaga rezultatul simularii inapoi la parintii nodului si actualizeaza scorul si numarul de vizite.

    Args:
        node (Node): Nodul de la care incepe propagarea.
        result (int): Rezultatul simularii.
    """
    while node:
        node.visits += 1
        node.score += result
        node = node.parent

def best_child(node):
    """
    Selecteaza cel mai bun copil al unui nod.

    Args:
        node (Node): Nodul pentru care se cauta cel mai bun copil.

    Returns:
        Node: Cel mai bun copil al nodului.
    """
    if node.children:
        return max(node.children, key=lambda x: x.visits)
    else:
        return None

def monte_carlo_tree_search(root_node, num_simulations):
    """
    Implementarea algoritmului de cautare Monte Carlo Tree Search.

    Args:
        root_node (Node): Nodul radacina al arborelui.
        num_simulations (int): Numarul de simulari care vor fi efectuate.

    Returns:
        State or None: Starea finala optima sau None daca nu s-a gasit o solutie.
    """
    for _ in range(num_simulations):
        node_to_simulate = select_node(root_node)
        
        if not node_to_simulate.state.is_terminal():
            expand_node(node_to_simulate)
            node_to_simulate = random.choice(node_to_simulate.children)
        
        simulation_result = simulate(node_to_simulate)
        
        backpropagate(node_to_simulate, simulation_result)
    
    best_child_node = best_child(root_node)
    if best_child_node:
        return best_child_node.state
    else:
        return None

class State:
    def __init__(self, info, timetable, case, seed=42):
        """
        Initializarea unei stari a problemei.

        Args:
            info (Info): Obiectul cu informatiile despre probleme.
            timetable (dict): Orarul curent.
            case (tuple): Tuplu care contine dictionare cu numarul de ore pentru profesori si numarul de studenti pentru fiecare materie.
            seed (int): Valoarea seed pentru generarea aleatoare (implicit 42).
        """
        self.info = info
        self.timetable = timetable
        self.seed = seed
        self.dict_t, self.dict_c = case
        self.nr_conflicts = self.conflicts()
        self.nr_soft_conflicts = 0
        self.nr_hard_conflicts = 0
        
    def copy(self):
        """
        Creeaza o copie a starii.

        Returns:
            State: Copia starii.
        """
        return deepcopy(self)
        
    def is_terminal(self):
        """
        Verifica daca starea este terminala (toate materiile sunt acoperite).

        Returns:
            bool: True daca starea este terminala, False in caz contrar.
        """
        return all(students_covered >= students_total for students_covered, students_total in self.dict_c.values())
        
    def conflicts(self):
        """
        Calculeaza numarul total de conflicte in stare.

        Returns:
            int: Numarul total de conflicte.
        """
        points = 0
        for course, students_total in self.info.courses.items():
            students_covered = self.dict_c.get(course, 0)
            if students_covered < students_total:
                points += (students_total - students_covered)
        return points
    
    def generate_next_states(self):
        """
        Genereaza starile urmatoare posibile prin completarea unor intervale cu materii neacoperite.

        Returns:
            list: Lista de stari urmatoare posibile.
        """
        next_states = []
        for day in self.timetable:
            for interval in self.timetable[day]:
                for room in self.timetable[day][interval]:
                    if self.timetable[day][interval][room] is None:
                        for course, students_total in self.info.courses.items():
                            students_covered = self.dict_c.get(course, 0)
                            if students_covered < students_total:
                                teachers = self.info.get_teacher_courses(course)
                                for teacher in teachers:
                                    if self.dict_t[teacher] < 7:
                                        next_states.append(self.apply_move(day, interval, room, teacher, course))
        return next_states
    
    def apply_move(self, day, interval, room, teacher, course):
        """
        Aplica o mutare (adauga o materie intr-un interval).

        Args:
            day (str): Ziua in care se aplica mutarea.
            interval (str): Intervalul orar in care se aplica mutarea.
            room (str): Sala in care se aplica mutarea.
            teacher (str): Profesorul care tine cursul.
            course (str): Materia care se adauga.

        Returns:
            State: Starea rezultata după aplicarea mutarii.
        """
        new_state = deepcopy(self)
        new_state.timetable[day][interval][room] = (teacher, course)
        new_state.dict_t[teacher] += 1
        new_state.dict_c[course] = new_state.dict_c.get(course, 0) + self.info.rooms[room]['Capacitate']
        new_state.nr_conflicts = new_state.conflicts()
        new_state.nr_soft_conflicts += self.check_soft_constraints(day, interval, room, teacher, course)
        new_state.nr_hard_conflicts += self.check_hard_constraints(day, interval, room, teacher, course)
        return new_state
    
    def get_conflicts(self):
        """
        Obtine numarul total de conflicte in starea curenta.

        Returns:
            int: Numarul total de conflicte.
        """
        return self.nr_conflicts + self.nr_soft_conflicts
    
    def check_hard_constraints(self, day, interval, room, teacher, course):
        """
        Verifica constrangerile dure.

        Args:
            day (str): Ziua in care se aplica mutarea.
            interval (str): Intervalul orar in care se aplica mutarea.
            room (str): Sala in care se aplica mutarea.
            teacher (str): Profesorul care tine cursul.
            course (str): Materia care se adauga.

        Returns:
            int: Penalizarea pentru incălcarea constrangerilor dure.
        """
        if self.timetable[day][interval][room] is not None:
            return 1000
        return 0
    
    def check_soft_constraints(self, day, interval, room, teacher, course):
        """
        Verifica constrangerile soft.

        Args:
            day (str): Ziua in care se aplica mutarea.
            interval (str): Intervalul orar in care se aplica mutarea.
            room (str): Sala in care se aplica mutarea.
            teacher (str): Profesorul care tine cursul.
            course (str): Materia care se adauga.

        Returns:
            int: Punctajul obtinut in urma verificarii constrangerilor soft.
        """
        points = 0
        if day not in self.info.teachers[teacher]['Constrangeri']:
            points += 1
        return points
    
    def get_capacity(self, room):
        return self.info.rooms[room]['Capacitate']
    
    def check_constraints(self):
        total_constraints = 0
        for day in self.timetable:
            for interval in self.timetable[day]:
                for room in self.timetable[day][interval]:
                    if self.timetable[day][interval][room] is not None:
                        teacher, course = self.timetable[day][interval][room]
                        total_constraints += self.check_soft_constraints(day, interval, room, teacher, course)
                        total_constraints += self.check_hard_constraints(day, interval, room, teacher, course)
        return total_constraints

