# ავტომატური დავალების მენეჯმენტის სისტემა.

ამ პროექტის მიზანია, ყველა დავალების გაერთიანება ერთ პროექტში და მარტივად ტერმინალიდან გაშვება.

## ინსტალაცია

```
pip install poetry
poetry config virtualenvs.in-project true (Optional)
poetry install
eval $(poetry env activate)
```

## გამოყენება

```
python manage.py <task_path> [args...]

```

### მაგალითები გამოყენების:

```
> python3 manage.py available_tasks 
Available tasks:
  task1.1: Finds Armstrong numbers in a given range and their sum.
  task1.2: Extracts numbers from a string and categorizes them into float, odd, and even lists
  task1.3: Check seat availability and find closest available seat
```

```
> python3 manage.py task1.1                       
Armstrong numbers: [9, 153, 370, 371, 407, 1634, 8208, 9474]
Sum of Armstrong numbers: 20626
```


## დამატებითი ინფორმაცია

პროექტი დაყოფილია task-ების პაკეტებათ, თითოეული დავალებისთვის შესრულებული კოდის პოვნა შესაძლებელია
```
tasksx -> tasky -> main.py
```
სადაც, x არის ლექციის რიცხვი, ხოლო y ლექციის შემდგომ მოცემული დავალების ნომერი.

```
tasks1
 |-task1
 | |-__init__.py
 | |-main.py
 |-task2
 | |-main.py
 | |-__init__.py
 |-task3
 | |-__init__.py
 | |-main.py
 |-__init__.py
 ```