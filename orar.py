from copy import copy, deepcopy
from utils import *
import random
import argparse
from hill_climbing import *
from monte_carlo import *


class Info:
    def __init__(self, info) -> None:
        """
        Clasa pentru stocarea informatiilor despre sali, profesori si materii.

        Args:
            info (tuple): Un tuplu continand informatiile despre sali, profesori si materii.
        """
        # Extrag informatiile din fisier
        self.classrooms, self.teachers, self.courses = info
        # Sortez materiile in functie de numarul de studenti
        self.sorted_courses = self.courses_sorted()

    def courses_sorted(self):
        """
        Returneaza un dictionar sortat al materiilor in functie de numarul de studenti.

        Returns:
            dict: Dictionarul sortat al materiilor.
        """
        return dict(sorted(self.courses.items(), key=lambda x: x[1]))
    
    def teacher_has_course(self, course):
        """
        Returneaza lista de profesori care predau o anumita materie.

        Args:
            course (str): Numele materiei.

        Returns:
            list: Lista de profesori care predau materia respectiva.
        """
        teachers = []
        for teacher in self.teachers:
            if course in self.teachers[teacher]['Materii']:
                teachers.append(teacher)
        return teachers
    
    def teacher_constr(self, teacher, interval, day):
        """
        Verifica daca un profesor are constrangeri legate de zi si interval.

        Args:
            teacher (str): Numele profesorului.
            interval (str): Intervalul orar.
            day (str): Ziua saptamanii.

        Returns:
            int: Punctajul obtinut in urma verificarii constrangerilor.
        """
        points = 0

        # Constrangerea: Un profesor poate tine o singura materie intr-un interval orar intr-o sala.
        # Verific daca intervalul si sala sunt disponibile pentru profesor
        if self.timetable[day][interval] is None:
            if self.teachers[teacher]['Constrangeri']['Interaval'] is None or interval in self.teachers[teacher]['Constrangeri']['Interval']:
                if self.teachers[teacher]['Constrangeri']['Sala'] is None or self.teachers[teacher]['Constrangeri']['Sala'] in self.info.classrooms:
                    points += 1

        # Constrangerea: Un profesor poate tine ore in maxim 7 intervale pe saptamana.
        # Verific daca profesorul a depasit numarul maxim de ore pe saptamana
        if self.teacher_counts[teacher] < 7:
            points += 1

        # Constrangerea: Toti profesorii predau doar materiile pe care sunt specializati.
        # Verific daca materia este in lista materiilor predate de profesor
        if self.teachers[teacher]['Materii'] is None or self.teachers[teacher]['Materii'] in self.info.teachers[teacher]:
            points += 1

        # Prefera anumite zile sau nu doresc sa predea intr-o zi anume.
        if day in self.teachers[teacher]['Constrangeri']['Zi']:
            points += 1
        # Prefera sau nu doresc anumite intervale orare, in oricare dintre zile
        if interval in self.teachers[teacher]['Constrangeri']['Interval']:
            points += 1

        return points



