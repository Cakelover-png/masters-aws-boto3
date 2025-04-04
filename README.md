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

შეცვალეთ example.env .env-ად და მოუთითეთ მოცემული secrets

```
python manage.py <task_path> [args...]

```

### მაგალითები გამოყენების:

```
> python manage.py available_tasks 
Available tasks:
  task1.1: Finds Armstrong numbers in a given range and their sum.
  task1.2: Extracts numbers from a string and categorizes them into float, odd, and even lists
  task1.3: Check seat availability and find closest available seat
  ...
```

```
> python manage.py task1.1                       
Armstrong numbers: [9, 153, 370, 371, 407, 1634, 8208, 9474]
Sum of Armstrong numbers: 20626
```

```
> python manage.py task2.4 -h                                      
usage: manage.py [-h] [--desc] <command> ...

Task: task2.4

options:
  -h, --help      show this help message and exit
  --desc          Display task description

Available commands:
  <command>       Action to perform on S3
    list          List accessible S3 buckets.
    exists        Check if a bucket exists.
    create        Create a new S3 bucket.
    delete        Delete an existing S3 bucket (must be empty!).
    upload        Download from URL and upload to S3.
    ...

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

## შესრულებული დავალებები
- ლექცია პირველი:
  - [x] Task 0
  - [x] Task 1
  - [x] Task 2
  - [x] Task 3

- ლექცია მეორე:
  - [x] Task 1
  - [x] Task 2
  - [x] Task 3
  - [x] Task 4

- ლექცია მესამე:
  - [x] Task 1
  - [x] Task 2
  - [x] Task 3
  - [] Task 4