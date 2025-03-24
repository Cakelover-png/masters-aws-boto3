import sys
import importlib
import inspect
from core.settings import AVAILABLE_PACKAGES
from core.utils.tasks import BaseTask
import pkgutil

def get_available_tasks():
    tasks = {}
    for package in AVAILABLE_PACKAGES:
        try:
            pkg = importlib.import_module(package)
            # Use pkgutil to find all submodules
            for finder, module_name, ispkg in pkgutil.iter_modules(pkg.__path__):
                if module_name.startswith('task'):
                    try:
                        module_path = f"{package}.{module_name}.main"
                        module = importlib.import_module(module_path)
                        
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if (issubclass(obj, BaseTask) and 
                                obj != BaseTask):
                                task_instance = obj()
                                tasks[task_instance.name] = task_instance
                    except ImportError as e:
                        print(f"Failed to import {module_path}: {e}")
                        continue
        except ImportError as e:
            print(f"Failed to import package {package}: {e}")
            continue
    return tasks

def filter_tasks(tasks, prefix=None):
    if prefix is None:
        return tasks
    return {name: task for name, task in tasks.items() if prefix in name.split('.')[1]}

def run_task(task_path):
    tasks = get_available_tasks()
    task_instance = tasks.get(task_path)
    
    if task_instance is None:
        print(f"Error: Task '{task_path}' not found")
        print("Available tasks:")
        for name in tasks.keys():
            print(f"  {name}")
        sys.exit(1)
    
    try:
        sys.argv = sys.argv[0:1] + sys.argv[2:]
        task_instance.execute()
    except Exception as e:
        print(f"Error executing task '{task_path}': {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py <task_path> [args...]")
        print("       python manage.py available_tasks [search_prefix]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "available_tasks":
        tasks = get_available_tasks()
        search_prefix = sys.argv[2] if len(sys.argv) > 2 else None
        filtered_tasks = filter_tasks(tasks, search_prefix)
        
        if not filtered_tasks:
            print(f"No tasks found matching prefix '{search_prefix}'" if search_prefix else "No tasks found")
        else:
            print("Available tasks:")
            for task_path, task in filtered_tasks.items():
                print(f"  {task_path}: {task.small_desc}")
    else:
        run_task(command)