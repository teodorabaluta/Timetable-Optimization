from orar import State, Info
from utils import read_yaml_file, create_timetable
from copy import deepcopy  # Importăm funcția deepcopy din modulul copy
import random  # Importăm modulul random

def hill_climbing(initial: State, max_iters: int = 1000):
    """
    Algoritmul Hill Climbing pentru generarea unui orar optim.
    
    Args:
        initial (State): Starea initiala a problemei.
        max_iters (int): Numarul maxim de iteratii permise.
        
    Returns:
        State: Starea finala obtinuta de algoritm.
        int: Numarul total de iteratii efectuate.
        int: Numarul total de stari generate.
    """
    iters, states = 0, 0  # Initializez contoarele pentru numarul de iteratii si stari generate
    state = initial.copy()  # Creez o copie a starii initiale pentru a nu modifica starea initiala
    best_state = state  # Initializez cea mai buna stare cu starea initiala

    while iters < max_iters:
        iters += 1

        states_gen = list(state.get_next_state())  # Generez starile vecine ale starii curente
        states += len(states_gen)

        if states_gen:  # Verific daca au fost generate stari vecine
            best_neighbor = min(states_gen, key=lambda neigh: neigh.get_conflicts())  # Gasesc cea mai buna stare vecina
            if best_neighbor.get_conflicts() < best_state.get_conflicts():  # Verific daca starea vecina este mai buna decat cea mai buna stare curenta
                best_state = best_neighbor
                state = best_neighbor
            else:
                break  # Ies din bucla daca nu mai pot imbunatati starea
        else:
            break  # Ies din bucla daca nu mai am stari vecine

    return best_state, iters, states

if __name__ == "__main__":
    yaml_file = read_yaml_file('inputs/orar_mare_relaxat.yaml')
    timetable = create_timetable(yaml_file)
    info = Info((yaml_file['Sali'], yaml_file['Profesori'], yaml_file['Materii']))

    teachers_counts = {teacher: 0 for teacher in yaml_file['Profesori']}
    courses_counts = {course: 0 for course in yaml_file['Materii']}

    # Creez starea initiala a problemei
    initial_state = State(info, timetable, (teachers_counts, courses_counts))
    print(f"Initial state conflicts: {initial_state.get_conflicts()}")

    final_state, iters, states = hill_climbing(initial_state, 1000)

    print(f"Best state with {final_state.get_conflicts()} conflicts made in {iters} iterations and {states} states generated: \n{final_state}")
    print(f"Number of students enrolled in each course: {final_state.courses_counts}")
    print(f"Total capacity of each course: {final_state.info.courses}")

    with open("outputs/hill_climbing_result.txt", "w") as f:
        f.write(str(final_state))