class State:
    def __init__(self, info, timetable, case, seed=42):
        """
        Clasa pentru reprezentarea starii problemei.

        Args:
            info (Info): Obiectul care contine informatiile despre sali, profesori si materii.
            timetable (dict): Dictionarul reprezentand orarul.
            case (tuple): Tuplu continand contoarele pentru orele de predare si numarul de studenti pe materie.
            seed (int, optional): Valoarea pentru initializarea generatorului de numere aleatoare. Implicit este 42.
        """
        self.info = info
        self.timetable = timetable
        self.seed = seed
        self.teacher_counts, self.courses_counts = case
        self.nr_conflicts = self.conflicts()
        self.nr_soft_conflicts = 0
        self.nr_hard_conflicts = 0
        
    def copy(self):
        """
        Creeaza o copie a starii actuale.

        Returns:
            State: Copia starii actuale.
        """
        return deepcopy(self)
        
    def conflicts(self):
        """
        Calculeaza numarul total de conflicte in starea curenta.

        Returns:
            int: Numarul total de conflicte.
        """
        points = 0
        for course in self.courses_counts:
            if self.courses_counts[course] < self.info.courses[course]:
                points += self.info.courses[course] - self.courses_counts[course]
        return points
    
    def apply_move(self, day, interval, room, teacher, course):
        """
        Aplica o mutare in starea curenta.

        Args:
            day (str): Ziua saptamanii.
            interval (str): Intervalul orar.
            room (str): Sala de clasa.
            teacher (str): Profesorul care preda materia.
            course (str): Materia de predat.

        Returns:
            State: Starea rezultata dupa aplicarea mutarii.
        """
        new_state = deepcopy(self)
        new_state.timetable[day][interval][room] = (teacher, course)
        new_state.teacher_counts[teacher] += 1
        new_state.courses_counts[course] += self.info.classrooms[room]['Capacitate']
        new_state.nr_conflicts = new_state.conflicts()
        new_state.nr_soft_conflicts += new_state.info.teacher_constr(teacher, day, interval, room, course)
        new_state.nr_hard_conflicts += self.check_hard_constraints(day, interval, room, teacher, course)
        return new_state
    
    def get_next_state(self):
        """
        Genereaza toate starile vecine posibile prin completarea unui interval cu o materie neacoperita.

        Returns:
            list: Lista de stari vecine posibile.
        """
        uncovered_courses = [course for course, students in self.info.sorted_courses.items() if self.courses_counts[course] < students]

        random.shuffle(uncovered_courses)

        next_states = []

        for uncovered_course in uncovered_courses:
            teachers = self.info.teacher_has_course(uncovered_course)
            # Iterez prin fiecare zi - interval - sala
            for day in self.timetable:
                for interval in self.timetable[day]:
                    for room in self.timetable[day][interval]:
                        # Daca intervalul este liber
                        if self.timetable[day][interval][room] is None:
                            # Iterez prin fiecare profesor si verific daca poate preda materia in intervalul respectiv
                            for teacher in teachers:
                                # Verific daca profesorul nu are alte cursuri in acelasi interval
                                if self.teacher_counts[teacher] < 7:
                                    # Verific constrangerile pentru acest move
                                    if self.info.teacher_constr(teacher, day, interval):
                                        next_states.append(self.apply_move(day, interval, room, teacher, uncovered_course))

        return next_states

class NoSolutionState:
    """
    Clasa folosita pentru a marca cazul in care nu a fost gasita o solutie adecvata.
    """
    pass

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a timetable using Hill Climbing or Monte Carlo Tree Search algorithm.')
    parser.add_argument('algorithm', type=str, choices=['hc', 'mtcs'], help='Algorithm to use: "hc" for Hill Climbing, "mtcs" for Monte Carlo Tree Search')
    parser.add_argument('input_file', type=str, help='Input YAML file containing timetable specifications')
    parser.add_argument('output_file', nargs='?', default=None, type=str, help='Output text file to save the final timetable')
    args = parser.parse_args()

    algorithm = args.algorithm
    input_file = args.input_file
    output_file = args.output_file

    timetable_specs = read_yaml_file(input_file)
    timetable = create_timetable(timetable_specs)
    info = Info((timetable_specs[SALI], timetable_specs[PROFESORI], timetable_specs[MATERII]))

    teacher_counts = {teacher: 0 for teacher in info.teachers}
    courses_counts = {course: 0 for course in info.courses}

    initial_state = State(info, timetable, (teacher_counts, courses_counts))

    if algorithm == 'hc':
        final_state, iters, states = hill_climbing(initial_state)
    elif algorithm == 'mtcs':
        final_state = monte_carlo_tree_search(initial_state, num_simulations=1000)

    if isinstance(final_state, NoSolutionState):
        print("Nu s-a găsit o soluție adecvată.")
    else:
        final_timetable_str = pretty_print_timetable(final_state.timetable, input_file)
        print(final_timetable_str)

        if output_file:
            output_path = f"outputs/{output_file}"
            with open(output_path, 'w') as f:
                f.write(final_timetable_str)
            
            with open(output_path, 'a') as f:
                f.write(f"\n\nFinal state: {final_state}")
                f.write(f"\nNumber of iterations: {iters}")
                f.write(f"\nNumber of states generated: {states}")
