# OS CEP

# We will solve our problem statement using producer consumer problem

# Problem Statement
# Implement any one of the given classical synchronization problems using any appropriate system and application
# programming tools considering all the conditions and constraints specified in the problem statement.


# Problem Statement: Spring Workers
# Simulate a tree laden with fruits. Launch three “picker” processes and a “loader” process in parallel. If there is
# fruit on the tree, the picker picks it and places it in a slot of a crate with 12 slots. When a picker finds that the
# crate is full, it calls the loader. It waits for the loader to place this crate in a truck. Then, the loader furnishes a
# new crate for the pickers. We assume there is enough space in the truck for all crates. All pickers return to the
# main function when the tree is bare. In the end, the loader places any partially filled crate in the truck if present.
# If a picker is adding to the last crate, the loader waits for it to complete the action.
# Points to note:
# • The number of fruits on the tree is known globally.
# • This tree is implemented as an integer array to represent different pieces of fruit.
# • The main function provides a shared empty crate when execution starts.
# • A piece of fruit can be picked only once and by only one picker for obvious reasons.
# Synchronize the processes, enforcing mutual exclusion where necessary. Produce a working code such that the
# output identifies each action and the agent performing this action.

import os
import multiprocessing as mp
import queue

TOTAL_FRUITS = None

def main():
    while True:
        total_fruits = int(input("Enter the total number of fruits on the tree: "))
        if total_fruits <= 0:
            print("Please enter a valid number of fruits!")
        else:
            break

    TOTAL_FRUITS = mp.Value('i', total_fruits)  # The number of fruits on the tree is known globally.
    
    # Defining global variables (shared modifiable data that will require mutual exclusion)
    manager = mp.Manager()
    tree = manager.list(range(1, TOTAL_FRUITS.value+1))
    crate = manager.list()
    truck = manager.list()

    # Defining locks
    tree_lock = mp.Lock()
    crate_lock = mp.Lock()
    loader_lock = mp.Lock()

    # Condition variables 
    crate_full_condition = mp.Condition(crate_lock)
    new_crate_condition = mp.Condition(crate_lock)
        
    all_picking_done = mp.Value('i', 0)
        
    active_pickers = mp.Value('i', 3)

    print("--------------------------------------------OS CEP--------------------------------------------")
    print("\n\n")
    

    # Create the loader process
    loader_process = mp.Process(
        target=loader, 
        args=(crate, truck, crate_full_condition, new_crate_condition, all_picking_done, active_pickers, crate_lock)
    )
    
    # Create picker processes
    picker_processes = []
    for i in range(3):
        p = mp.Process(
            target=picker, 
            args=(i+1, tree, crate, tree_lock, crate_lock, crate_full_condition, 
                  new_crate_condition, all_picking_done, active_pickers)
        )
        picker_processes.append(p)
    
    # Start all processes
    loader_process.start()
    for p in picker_processes:
        p.start()
    
    # Wait for picker processes to complete
    for p in picker_processes:
        p.join()
    
    # Wait for loader to finish
    loader_process.join()

    print("\n-------- Final Results --------")
    print(f"Total fruits expected: {TOTAL_FRUITS.value}")
    print(f"Total fruits collected: {sum(len(c) for c in truck)}")
    print("\nCrate Breakdown:")
    print("+---------+-----------------+")
    print("| Crate # | Fruits in Crate |")
    print("+---------+-----------------+")
    for idx, crate in enumerate(truck, 1):
        print(f"| {idx:7} | {len(crate):15} |")
    print("+---------+-----------------+")
    print(f"| {'TOTAL':7} | {sum(len(c) for c in truck):15} |")
    print("+---------+-----------------+")

    missing = TOTAL_FRUITS.value - sum(len(c) for c in truck)
    if missing == 0:
        print("\nSUCCESS: All fruits accounted for!")
    elif missing > 0:
        print(f"\nWARNING: {missing} fruits missing!")
    else:
        print(f"\nERROR: {abs(missing)} extra fruits detected!")



def picker(picker_id, tree, crate, tree_lock, crate_lock, crate_full_condition, new_crate_condition, all_picking_done, active_pickers):
    print(f"Process {picker_id} has started!")
    while True:
        fruit = get_fruit(picker_id, tree, tree_lock)
        if fruit is None:
            break  # Return to main function
        fill_crate_result = fill_crate(picker_id, fruit, crate, crate_lock, crate_full_condition, new_crate_condition)
        if fill_crate_result and len(tree) == 0:
            break
    decrease_active_pickers(picker_id, active_pickers, all_picking_done, crate_full_condition, crate, crate_lock)
        

def get_fruit(p_id,tree, tree_lock):
    with tree_lock: # Automatically acquires lock and releases it after use. 
        # Any other process trying to access critical section will wait
        if len(tree) > 0:
            curr_length = len(tree)
            fruit = tree[curr_length-1]  # I got the fruit
            tree.remove(fruit) # Removing the last fruit
            print(f"Process {p_id} has acquired the fruit {fruit}")
            print(f"Tree now looks like: {tree}")
            return fruit
        else: 
            print(f"Tree is bare. Returning to main function!")
        # Releases lock on its own

def fill_crate(p_id, fruit, crate, crate_lock, crate_full_condition, new_crate_condition):
    with crate_lock: # Automatically acquires lock and releases it after use. 

        while len(crate) >= 12:
            print(f"Picker {p_id} found that the crate is full. Notifying loader...")
            
            # Signal the loader that the crate is full
            crate_full_condition.notify_all()
            
            # Wait for a new crate
            print(f"Picker {p_id} is waiting for a new crate...")
            new_crate_condition.wait()  
                           
                          
        print(f"Process {p_id} has acquired the crate and will put fruit in it.")
        crate.append(fruit)  # The crate is a Manager.list object
        print(f"Updated state of the crate is {crate}")

        if len(crate) == 12:
            print(f"Picker {p_id} has filled the crate. Notifying loader...")
            crate_full_condition.notify_all() # Notifying loader
            return True

def decrease_active_pickers(p_id, active_pickers, all_picking_done, crate_full_condition, crate, crate_lock):
    with active_pickers.get_lock():
        active_pickers.value -= 1
        print(f"Picker {p_id} is done. Active pickers remaining: {active_pickers.value}")
        
        # Notifying the loader in case of last picker
        if active_pickers.value == 0:
            with all_picking_done.get_lock():
                all_picking_done.value = 1
            print(f"Picker {p_id} was the last picker. Notifying loader about remaining fruits...")
            with crate_lock:  
                crate_full_condition.notify_all()  


def loader(crate, truck, crate_full_condition, new_crate_condition, all_picking_done, active_pickers, crate_lock):
    
    print(f"Loader (PID: {os.getpid()}) started working")
    
    while True:
        # Wait for the crate to be full or for all picking to be done
        with crate_full_condition:
           while True:  
                if (len(crate) == 12) or (all_picking_done.value == 1 and len(crate) > 0):  
                    break  
                elif all_picking_done.value == 1 and len(crate) == 0:    # No fruits left at all  
                    return  
                else:  
                    crate_full_condition.wait()  
        
        if all_picking_done.value == 1 and len(crate) == 0:
            print("Loader detected all picking is done and no fruits remain in the crate")
            break
        
        if all_picking_done.value == 1 and active_pickers.value > 0:
            print("Loader waiting for pickers to finish with the last crate...")
        
        current_crate = list(crate)
        truck.append(current_crate)
        
        print(f"Loader loaded crate with {len(current_crate)} fruits into the truck (Crate #{len(truck)})")
        print(f"Truck now looks like: {truck}")
        
        with crate_lock:
            crate[:] = [] # Clearing the crate

        if active_pickers.value == 0:
            break
        
        # Notify pickers that a new crate is available
        with new_crate_condition:
            print("Loader provided a new empty crate. Notifying pickers...")
            new_crate_condition.notify_all()

    
if __name__ == "__main__":
    main()